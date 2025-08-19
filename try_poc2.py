import os
import time
import logging
import pyautogui
import pandas as pd
from datetime import datetime
import win32gui
import win32con 
from typing import List, Dict, Optional
import json

class SAPAutomationBot:
    """
    Robotic Process Automation (RPA) bot for extracting part descriptions
    from SAP dashboards (MD04/MD06) and populating Excel Sheet.
    """

    def __init__(self, config_file: str = "sap_config.json"):
        