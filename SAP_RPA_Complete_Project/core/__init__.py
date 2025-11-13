"""Core package for SAP automation."""

from .sap_connector import SAPConnector
from .field_manager import FieldManager

__all__ = ['SAPConnector', 'FieldManager']
