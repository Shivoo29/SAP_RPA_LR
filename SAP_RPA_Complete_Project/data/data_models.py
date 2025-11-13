"""
Data Models
===========
Data structures for SAP automation results and processing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
from enum import Enum


class ScenarioType(Enum):
    """Enumeration of processing scenarios."""
    MD04_MATRES_FOUND = "MD04_MatRes_Found"
    ERF_DASHBOARD = "ERF_Dashboard"
    ERF_TO_KO03 = "ERF_to_KO03"
    ALL_FAILED = "All_Failed"


class ProcessingStatus(Enum):
    """Enumeration of processing statuses."""
    SUCCESS = "Success"
    FAILED = "Failed"
    PARTIAL = "Partial"
    PENDING = "Pending"


@dataclass
class ProcessingResult:
    """Result of processing a single material."""
    
    material_number: str
    success: bool = False
    scenario: ScenarioType = ScenarioType.ALL_FAILED
    data: Dict = field(default_factory=dict)
    error_message: str = ""
    plant_found: str = ""
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """
        Convert result to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'material_number': self.material_number,
            'success': self.success,
            'scenario': self.scenario.value,
            'plant_found': self.plant_found,
            'processing_time': self.processing_time,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': self.error_message,
            **self.data  # Unpack extracted data
        }
    
    def get_status(self) -> ProcessingStatus:
        """
        Get processing status.
        
        Returns:
            ProcessingStatus enum
        """
        if self.success:
            return ProcessingStatus.SUCCESS
        elif self.data:
            return ProcessingStatus.PARTIAL
        else:
            return ProcessingStatus.FAILED


@dataclass
class MaterialInput:
    """Input data for material processing."""
    
    material_number: str
    plant: Optional[str] = None
    mrp_area: Optional[str] = None
    description: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MaterialInput':
        """
        Create MaterialInput from dictionary.
        
        Args:
            data: Dictionary with material data
            
        Returns:
            MaterialInput instance
        """
        return cls(
            material_number=data.get('material_number', ''),
            plant=data.get('plant'),
            mrp_area=data.get('mrp_area'),
            description=data.get('description')
        )


@dataclass
class ERFData:
    """Data extracted from ERF Dashboard."""
    
    erf_number: str = ""
    order_number: str = ""
    short_order_desc: str = ""
    internal_order: str = ""
    cost_center: str = ""
    plant: str = ""
    material: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'erf_number': self.erf_number,
            'order_number': self.order_number,
            'short_order_desc': self.short_order_desc,
            'internal_order': self.internal_order,
            'cost_center': self.cost_center,
            'plant': self.plant,
            'material': self.material
        }


@dataclass
class KO03Data:
    """Data extracted from KO03 transaction."""
    
    order_number: str = ""
    order_type: str = ""
    description: str = ""
    responsible_cost_center: str = ""
    plant: str = ""
    status: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'ko03_order_number': self.order_number,
            'ko03_order_type': self.order_type,
            'ko03_description': self.description,
            'ko03_cost_center': self.responsible_cost_center,
            'ko03_plant': self.plant,
            'ko03_status': self.status
        }


@dataclass
class MD04Data:
    """Data extracted from MD04 transaction."""
    
    material: str = ""
    part_description: str = ""
    recipient: str = ""
    order: str = ""
    plant: str = ""
    mrp_area: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'material': self.material,
            'part_description': self.part_description,
            'recipient': self.recipient,
            'order': self.order,
            'plant': self.plant,
            'mrp_area': self.mrp_area
        }


@dataclass
class BatchProcessingReport:
    """Report for batch processing."""
    
    total_materials: int = 0
    successful: int = 0
    failed: int = 0
    scenario_1_count: int = 0
    scenario_2_count: int = 0
    scenario_3_count: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    results: list = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_materials == 0:
            return 0.0
        return (self.successful / self.total_materials) * 100
    
    @property
    def processing_time(self) -> float:
        """Calculate total processing time in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            'total_materials': self.total_materials,
            'successful': self.successful,
            'failed': self.failed,
            'success_rate': round(self.success_rate, 2),
            'scenario_1_count': self.scenario_1_count,
            'scenario_2_count': self.scenario_2_count,
            'scenario_3_count': self.scenario_3_count,
            'processing_time': round(self.processing_time, 2),
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else 'In Progress'
        }
