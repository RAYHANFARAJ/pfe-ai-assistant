from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ESReferenceTool:
    def __init__(self) -> None:
        self.output_dir = Path("output")
        self.products_path = self.output_dir / "products.json"
        self.criteria_path = self.output_dir / "criteria.json"
        self.choices_path = self.output_dir / "choice.json"

    def _load_json(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        products = self._load_json(self.products_path)
        for product in products:
            if product.get("id") == product_id:
                return product
        return None

    def get_criteria(self, product_id: str) -> List[Dict[str, Any]]:
        criteria = self._load_json(self.criteria_path)
        return [c for c in criteria if c.get("product_id") == product_id]

    def get_choices_by_criteria(self, criterion_id: str) -> List[Dict[str, Any]]:
        choices = self._load_json(self.choices_path)
        return [c for c in choices if c.get("criteria_id") == criterion_id]

    def get_all_choices_grouped(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all choices once and return them keyed by criteria_id."""
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for choice in self._load_json(self.choices_path):
            cid = choice.get("criteria_id")
            if cid:
                grouped.setdefault(cid, []).append(choice)
        return grouped
