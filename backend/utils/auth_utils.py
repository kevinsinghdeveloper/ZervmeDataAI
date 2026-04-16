"""
Authentication utilities - Cognito JWT validation.
Validates RS256 JWTs issued by AWS Cognito User Pool.
"""
import os
import json
import time
import urllib.request
from functools import wraps
from flask import request, jsonify
import jwt

COGNITO_REGION = os.getenv("AWS_REGION_NAME", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "")
COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

# Cache JWKS keys
_jwks_cache = {"keys": None, "fetched_at": 0}
JWKS_CACHE_TTL = 3600


def _get_jwks():
    """Fetch and cache Cognito JWKS public keys."""
    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < JWKS_CACHE_TTL:
        return _jwks_cache["keys"]
    response = urllib.request.urlopen(JWKS_URL)
    jwks = json.loads(response.read())
    _jwks_cache["keys"] = {
        k["kid"]: jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k))
        for k in jwks["keys"]
    }
    _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]


def decode_token(token: str) -> dict:
    """Decode and validate a Cognito JWT token."""
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    keys = _get_jwks()
    public_key = keys.get(kid)
    if not public_key:
        raise jwt.InvalidTokenError("Unknown key ID")
    return jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        issuer=COGNITO_ISSUER,
        options={"verify_exp": True, "verify_aud": False},
    )


def token_required(f):
    """Decorator to require a valid Cognito JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        if not token:
            return jsonify({"success": False, "error": "Authentication token required"}), 401
        try:
            payload = decode_token(token)
            request.user_id = payload.get("sub", payload.get("cognito:username"))
            request.user_email = payload.get("email")
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Token has expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"success": False, "error": f"Invalid token: {str(e)}"}), 401
        except Exception as e:
            return jsonify({"success": False, "error": f"Authentication failed: {str(e)}"}), 401
        return f(*args, **kwargs)
    return decorated
