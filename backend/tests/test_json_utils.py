"""Tests for utils/json_utils.py — Decimal handling."""
import json
from decimal import Decimal

from utils.json_utils import SafeEncoder, safe_dumps, AppJSONProvider


class TestSafeEncoder:
    def test_decimal_integer(self):
        assert json.dumps(Decimal("42"), cls=SafeEncoder) == "42"

    def test_decimal_float(self):
        assert json.dumps(Decimal("0.7"), cls=SafeEncoder) == "0.7"

    def test_nested_decimals(self):
        data = {"temperature": Decimal("0.7"), "max_tokens": Decimal("4096")}
        result = json.loads(json.dumps(data, cls=SafeEncoder))
        assert result == {"temperature": 0.7, "max_tokens": 4096}

    def test_deeply_nested(self):
        data = {"config": {"models": [{"rate": Decimal("125.50")}]}}
        result = json.loads(json.dumps(data, cls=SafeEncoder))
        assert result["config"]["models"][0]["rate"] == 125.5

    def test_non_decimal_raises(self):
        import pytest
        with pytest.raises(TypeError):
            json.dumps(object(), cls=SafeEncoder)


class TestSafeDumps:
    def test_handles_decimals(self):
        result = safe_dumps({"val": Decimal("3.14")})
        assert json.loads(result) == {"val": 3.14}

    def test_plain_data_unchanged(self):
        result = safe_dumps({"a": 1, "b": "hello"})
        assert json.loads(result) == {"a": 1, "b": "hello"}


class TestAppJSONProvider:
    def test_jsonify_with_decimals(self):
        from flask import Flask, jsonify

        app = Flask(__name__)
        app.json_provider_class = AppJSONProvider
        app.json = AppJSONProvider(app)

        with app.app_context():
            resp = jsonify({
                "temperature": Decimal("0.7"),
                "count": Decimal("100"),
                "nested": {"rate": Decimal("50.25")},
            })
            data = json.loads(resp.get_data(as_text=True))
            assert data["temperature"] == 0.7
            assert data["count"] == 100
            assert data["nested"]["rate"] == 50.25
