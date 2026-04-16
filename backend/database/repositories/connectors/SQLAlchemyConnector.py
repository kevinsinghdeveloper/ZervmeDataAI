"""SQLAlchemy connector and base repository."""
import os
from typing import Dict, Optional

from sqlalchemy import create_engine, text, inspect as sa_inspect
from sqlalchemy.orm import sessionmaker, Session

from abstractions.IDatabaseConnector import IDatabaseConnector
from abstractions.IRepository import IRepository
from utils.db.model_builder import Base, TABLE_MODEL_MAP


# ---------------------------------------------------------------------------
# Connector
# ---------------------------------------------------------------------------

class SQLAlchemyConnector(IDatabaseConnector):

    def __init__(self):
        self._engine = None
        self._session_factory = None

    def initialize(self, config: Optional[Dict] = None):
        database_url = os.getenv("DATABASE_URL", "postgresql://zerve:zerve@localhost:5432/zerve")
        pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))

        self._engine = create_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
        )
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)
        print(f"PostgreSQL connected: {database_url.split('@')[-1] if '@' in database_url else 'database'}")

    def health_check(self) -> bool:
        if not self._engine:
            return False
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def close(self):
        if self._engine:
            self._engine.dispose()

    def get_session(self) -> Session:
        return self._session_factory()

    def get_repository(self, table_name: str, pk_field: str = "id") -> "SQLAlchemyRepository":
        model_class = TABLE_MODEL_MAP.get(table_name)
        if not model_class:
            raise ValueError(f"Unknown table: {table_name}")
        return SQLAlchemyRepository(self, model_class, pk_field)

    @property
    def engine(self):
        return self._engine


# ---------------------------------------------------------------------------
# Base Repository
# ---------------------------------------------------------------------------

class SQLAlchemyRepository(IRepository):

    def __init__(self, connector: SQLAlchemyConnector, model_class, pk_field: str = "id"):
        self._connector = connector
        self._model = model_class
        self._pk_field = pk_field
        # Build column-name -> attribute-name mapping for reserved name handling
        # e.g. {"metadata": "metadata_"} when the DB column is "metadata" but the
        # Python attribute on the ORM class is "metadata_"
        self._col_to_attr = {}
        for attr in sa_inspect(model_class).mapper.column_attrs:
            col_name = attr.columns[0].name
            if col_name != attr.key:
                self._col_to_attr[col_name] = attr.key

    def _map_key(self, col_name: str) -> str:
        """Map a dict/column key to the model attribute name."""
        return self._col_to_attr.get(col_name, col_name)

    def _to_dict(self, obj) -> Optional[dict]:
        if obj is None:
            return None
        result = {}
        for attr in sa_inspect(obj.__class__).mapper.column_attrs:
            # Use the actual column name (not the python attr name) as the dict key
            col_name = attr.columns[0].name
            result[col_name] = getattr(obj, attr.key)
        return result

    def get_by_id(self, id: str) -> Optional[dict]:
        session = self._connector.get_session()
        try:
            obj = session.query(self._model).filter(
                getattr(self._model, self._pk_field) == id
            ).first()
            return self._to_dict(obj)
        finally:
            session.close()

    def get_by_key(self, key: dict) -> Optional[dict]:
        session = self._connector.get_session()
        try:
            query = session.query(self._model)
            for k, v in key.items():
                query = query.filter(getattr(self._model, self._map_key(k)) == v)
            obj = query.first()
            return self._to_dict(obj)
        finally:
            session.close()

    def create(self, item: dict) -> dict:
        session = self._connector.get_session()
        try:
            mapped = {self._map_key(k): v for k, v in item.items() if hasattr(self._model, self._map_key(k))}
            obj = self._model(**mapped)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return self._to_dict(obj)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def upsert(self, item: dict) -> dict:
        session = self._connector.get_session()
        try:
            pk_cols = [c.name for c in sa_inspect(self._model).primary_key]
            query = session.query(self._model)
            for col in pk_cols:
                if col in item:
                    query = query.filter(getattr(self._model, self._map_key(col)) == item[col])
            existing = query.first()

            if existing:
                for k, v in item.items():
                    attr = self._map_key(k)
                    if hasattr(self._model, attr):
                        setattr(existing, attr, v)
                session.commit()
                session.refresh(existing)
                return self._to_dict(existing)
            else:
                mapped = {self._map_key(k): v for k, v in item.items() if hasattr(self._model, self._map_key(k))}
                obj = self._model(**mapped)
                session.add(obj)
                session.commit()
                session.refresh(obj)
                return self._to_dict(obj)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update(self, id: str, fields: dict) -> Optional[dict]:
        if not fields:
            return self.get_by_id(id)
        session = self._connector.get_session()
        try:
            obj = session.query(self._model).filter(
                getattr(self._model, self._pk_field) == id
            ).first()
            if not obj:
                return None
            for key, value in fields.items():
                attr = self._map_key(key)
                if hasattr(self._model, attr):
                    setattr(obj, attr, value)
            session.commit()
            session.refresh(obj)
            return self._to_dict(obj)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_if(self, id: str, fields: dict, conditions: dict) -> bool:
        session = self._connector.get_session()
        try:
            query = session.query(self._model).filter(
                getattr(self._model, self._pk_field) == id
            )
            for k, v in conditions.items():
                query = query.filter(getattr(self._model, self._map_key(k)) == v)
            update_dict = {self._map_key(k): v for k, v in fields.items() if hasattr(self._model, self._map_key(k))}
            result = query.update(update_dict)
            session.commit()
            return result > 0
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, id: str) -> bool:
        session = self._connector.get_session()
        try:
            obj = session.query(self._model).filter(
                getattr(self._model, self._pk_field) == id
            ).first()
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_by_key(self, key: dict) -> bool:
        session = self._connector.get_session()
        try:
            query = session.query(self._model)
            for k, v in key.items():
                query = query.filter(getattr(self._model, self._map_key(k)) == v)
            result = query.delete()
            session.commit()
            return result > 0
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_where(self, field: str, value) -> int:
        session = self._connector.get_session()
        try:
            result = session.query(self._model).filter(
                getattr(self._model, self._map_key(field)) == value
            ).delete()
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_all(self, **filters) -> list:
        session = self._connector.get_session()
        try:
            query = session.query(self._model)
            for key, value in filters.items():
                attr = self._map_key(key)
                if hasattr(self._model, attr):
                    query = query.filter(getattr(self._model, attr) == value)
            return [self._to_dict(obj) for obj in query.all()]
        finally:
            session.close()

    def find_by(self, field: str, value) -> list:
        return self.list_all(**{field: value})

    def count(self, **filters) -> int:
        session = self._connector.get_session()
        try:
            query = session.query(self._model)
            for key, value in filters.items():
                attr = self._map_key(key)
                if hasattr(self._model, attr):
                    query = query.filter(getattr(self._model, attr) == value)
            return query.count()
        finally:
            session.close()

    # -- Raw DynamoDB-compatible passthrough stubs ----------------------------
    # These translate DynamoDB-style raw calls to SQLAlchemy equivalents so
    # managers using the old direct-access pattern work with both backends.

    def raw_get_item(self, key: dict) -> Optional[dict]:
        return self.get_by_key(key)

    def raw_put_item(self, item: dict):
        self.upsert(item)

    def raw_update_item(self, **kwargs):
        # Extract Key and update fields from DynamoDB-style kwargs
        key = kwargs.get("Key", {})
        if not key:
            return
        # Best-effort: find item and update via composite key
        item = self.get_by_key(key)
        if item:
            # Parse simple SET expressions if possible
            expr = kwargs.get("UpdateExpression", "")
            values = kwargs.get("ExpressionAttributeValues", {})
            names = kwargs.get("ExpressionAttributeNames", {})
            fields = {}
            if expr.startswith("SET "):
                for part in expr[4:].split(","):
                    part = part.strip()
                    if "=" in part:
                        lhs, rhs = part.split("=", 1)
                        lhs = lhs.strip()
                        rhs = rhs.strip()
                        # Resolve attribute names
                        field = names.get(lhs, lhs)
                        value = values.get(rhs, rhs)
                        fields[field] = value
            if fields:
                session = self._connector.get_session()
                try:
                    query = session.query(self._model)
                    for k, v in key.items():
                        query = query.filter(getattr(self._model, self._map_key(k)) == v)
                    obj = query.first()
                    if obj:
                        for k, v in fields.items():
                            attr = self._map_key(k)
                            if hasattr(self._model, attr):
                                setattr(obj, attr, v)
                        session.commit()
                except Exception:
                    session.rollback()
                    raise
                finally:
                    session.close()

    def raw_delete_item(self, **kwargs):
        key = kwargs.get("Key", {})
        if key:
            self.delete_by_key(key)

    def raw_query(self, **kwargs):
        # Translate to list_all with filters from KeyConditionExpression
        # This is a best-effort stub; complex queries may need refinement
        return {"Items": self.list_all(), "Count": self.count()}

    def raw_scan(self, **kwargs):
        select = kwargs.get("Select", "")
        if select == "COUNT":
            return {"Count": self.count(), "Items": []}
        return {"Items": self.list_all(), "Count": self.count()}
