"""
Shared Utilities
=================
Common utility functions used across the application.
"""

import subprocess
import logging
from typing import Optional, Dict
from pathlib import Path


logger = logging.getLogger(__name__)


def execute_vbs_script(vbs_script_path: Path, timeout: int = 30) -> Optional[Dict]:
    """
    Execute a VBS script and return its output.

    Args:
        vbs_script_path: Path to the VBS script file
        timeout: Timeout in seconds (default: 30)

    Returns:
        Dictionary with 'success', 'output', and 'error' keys, or None if script doesn't exist
    """
    if not vbs_script_path.exists():
        logger.warning(f"VBS script not found: {vbs_script_path}")
        return None

    logger.info(f"Executing VBS script: {vbs_script_path.name}")

    try:
        result = subprocess.run(
            ['cscript', '//nologo', str(vbs_script_path)],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            logger.info(f"VBS script executed successfully: {output[:100]}...")
            return {
                'success': True,
                'output': output,
                'error': None
            }
        else:
            error = result.stderr.strip()
            logger.error(f"VBS script failed with return code {result.returncode}: {error}")
            return {
                'success': False,
                'output': None,
                'error': error
            }

    except subprocess.TimeoutExpired:
        logger.error(f"VBS script timed out after {timeout} seconds")
        return {
            'success': False,
            'output': None,
            'error': f'Timeout after {timeout} seconds'
        }
    except Exception as e:
        logger.error(f"Error executing VBS script: {e}")
        return {
            'success': False,
            'output': None,
            'error': str(e)
        }


def parse_vbs_output_to_dict(output: str, delimiter: str = '|') -> Dict[str, str]:
    """
    Parse VBS script output into a dictionary.

    Assumes format: key1|value1|key2|value2 or key=value pairs

    Args:
        output: VBS script output string
        delimiter: Delimiter used in output (default: |)

    Returns:
        Dictionary of parsed values
    """
    parsed = {}

    try:
        # Try pipe-delimited format
        if delimiter in output:
            parts = output.split(delimiter)
            for i in range(0, len(parts) - 1, 2):
                key = parts[i].strip()
                value = parts[i + 1].strip()
                parsed[key] = value

        # Try key=value format
        elif '=' in output:
            lines = output.split('\n')
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    parsed[key.strip()] = value.strip()

        # Otherwise return as single value
        else:
            parsed['output'] = output

    except Exception as e:
        logger.warning(f"Error parsing VBS output: {e}")
        parsed['raw_output'] = output

    return parsed


def format_material_number(material_number: str) -> str:
    """
    Format material number by removing leading zeros and whitespace.

    Args:
        material_number: Raw material number

    Returns:
        Formatted material number
    """
    return material_number.strip().lstrip('0') or '0'


def format_rpm_number(rpm_text: str) -> Optional[str]:
    """
    Extract and format RPM number from text like 'RPM0012345'.

    Args:
        rpm_text: Raw RPM text

    Returns:
        Formatted RPM number (without leading zeros) or None
    """
    import re

    if not rpm_text:
        return None

    # Extract digits from RPM text
    match = re.search(r'\d+', rpm_text)
    if match:
        return match.group(0).lstrip('0') or '0'

    return None


def validate_field_ids(config_dict: Dict, required_fields: list) -> bool:
    """
    Validate that all required field IDs are configured.

    Args:
        config_dict: Dictionary of field IDs
        required_fields: List of required field names

    Returns:
        True if all required fields are present and non-empty
    """
    for field_name in required_fields:
        if not config_dict.get(field_name):
            logger.error(f"Required field ID missing: {field_name}")
            return False

    return True
