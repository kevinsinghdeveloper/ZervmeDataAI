import os
import json
from apig_wsgi import make_lambda_handler
from run_web_service import create_app


class StripStageMiddleware:
    """Strip the API Gateway stage prefix (e.g. /dev) from PATH_INFO."""

    def __init__(self, app, stage_prefix):
        self.app = app
        self.prefix = stage_prefix

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path.startswith(self.prefix):
            environ["PATH_INFO"] = path[len(self.prefix):] or "/"
            environ["SCRIPT_NAME"] = self.prefix
        return self.app(environ, start_response)


app = create_app()

# API Gateway HTTP API includes the stage name in the path (e.g. /dev/api/health)
# but Flask routes are registered without it (/api/health). Strip it.
stage = os.getenv("API_STAGE", "dev")
wsgi_app = StripStageMiddleware(app, f"/{stage}")

_apig_handler = make_lambda_handler(wsgi_app)


def handler(event, context):
    """Wrap apig_wsgi handler to ensure event structure is complete.

    API Gateway HTTP API v2 events sometimes arrive with missing fields
    in requestContext.http (e.g. sourceIp), which causes apig_wsgi to
    crash with KeyError. This wrapper fills in safe defaults.
    """
    # Non-HTTP events (warmup, EventBridge, etc.) - return early
    if not isinstance(event, dict) or "requestContext" not in event:
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "ok"}),
        }

    # Ensure requestContext.http exists with required fields for v2 format
    rc = event.get("requestContext", {})
    http = rc.get("http")
    if isinstance(http, dict):
        http.setdefault("sourceIp", "0.0.0.0")
        http.setdefault("method", "GET")
        http.setdefault("path", "/")
        http.setdefault("protocol", "HTTP/1.1")
        http.setdefault("userAgent", "")
    elif "version" in event and event.get("version") == "2.0":
        # v2 event but missing http block entirely
        rc["http"] = {
            "method": event.get("httpMethod", "GET"),
            "path": event.get("rawPath", "/"),
            "protocol": "HTTP/1.1",
            "sourceIp": "0.0.0.0",
            "userAgent": "",
        }
        event["requestContext"] = rc

    return _apig_handler(event, context)
