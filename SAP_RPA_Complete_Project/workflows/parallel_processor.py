"""
Parallel Processing Manager
============================
Handles concurrent processing of multiple materials using separate SAP sessions.
Uses multiprocessing for true parallelism with COM automation.
"""

import logging
import multiprocessing as mp
from multiprocessing import Queue, Process
from typing import List, Dict, Optional
from datetime import datetime
import time

from core.sap_connector import SAPConnector
from workflows.scenario_manager import ScenarioManager
from data.excel_manager import ExcelManager
from data.data_models import ProcessingResult, ScenarioType
from config import Config


def worker_process(
    worker_id: int,
    materials_queue: Queue,
    results_queue: Queue,
    config_dict: Dict,
    stop_event: mp.Event
):
    """
    Worker process that processes materials from queue.

    Args:
        worker_id: ID of this worker
        materials_queue: Queue of materials to process
        results_queue: Queue to put results in
        config_dict: Configuration dictionary
        stop_event: Event to signal stop
    """
    # CRITICAL: Initialize COM for this process (required for SAP GUI automation)
    import pythoncom
    pythoncom.CoInitialize()

    # CRITICAL: Setup logging for this worker process
    import logging
    from pathlib import Path
    from datetime import datetime

    # Configure logging for worker process
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"worker_{worker_id}_{timestamp}.log"

    # Setup basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to console
        ],
        force=True  # Override any existing configuration
    )

    logger = logging.getLogger(f"Worker-{worker_id}")
    logger.info(f"🚀 Worker {worker_id} started (COM initialized)")
    logger.info(f"Worker {worker_id} logging to: {log_file}")

    sap_connector = None
    scenario_manager = None

    try:
        # Each worker connects to its own existing SAP session
        # Worker 0 uses session 0, Worker 1 uses session 1, Worker 2 uses session 2, etc.
        # User must manually open sessions (Ctrl+N) BEFORE running parallel mode
        sap_connector = SAPConnector()
        if not sap_connector.connect(session_index=worker_id):
            logger.error(f"Worker {worker_id} failed to connect to SAP session {worker_id}")
            logger.error(f"Make sure you have opened at least {worker_id + 1} SAP sessions manually!")
            pythoncom.CoUninitialize()
            return

        logger.info(f"✓ Worker {worker_id} connected to SAP session {worker_id}")

        excel_manager = ExcelManager()
        scenario_manager = ScenarioManager(sap_connector, excel_manager)

        # Process materials until queue is empty or stop signal
        while not stop_event.is_set():
            try:
                # Get material from queue with timeout
                task = materials_queue.get(timeout=1)

                if task is None:  # Poison pill
                    break

                material, selected_plants, mrp_area, enable_erf, enable_ko03 = task

                logger.info(f"Worker {worker_id} processing: {material}")
                start_time = time.time()

                # Process the material
                result = scenario_manager.process_single_material(
                    material_number=material,
                    selected_plants=selected_plants,
                    mrp_area=mrp_area,
                    enable_erf_fallback=enable_erf,
                    enable_ko03_fallback=enable_ko03
                )

                # Add worker ID and processing time
                result.worker_id = worker_id
                result.processing_time = time.time() - start_time

                # Put result in results queue
                results_queue.put(result)

                logger.info(f"✓ Worker {worker_id} completed: {material} ({result.processing_time:.1f}s)")

            except mp.queues.Empty:
                continue  # Queue empty, check stop event and try again
            except Exception as e:
                logger.error(f"Worker {worker_id} error processing material: {e}", exc_info=True)
                # Create error result
                error_result = ProcessingResult(material_number=material if 'material' in locals() else "Unknown")
                error_result.success = False
                error_result.error_message = str(e)
                error_result.worker_id = worker_id
                results_queue.put(error_result)

    except Exception as e:
        logger.error(f"Worker {worker_id} fatal error: {e}", exc_info=True)

    finally:
        # Cleanup SAP connection
        if sap_connector and sap_connector.is_connected:
            try:
                sap_connector.disconnect()
                logger.info(f"Worker {worker_id} disconnected from SAP")
            except:
                pass

        # CRITICAL: Uninitialize COM for this process
        try:
            pythoncom.CoUninitialize()
            logger.info(f"Worker {worker_id} stopped (COM uninitialized)")
        except:
            logger.info(f"Worker {worker_id} stopped")


class ParallelProcessor:
    """Manages parallel processing of materials using multiple SAP sessions."""

    def __init__(self, num_workers: int = None):
        """
        Initialize parallel processor.

        Args:
            num_workers: Number of worker processes (default: from config)
        """
        self.config = Config()
        self.logger = logging.getLogger(__name__)

        if num_workers is None:
            num_workers = self.config.MAX_PARALLEL_WORKERS

        self.num_workers = min(num_workers, 5)  # Cap at 5 workers for safety
        self.logger.info(f"Parallel processor initialized with {self.num_workers} workers")

        self.materials_queue = None
        self.results_queue = None
        self.stop_event = None
        self.workers = []

    def start_workers(self):
        """Start worker processes."""
        self.materials_queue = Queue()
        self.results_queue = Queue()
        self.stop_event = mp.Event()

        config_dict = {
            'plants': self.config.AVAILABLE_PLANTS,
            'mrp_area': self.config.DEFAULT_MRP_AREA
        }

        for i in range(self.num_workers):
            worker = Process(
                target=worker_process,
                args=(i + 1, self.materials_queue, self.results_queue, config_dict, self.stop_event),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            time.sleep(2)  # Stagger worker startup to avoid SAP connection conflicts

        self.logger.info(f"✓ Started {self.num_workers} worker processes")

    def stop_workers(self):
        """Stop all worker processes."""
        self.logger.info("Stopping workers...")
        self.stop_event.set()

        # Send poison pills
        for _ in range(self.num_workers):
            try:
                self.materials_queue.put(None, timeout=1)
            except:
                pass

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
            if worker.is_alive():
                worker.terminate()

        self.workers = []
        self.logger.info("✓ All workers stopped")

    def process_materials_parallel(
        self,
        materials: List[str],
        selected_plants: List[str] = None,
        mrp_area: str = None,
        enable_erf_fallback: bool = True,
        enable_ko03_fallback: bool = True,
        progress_callback = None
    ) -> List[ProcessingResult]:
        """
        Process multiple materials in parallel.

        Args:
            materials: List of material numbers
            selected_plants: Plants to search
            mrp_area: MRP area
            enable_erf_fallback: Enable ERF fallback
            enable_ko03_fallback: Enable KO03 fallback
            progress_callback: Optional callback function(result) for progress updates

        Returns:
            List of ProcessingResult objects
        """
        if not materials:
            return []

        results = []
        total_materials = len(materials)

        self.logger.info(f"🚀 Starting parallel processing of {total_materials} materials with {self.num_workers} workers")

        try:
            # Start workers
            self.start_workers()

            # Queue all materials
            for material in materials:
                task = (material, selected_plants, mrp_area, enable_erf_fallback, enable_ko03_fallback)
                self.materials_queue.put(task)

            # Collect results
            completed = 0
            while completed < total_materials:
                try:
                    result = self.results_queue.get(timeout=300)  # 5 min timeout per result
                    results.append(result)
                    completed += 1

                    self.logger.info(f"Progress: {completed}/{total_materials} completed")

                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(result)

                except mp.queues.Empty:
                    self.logger.warning(f"Timeout waiting for results ({completed}/{total_materials} completed)")
                    break

        except Exception as e:
            self.logger.error(f"Error in parallel processing: {e}", exc_info=True)

        finally:
            # Stop workers
            self.stop_workers()

        self.logger.info(f"✓ Parallel processing completed: {len(results)}/{total_materials} materials processed")
        return results

    def is_available(self) -> bool:
        """Check if parallel processing is available and enabled."""
        return self.config.ENABLE_PARALLEL_PROCESSING and self.num_workers > 1

    def get_worker_count(self) -> int:
        """Get the number of workers."""
        return self.num_workers
