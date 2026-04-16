"""Unified ConfigRepository — wraps any IRepository, backend-agnostic."""
import json
from typing import Optional
from abstractions.IRepository import IRepository
from abstractions.IConfigRepository import IConfigRepository
from utils.json_utils import safe_dumps


class ConfigRepository(IConfigRepository):

    def __init__(self, repo: IRepository):
        self._repo = repo

    def __getattr__(self, name):
        """Forward raw_* calls to the underlying repository."""
        return getattr(self._repo, name)

    def get_config(self, pk: str, sk: str) -> Optional[dict]:
        item = self._repo.get_by_key({"pk": pk, "sk": sk})
        if not item:
            return None
        data = item.get("data")
        if not data:
            return item
        try:
            parsed = json.loads(data) if isinstance(data, str) else data
            return {"pk": pk, "sk": sk, "data": item.get("data"), **parsed}
        except (json.JSONDecodeError, TypeError):
            return item

    def put_config(self, pk: str, sk: str, data: dict) -> dict:
        self._repo.upsert({"pk": pk, "sk": sk, "data": safe_dumps(data)})
        return data

    def get_settings(self) -> Optional[dict]:
        return self.get_config("APP", "SETTINGS")

    def put_settings(self, data: dict) -> dict:
        return self.put_config("APP", "SETTINGS", data)

    def scan_by_pk(self, pk: str) -> list:
        items = self._repo.find_by("pk", pk)
        results = []
        for item in items:
            data = item.get("data")
            if data:
                try:
                    parsed = json.loads(data) if isinstance(data, str) else data
                    result = {"pk": item["pk"], "sk": item["sk"], "data": data, **parsed}
                    results.append(result)
                    continue
                except (json.JSONDecodeError, TypeError):
                    pass
            results.append(item)
        return results
