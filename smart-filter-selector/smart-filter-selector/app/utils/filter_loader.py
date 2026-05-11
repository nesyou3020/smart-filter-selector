import json
from typing import Any, Dict


class FilterLoader:
    """Load and manage filter configuration data."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.filter_data = None

    def load_filters(self) -> Dict[str, Any]:
        """
        Load filter configuration from JSON file.

        Returns:
            Dictionary containing filter configuration
        """
        if self.filter_data is None:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.filter_data = json.load(f)
        return self.filter_data

    def flatten_filter_values(self) -> list:
        """
            Flatten all filter values into a single list for embedding generation.

            Returns:
                List of tuples (category, subcategory, value_dict)
        """
        flattened = []
        filters = self.load_filters()

        for category, items in filters.items():
            if isinstance(items, list):  # Process flat lists of items
                for item in items:
                    flattened.append({
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "category": category,
                        "subcategory": item.get("subcategory", "")
                    })
            elif isinstance(items, dict):  # Process nested structures
                for subcategory, subitems in items.items():
                    for item in subitems:
                        flattened.append({
                            "name": item.get("name", ""),
                            "description": item.get("description", ""),
                            "category": category,
                            "subcategory": subcategory
                        })

        return flattened
