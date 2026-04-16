"""Utility to build SQLAlchemy ORM models from schema dataclasses + entity metadata."""
import dataclasses
import typing

from sqlalchemy import Column, String, Boolean, Float, Integer, Text
from sqlalchemy.orm import declarative_base

from database.repositories.entities import ENTITIES

Base = declarative_base()

# Python type -> SQLAlchemy column type (str is default, overridden by text_fields)
_PYTHON_TYPE_MAP = {
    str: String,
    int: Integer,
    float: Float,
    bool: Boolean,
}

# SQLAlchemy reserves 'metadata' on declarative classes
_RESERVED_ATTR_NAMES = {"metadata"}


def _unwrap_optional(type_hint):
    """Extract the inner type from Optional[X] (Union[X, None])."""
    origin = getattr(type_hint, "__origin__", None)
    if origin is typing.Union:
        args = [a for a in type_hint.__args__ if a is not type(None)]
        if len(args) == 1:
            return args[0], True
    return type_hint, False


def _get_default(dc_field):
    """Extract a plain default value from a dataclass field (skip factories)."""
    if dc_field.default is not dataclasses.MISSING:
        return dc_field.default
    return None


def build_models():
    """Build SQLAlchemy ORM models by introspecting schema dataclasses."""
    models = {}
    for logical_name, entity in ENTITIES.items():
        schema = entity.schema
        pk_set = set(entity.pk)
        index_set = set(entity.indexes)
        unique_set = set(entity.unique)
        text_set = set(entity.text_fields)
        non_nullable_set = set(entity.non_nullable)

        hints = typing.get_type_hints(schema)
        dc_fields = {f.name: f for f in dataclasses.fields(schema)}

        attrs = {"__tablename__": logical_name}
        for field_name, type_hint in hints.items():
            base_type, is_optional = _unwrap_optional(type_hint)
            is_pk = field_name in pk_set

            if field_name in text_set:
                col_type = Text
            else:
                col_type = _PYTHON_TYPE_MAP.get(base_type, String)

            nullable = not is_pk and field_name not in non_nullable_set and is_optional

            # Handle reserved attribute names by using an alias
            attr_name = f"{field_name}_" if field_name in _RESERVED_ATTR_NAMES else field_name
            col_kwargs = dict(
                primary_key=is_pk,
                nullable=nullable,
                unique=field_name in unique_set,
                index=field_name in index_set,
                default=_get_default(dc_fields[field_name]),
            )
            if attr_name != field_name:
                # Column name in DB stays as field_name, attr name on class uses alias
                attrs[attr_name] = Column(field_name, col_type, **col_kwargs)
            else:
                attrs[field_name] = Column(col_type, **col_kwargs)

        class_name = logical_name.title().replace("_", "")
        models[logical_name] = type(class_name, (Base,), attrs)

    return models


# Built once at import time
TABLE_MODEL_MAP = build_models()
