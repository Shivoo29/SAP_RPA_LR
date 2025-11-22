"""
Table ID Cache Manager
=======================
Manages persistent caching of discovered SAP table IDs.
Learns over time which table IDs work for MD04 screens.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from collections import defaultdict


class TableIDCache:
    """Manages caching and learning of SAP table IDs."""

    def __init__(self, cache_dir: str = 'cache'):
        """
        Initialize table ID cache manager.

        Args:
            cache_dir: Directory to store cache file
        """
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / 'table_id_cache.json'
        self.cache_data = {
            'version': '1.0',
            'discovered_table_ids': [],
            'statistics': {
                'total_discoveries': 0,
                'total_uses': 0,
                'last_updated': None
            }
        }

        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)

        # Load existing cache
        self.load_cache()

    def load_cache(self) -> bool:
        """
        Load cache from disk.

        Returns:
            True if cache loaded successfully
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    self.cache_data = json.load(f)

                count = len(self.cache_data.get('discovered_table_ids', []))
                self.logger.info(f"✓ Loaded table ID cache with {count} known table IDs")
                return True
            else:
                self.logger.info("No existing cache file - starting fresh")
                return False
        except Exception as e:
            self.logger.warning(f"Failed to load cache: {e}")
            return False

    def save_cache(self) -> bool:
        """
        Save cache to disk.

        Returns:
            True if cache saved successfully
        """
        try:
            self.cache_data['statistics']['last_updated'] = datetime.now().isoformat()

            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)

            self.logger.debug("✓ Cache saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save cache: {e}")
            return False

    def get_cached_table_ids(self) -> List[str]:
        """
        Get list of cached table IDs, sorted by success count (most successful first).

        Returns:
            List of table ID strings
        """
        table_entries = self.cache_data.get('discovered_table_ids', [])

        # Sort by success_count (descending), then by last_used (most recent first)
        sorted_entries = sorted(
            table_entries,
            key=lambda x: (x.get('success_count', 0), x.get('last_used', '')),
            reverse=True
        )

        return [entry['table_id'] for entry in sorted_entries]

    def record_success(self, table_id: str, plant: Optional[str] = None,
                      material: Optional[str] = None) -> None:
        """
        Record successful use of a table ID.

        Args:
            table_id: The table ID that worked
            plant: Plant number where it worked (optional)
            material: Material number where it worked (optional)
        """
        # Find existing entry or create new one
        entry = self._find_entry(table_id)

        if entry:
            # Update existing entry
            entry['success_count'] = entry.get('success_count', 0) + 1
            entry['last_used'] = datetime.now().isoformat()

            # Update context
            if plant and plant not in entry.get('context', {}).get('plants_worked', []):
                entry.setdefault('context', {}).setdefault('plants_worked', []).append(plant)

            if material:
                # Keep only last 10 materials to avoid bloat
                materials = entry.setdefault('context', {}).setdefault('materials_worked', [])
                if material not in materials:
                    materials.append(material)
                    if len(materials) > 10:
                        materials.pop(0)

            self.logger.info(f"✓ Table ID success recorded (count: {entry['success_count']})")
        else:
            # Create new entry
            new_entry = {
                'table_id': table_id,
                'success_count': 1,
                'first_discovered': datetime.now().isoformat(),
                'last_used': datetime.now().isoformat(),
                'context': {
                    'plants_worked': [plant] if plant else [],
                    'materials_worked': [material] if material else []
                }
            }
            self.cache_data['discovered_table_ids'].append(new_entry)
            self.cache_data['statistics']['total_discoveries'] += 1

            self.logger.info(f"✓ New table ID discovered and cached: {table_id[:50]}...")

        self.cache_data['statistics']['total_uses'] += 1
        self.save_cache()

    def record_failure(self, table_id: str) -> None:
        """
        Record failed attempt with a table ID.

        Args:
            table_id: The table ID that failed
        """
        entry = self._find_entry(table_id)

        if entry:
            entry['failure_count'] = entry.get('failure_count', 0) + 1
            entry['last_failed'] = datetime.now().isoformat()

            # If failure rate is too high, reduce priority
            success_count = entry.get('success_count', 0)
            failure_count = entry.get('failure_count', 0)

            if failure_count > success_count * 2:  # More than 2x failures vs successes
                self.logger.warning(f"Table ID has high failure rate ({failure_count} failures vs {success_count} successes)")

            self.save_cache()

    def add_known_table_id(self, table_id: str, source: str = "manual") -> None:
        """
        Manually add a known table ID to cache.

        Args:
            table_id: The table ID to add
            source: Source of this table ID (e.g., "config", "manual")
        """
        entry = self._find_entry(table_id)

        if not entry:
            new_entry = {
                'table_id': table_id,
                'success_count': 0,
                'first_discovered': datetime.now().isoformat(),
                'last_used': None,
                'source': source,
                'context': {
                    'plants_worked': [],
                    'materials_worked': []
                }
            }
            self.cache_data['discovered_table_ids'].append(new_entry)
            self.logger.info(f"Added known table ID from {source}")
            self.save_cache()

    def get_statistics(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        stats = self.cache_data.get('statistics', {}).copy()
        stats['known_table_ids'] = len(self.cache_data.get('discovered_table_ids', []))

        # Calculate success rates
        entries = self.cache_data.get('discovered_table_ids', [])
        if entries:
            total_successes = sum(e.get('success_count', 0) for e in entries)
            total_failures = sum(e.get('failure_count', 0) for e in entries)
            total_attempts = total_successes + total_failures

            stats['total_successes'] = total_successes
            stats['total_failures'] = total_failures
            stats['success_rate'] = (total_successes / total_attempts * 100) if total_attempts > 0 else 0

        return stats

    def _find_entry(self, table_id: str) -> Optional[Dict]:
        """
        Find cache entry for a table ID.

        Args:
            table_id: The table ID to find

        Returns:
            Cache entry dict if found, None otherwise
        """
        for entry in self.cache_data.get('discovered_table_ids', []):
            if entry.get('table_id') == table_id:
                return entry
        return None

    def clear_cache(self) -> None:
        """Clear all cached table IDs."""
        self.cache_data['discovered_table_ids'] = []
        self.cache_data['statistics'] = {
            'total_discoveries': 0,
            'total_uses': 0,
            'last_updated': None
        }
        self.save_cache()
        self.logger.info("Cache cleared")
