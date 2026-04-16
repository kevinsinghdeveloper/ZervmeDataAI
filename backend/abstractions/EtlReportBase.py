import json
import logging
import os
from abc import abstractmethod, ABC
from typing import Optional

from abstractions.ILLMServiceManager import ILLMServiceManager


def run_pipeline(pipeline_tasks: dict):
    for name, task in pipeline_tasks.items():
        logging.info(f"Running task {name}...")
        task()
        logging.info(f"Task {name} completed successfully.")


class EtlReportBase(ABC):
    """Base class for ETL report pipelines.

    Supports DynamoDB-backed caching via ``db_service.report_cache`` with an
    automatic fallback to local file-based caching when the database service
    is unavailable.
    """

    # Default cache key used when storing the full response blob
    _DEFAULT_CACHE_KEY = "full_response"

    def __init__(self, run_params: dict, etl_name: str,
                 llm_service_manager: ILLMServiceManager,
                 db_service=None):
        self._run_params = run_params
        self._llm_service_manager = llm_service_manager
        self._etl_name = etl_name
        self._db = db_service
        self._pre_validation_pipeline_tasks = {}
        self._extract_pipeline_tasks = {}
        self._transform_process_pipeline_tasks = {}
        self._post_validation_pipeline_tasks = {}
        self._llm_response_data = {}
        self._use_cache = run_params.get('use_cache', True)
        self._cache_file = f"cache/{etl_name}.json"

    # ------------------------------------------------------------------
    # Pipeline execution
    # ------------------------------------------------------------------

    def run_etl(self):
        logging.info(f"Running ETL process '{self._etl_name}' with config: {self._run_params}")
        self.configure_init_tasks()
        self.run_pre_validation()
        self.run_extract_tasks()
        self.run_transform_process_tasks()
        self.run_post_validation()
        return {"status": "success", "message": f"{self._etl_name} completed."}

    def run_pre_validation(self):
        run_pipeline(self._pre_validation_pipeline_tasks)

    def run_post_validation(self):
        run_pipeline(self._post_validation_pipeline_tasks)

    def run_extract_tasks(self):
        run_pipeline(self._extract_pipeline_tasks)

    def run_transform_process_tasks(self):
        run_pipeline(self._transform_process_pipeline_tasks)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _json_serializer(self, obj):
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return obj.to_dict()
        return str(obj)

    @property
    def _has_db_cache(self) -> bool:
        """Return True when a usable DynamoDB report_cache repository exists."""
        return (
            self._db is not None
            and hasattr(self._db, 'report_cache')
            and self._db.report_cache is not None
        )

    # ------------------------------------------------------------------
    # Caching — DynamoDB primary, file-based fallback
    # ------------------------------------------------------------------

    def save_cache(self) -> None:
        """Persist ``_llm_response_data`` to the cache layer.

        Attempts DynamoDB first.  Falls back to a local JSON file when the
        database service is not configured or when the write fails.
        """
        if not self._use_cache:
            return

        cache_json = json.dumps(
            self._llm_response_data,
            indent=2,
            default=self._json_serializer,
        )

        if self._has_db_cache:
            try:
                from database.schemas.report_cache import ReportCacheItem

                item = ReportCacheItem(
                    report_id=self._etl_name,
                    cache_key=self._DEFAULT_CACHE_KEY,
                    cache_data=cache_json,
                )
                self._db.report_cache.upsert(item.to_item())
                logging.info(
                    f"Cache saved to DynamoDB for report_id={self._etl_name}, "
                    f"cache_key={self._DEFAULT_CACHE_KEY}"
                )
                return
            except Exception:
                logging.warning(
                    "DynamoDB cache write failed; falling back to file cache.",
                    exc_info=True,
                )

        # File-based fallback
        self._save_cache_to_file(cache_json)

    def load_cache(self) -> bool:
        """Load cached data into ``_llm_response_data``.

        Returns ``True`` when cache was successfully loaded, ``False``
        otherwise.  Tries DynamoDB first, then the local file.
        """
        if not self._use_cache:
            return False

        if self._has_db_cache:
            try:
                item = self._db.report_cache.get_by_key({
                    "report_id": self._etl_name,
                    "cache_key": self._DEFAULT_CACHE_KEY,
                })
                if item and item.get("cache_data"):
                    self._llm_response_data = json.loads(item["cache_data"])
                    logging.info(
                        f"Cache loaded from DynamoDB for report_id={self._etl_name}"
                    )
                    return True
            except Exception:
                logging.warning(
                    "DynamoDB cache read failed; falling back to file cache.",
                    exc_info=True,
                )

        # File-based fallback
        return self._load_cache_from_file()

    def is_cached(self, key: str) -> bool:
        """Check whether *key* exists in the current response data.

        If ``_llm_response_data`` is empty but caching is enabled, attempt to
        load the cache from DynamoDB (or file) first so callers get an
        accurate answer without having to call ``load_cache()`` explicitly.
        """
        if not self._use_cache:
            return False

        # If data is already loaded in memory, just check the dict
        if self._llm_response_data:
            return key in self._llm_response_data

        # Attempt to hydrate from persistent store
        if self._has_db_cache:
            try:
                item = self._db.report_cache.get_by_key({
                    "report_id": self._etl_name,
                    "cache_key": self._DEFAULT_CACHE_KEY,
                })
                if item and item.get("cache_data"):
                    self._llm_response_data = json.loads(item["cache_data"])
                    return key in self._llm_response_data
            except Exception:
                logging.warning(
                    "DynamoDB is_cached check failed; falling back to file.",
                    exc_info=True,
                )

        # File fallback — load if present
        if self._load_cache_from_file():
            return key in self._llm_response_data

        return False

    # ------------------------------------------------------------------
    # Private file-cache helpers
    # ------------------------------------------------------------------

    def _save_cache_to_file(self, cache_json: str) -> None:
        """Write *cache_json* to the local file cache."""
        os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
        with open(self._cache_file, 'w') as f:
            f.write(cache_json)
        logging.info(f"Cache saved to {self._cache_file}")

    def _load_cache_from_file(self) -> bool:
        """Read cache from the local JSON file. Returns True on success."""
        if os.path.exists(self._cache_file):
            with open(self._cache_file, 'r') as f:
                self._llm_response_data = json.load(f)
            logging.info(f"Cache loaded from {self._cache_file}")
            return True
        return False

    @abstractmethod
    def configure_init_tasks(self):
        pass
