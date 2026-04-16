import json
from decimal import Decimal
from flask.json.provider import DefaultJSONProvider


class SafeEncoder(json.JSONEncoder):
    """JSON encoder that handles DynamoDB Decimal types."""

    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o == int(o) else float(o)
        return super().default(o)


def safe_dumps(obj, **kwargs):
    """json.dumps that handles Decimal values."""
    kwargs.setdefault("cls", SafeEncoder)
    return json.dumps(obj, **kwargs)


class AppJSONProvider(DefaultJSONProvider):
    """Flask JSON provider that handles DynamoDB Decimal types."""

    def dumps(self, obj, **kwargs):
        kwargs.setdefault("cls", SafeEncoder)
        return json.dumps(obj, **kwargs)
