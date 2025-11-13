#!/usr/bin/env python3
"""
SAP RPA - Main Entry Point
===========================
Orchestrates the entire SAP automation workflow with multiple scenarios
and fallback mechanisms.

Author: Shivam Kumar Jha
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from gui.main_window import MainWindow
from core.sap_connector import SAPConnector
from workflows.scenario_manager import ScenarioManager
from data.excel_manager import ExcelManager
from config import Config


def setup_logging():
    """Setup logging configuration."""
    log_dir = PROJECT_ROOT / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'sap_rpa_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    """Main application entry point."""
    logger = setup_logging()
    logger.info("="*60)
    logger.info("SAP RPA - Multi-Scenario Automation System")
    logger.info("="*60)
    
    try:
        # Initialize configuration
        config = Config()
        logger.info("Configuration loaded successfully")
        
        # Create output directory
        output_dir = PROJECT_ROOT / config.OUTPUT_DIRECTORY
        output_dir.mkdir(exist_ok=True)
        
        # Start GUI application
        logger.info("Starting GUI application...")
        app = MainWindow(config)
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
