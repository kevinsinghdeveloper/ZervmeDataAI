"""DynamoDB connector and base repository implementation."""
import os
from typing import Dict, Optional

import boto3

from abstractions.IDatabaseConnector import IDatabaseConnector
from abstractions.IRepository import IRepository
from database.repositories.entities import ENTITIES


class AttrDict(dict):
    """Dict subclass that supports attribute-style access (d.key) alongside d['key'] and d.get('key')."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value


def _wrap(item):
    """Wrap a raw DynamoDB item dict as an AttrDict, or return None."""
    return AttrDict(item) if item else None


def _wrap_list(items):
    """Wrap a list of raw DynamoDB item dicts as AttrDicts."""
    return [AttrDict(i) for i in items]

# Derived from the single entity definitions
TABLE_MAP = {name: entity.dynamo_suffix for name, entity in ENTITIES.items()}


class DynamoDBConnector(IDatabaseConnector):

    def __init__(self):
        self._resource = None
        self._table_prefix = ""

    def initialize(self, config: Optional[Dict] = None):
        region = os.getenv("AWS_REGION_NAME", "us-east-1")
        endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")
        self._table_prefix = os.getenv("DYNAMODB_TABLE_PREFIX", "zerve-dev")

        kwargs = {"region_name": region}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self._resource = boto3.resource("dynamodb", **kwargs)
        print(f"DynamoDB connected. Table prefix: {self._table_prefix}")

    def health_check(self) -> bool:
        if not self._resource:
            return False
        try:
            suffix = TABLE_MAP.get("config", "config")
            table = self._resource.Table(f"{self._table_prefix}-{suffix}")
            _ = table.table_status
            return True
        except Exception:
            return False

    def close(self):
        pass

    def get_table(self, logical_name: str):
        suffix = TABLE_MAP.get(logical_name)
        if not suffix:
            raise ValueError(f"Unknown table: {logical_name}. Valid: {list(TABLE_MAP.keys())}")
        return self._resource.Table(f"{self._table_prefix}-{suffix}")

    def get_repository(self, table_name: str, pk_field: str = "id") -> "DynamoDBRepository":
        return DynamoDBRepository(self, table_name, pk_field)


class DynamoDBRepository(IRepository):

    def __init__(self, connector, table_name: str, pk_field: str = "id"):
        self._connector = connector
        self._table_name = table_name
        self._pk_field = pk_field

    @property
    def _table(self):
        return self._connector.get_table(self._table_name)

    def get_by_id(self, id: str) -> Optional[dict]:
        resp = self._table.get_item(Key={self._pk_field: id})
        return _wrap(resp.get("Item"))

    def get_by_key(self, key: dict) -> Optional[dict]:
        resp = self._table.get_item(Key=key)
        return _wrap(resp.get("Item"))

    def create(self, item: dict) -> dict:
        self._table.put_item(Item=item)
        return item

    def upsert(self, item: dict) -> dict:
        self._table.put_item(Item=item)
        return item

    def update(self, id: str, fields: dict) -> Optional[dict]:
        if not fields:
            return self.get_by_id(id)

        update_parts = []
        expr_values = {}
        expr_names = {}

        for key, value in fields.items():
            safe_key = f"#f_{key}"
            placeholder = f":v_{key}"
            expr_names[safe_key] = key
            expr_values[placeholder] = value
            update_parts.append(f"{safe_key} = {placeholder}")

        result = self._table.update_item(
            Key={self._pk_field: id},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW",
        )
        return _wrap(result.get("Attributes"))

    def update_if(self, id: str, fields: dict, conditions: dict) -> bool:
        update_parts = []
        cond_parts = []
        expr_values = {}
        expr_names = {}

        for key, value in fields.items():
            safe_key = f"#f_{key}"
            placeholder = f":v_{key}"
            expr_names[safe_key] = key
            expr_values[placeholder] = value
            update_parts.append(f"{safe_key} = {placeholder}")

        for key, value in conditions.items():
            safe_key = f"#c_{key}"
            placeholder = f":c_{key}"
            expr_names[safe_key] = key
            expr_values[placeholder] = value
            cond_parts.append(f"{safe_key} = {placeholder}")

        try:
            self._table.update_item(
                Key={self._pk_field: id},
                UpdateExpression="SET " + ", ".join(update_parts),
                ConditionExpression=" AND ".join(cond_parts),
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
            )
            return True
        except Exception as e:
            if "ConditionalCheckFailedException" in str(type(e).__name__):
                return False
            raise

    def delete(self, id: str) -> bool:
        self._table.delete_item(Key={self._pk_field: id})
        return True

    def delete_by_key(self, key: dict) -> bool:
        self._table.delete_item(Key=key)
        return True

    def delete_where(self, field: str, value) -> int:
        items = self.find_by(field, value)
        for item in items:
            pk_val = item.get(self._pk_field)
            if pk_val:
                self._table.delete_item(Key={self._pk_field: pk_val})
        return len(items)

    def list_all(self, **filters) -> list:
        all_items = []
        scan_kwargs = {}

        if filters:
            filter_parts = []
            expr_values = {}
            expr_names = {}
            for key, value in filters.items():
                safe_key = f"#f_{key}"
                placeholder = f":v_{key}"
                expr_names[safe_key] = key
                expr_values[placeholder] = value
                filter_parts.append(f"{safe_key} = {placeholder}")
            scan_kwargs["FilterExpression"] = " AND ".join(filter_parts)
            scan_kwargs["ExpressionAttributeNames"] = expr_names
            scan_kwargs["ExpressionAttributeValues"] = expr_values

        while True:
            response = self._table.scan(**scan_kwargs)
            all_items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key

        return _wrap_list(all_items)

    def find_by(self, field: str, value) -> list:
        return self.list_all(**{field: value})

    def count(self, **filters) -> int:
        if filters:
            return len(self.list_all(**filters))
        total = 0
        scan_kwargs = {"Select": "COUNT"}
        while True:
            result = self._table.scan(**scan_kwargs)
            total += result.get("Count", 0)
            last_key = result.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key
        return total

    def batch_get_by_ids(self, ids: list) -> list:
        """Batch get items by primary key. DynamoDB supports max 100 keys per call."""
        if not ids:
            return []
        table_name = self._table.table_name
        all_items = []
        for i in range(0, len(ids), 100):
            batch = ids[i:i + 100]
            keys = [{self._pk_field: uid} for uid in batch]
            resp = self._connector._resource.batch_get_item(
                RequestItems={table_name: {"Keys": keys}}
            )
            all_items.extend(resp.get("Responses", {}).get(table_name, []))
        return _wrap_list(all_items)

    # -- Raw DynamoDB passthrough methods ------------------------------------
    # These delegate directly to the underlying boto3 Table resource so that
    # managers written against the old direct-access pattern continue to work.

    def raw_get_item(self, key: dict) -> Optional[dict]:
        resp = self._table.get_item(Key=key)
        return _wrap(resp.get("Item"))

    def raw_put_item(self, item: dict):
        self._table.put_item(Item=item)

    def raw_update_item(self, **kwargs):
        return self._table.update_item(**kwargs)

    def raw_delete_item(self, **kwargs):
        return self._table.delete_item(**kwargs)

    def raw_query(self, **kwargs):
        return self._table.query(**kwargs)

    def raw_scan(self, **kwargs):
        return self._table.scan(**kwargs)
