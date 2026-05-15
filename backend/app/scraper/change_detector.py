from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional


class ChangeDetector:
    def compute_hash(self, data: Dict[str, Any]) -> str:
        content = str(sorted(data.items()))
        return hashlib.sha256(content.encode()).hexdigest()

    def has_changed(
        self,
        new_data: Dict[str, Any],
        existing_hash: Optional[str],
    ) -> bool:
        if existing_hash is None:
            return True
        new_hash = self.compute_hash(new_data)
        return new_hash != existing_hash
