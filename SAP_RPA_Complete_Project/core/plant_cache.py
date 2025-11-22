"""
Plant Availability Cache
=========================
Tracks which plants tend to have data for which material prefixes.
Optimizes plant search order based on historical success patterns.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict


class PlantCache:
    """Cache for plant availability patterns."""

    def __init__(self, cache_dir: Path = None):
        """
        Initialize plant cache.

        Args:
            cache_dir: Directory to store cache file
        """
        self.logger = logging.getLogger(__name__)

        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / 'cache'

        cache_dir.mkdir(exist_ok=True)
        self.cache_file = cache_dir / 'plant_availability_cache.json'

        # Structure: {material_prefix: {plant: {success_count, total_count}}}
        self.cache_data = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cache from JSON file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                self.logger.info(f"✓ Loaded plant cache with {len(data)} material prefixes")
                return data
            except Exception as e:
                self.logger.warning(f"Failed to load plant cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        """Save cache to JSON file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
            self.logger.debug("✓ Plant cache saved")
        except Exception as e:
            self.logger.error(f"Failed to save plant cache: {e}")

    def _get_material_prefix(self, material: str, prefix_length: int = 3) -> str:
        """
        Get material prefix for caching.

        Args:
            material: Material number
            prefix_length: Length of prefix to use

        Returns:
            Material prefix
        """
        # Remove any hyphens and take first N characters
        clean_material = material.replace('-', '').replace(' ', '')
        return clean_material[:prefix_length].upper()

    def record_plant_check(self, material: str, plant: str, found_data: bool):
        """
        Record the result of checking a plant for a material.

        Args:
            material: Material number
            plant: Plant code
            found_data: Whether data was found in this plant
        """
        prefix = self._get_material_prefix(material)

        if prefix not in self.cache_data:
            self.cache_data[prefix] = {}

        if plant not in self.cache_data[prefix]:
            self.cache_data[prefix][plant] = {'success': 0, 'total': 0}

        self.cache_data[prefix][plant]['total'] += 1
        if found_data:
            self.cache_data[prefix][plant]['success'] += 1

        # Save cache periodically (every 10 records)
        total_records = sum(
            sum(p['total'] for p in plants.values())
            for plants in self.cache_data.values()
        )
        if total_records % 10 == 0:
            self._save_cache()

    def get_ordered_plants(self, material: str, available_plants: List[str]) -> List[str]:
        """
        Get plants ordered by likelihood of having data, based on historical patterns.

        Args:
            material: Material number
            available_plants: List of plants to consider

        Returns:
            List of plants ordered by success probability (highest first)
        """
        prefix = self._get_material_prefix(material)

        if prefix not in self.cache_data:
            # No data for this prefix, return original order
            return available_plants

        # Calculate success rate for each plant
        plant_scores = []
        for plant in available_plants:
            if plant in self.cache_data[prefix]:
                stats = self.cache_data[prefix][plant]
                if stats['total'] > 0:
                    success_rate = stats['success'] / stats['total']
                    plant_scores.append((plant, success_rate, stats['total']))
                else:
                    plant_scores.append((plant, 0, 0))
            else:
                # No data for this plant, give it medium priority
                plant_scores.append((plant, 0.5, 0))

        # Sort by success rate (descending), then by total count (descending)
        plant_scores.sort(key=lambda x: (x[1], x[2]), reverse=True)

        ordered_plants = [p[0] for p in plant_scores]

        if ordered_plants != available_plants:
            self.logger.info(f"🔄 Reordered plants for {prefix}*: {ordered_plants}")

        return ordered_plants

    def get_plant_statistics(self, material: str, plant: str) -> Dict:
        """
        Get statistics for a specific plant and material prefix.

        Args:
            material: Material number
            plant: Plant code

        Returns:
            Dictionary with success rate and count
        """
        prefix = self._get_material_prefix(material)

        if prefix in self.cache_data and plant in self.cache_data[prefix]:
            stats = self.cache_data[prefix][plant]
            if stats['total'] > 0:
                return {
                    'success_rate': stats['success'] / stats['total'],
                    'success_count': stats['success'],
                    'total_count': stats['total']
                }

        return {'success_rate': 0, 'success_count': 0, 'total_count': 0}

    def should_skip_plant(self, material: str, plant: str, min_attempts: int = 5, failure_threshold: float = 0.1) -> bool:
        """
        Determine if a plant should be skipped based on historical failure rate.

        Args:
            material: Material number
            plant: Plant code
            min_attempts: Minimum number of attempts before skipping
            failure_threshold: Maximum success rate to skip (0.1 = skip if <10% success)

        Returns:
            True if plant should be skipped
        """
        stats = self.get_plant_statistics(material, plant)

        if stats['total_count'] >= min_attempts and stats['success_rate'] < failure_threshold:
            self.logger.info(f"⏭️ Skipping plant {plant} for {material} (success rate: {stats['success_rate']:.1%})")
            return True

        return False

    def get_cache_summary(self) -> Dict:
        """Get summary statistics for the cache."""
        total_prefixes = len(self.cache_data)
        total_records = sum(
            sum(p['total'] for p in plants.values())
            for plants in self.cache_data.values()
        )

        return {
            'total_prefixes': total_prefixes,
            'total_records': total_records,
            'cache_file': str(self.cache_file)
        }

    def clear_cache(self):
        """Clear all cache data."""
        self.cache_data = {}
        self._save_cache()
        self.logger.info("✓ Plant cache cleared")

    def __del__(self):
        """Save cache on object destruction."""
        try:
            self._save_cache()
        except:
            pass
