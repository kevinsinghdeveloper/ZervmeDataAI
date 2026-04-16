"""
RBAC utilities for Zerve My Time.

Provides decorators and helpers for org-role-based and super-admin access control.
Uses the user_roles table as the source of truth for role checks.
"""
from functools import wraps
from flask import request, jsonify
from database.schemas.user import UserItem
from utils import user_role_service

# Org role hierarchy (higher index = more privileges)
ORG_ROLE_HIERARCHY = ["member", "manager", "admin", "owner"]

# Module-level db reference, set via init_rbac_db()
_db = None


def init_rbac_db(db_service) -> None:
    """Initialize the RBAC module with a DatabaseService instance."""
    global _db
    _db = db_service


def _get_current_user() -> UserItem | None:
    """Get the current user using request.user_id (set by @token_required)."""
    user_id = getattr(request, "user_id", None)
    if not user_id:
        return None
    if _db is None:
        return None
    user = _db.users.get_by_id(user_id)
    return user


def _get_org_id_from_request() -> str | None:
    """Extract org_id from X-Org-Id header, falling back to user's org_id for backward compat."""
    org_id = request.headers.get("X-Org-Id")
    if org_id:
        return org_id
    # Backward compat: fall back to user's inline org_id
    user = _get_current_user()
    return user.org_id if user else None


def _role_meets_minimum(user_role: str, minimum_role: str) -> bool:
    """Check if user_role meets the minimum required role level."""
    try:
        user_level = ORG_ROLE_HIERARCHY.index(user_role)
        min_level = ORG_ROLE_HIERARCHY.index(minimum_role)
        return user_level >= min_level
    except ValueError:
        return False


def org_role_required(*roles):
    """
    Decorator: require the user to have one of the specified org roles (or higher).

    Uses the user_roles table for role checks. Super admins bypass all checks.

    Usage:
        @token_required
        @org_role_required("manager", "admin", "owner")
        def some_route():
            ...

    The lowest role in the list is used as the minimum threshold.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = _get_current_user()
            if not user:
                return jsonify({"success": False, "error": "User not found"}), 404

            user_id = user.id

            # Super admins bypass org role checks
            if user_role_service.is_super_admin(user_id):
                request.current_user = user
                return f(*args, **kwargs)

            # Determine org context
            org_id = _get_org_id_from_request()
            if not org_id:
                return jsonify({"success": False, "error": "Organization context required (X-Org-Id header)"}), 400

            # Check role in user_roles table
            min_role = min(roles, key=lambda r: ORG_ROLE_HIERARCHY.index(r) if r in ORG_ROLE_HIERARCHY else 999)
            if not user_role_service.user_meets_minimum_role(user_id, org_id, min_role):
                # Fallback: check inline org_role on user record (backward compat
                # for users created before user_roles table migration)
                if user.org_id == org_id and user.org_role and _role_meets_minimum(user.org_role, min_role):
                    # Auto-heal: write the missing role to user_roles table
                    try:
                        user_role_service.grant_role(user_id=user_id, org_id=org_id, role=user.org_role, granted_by="system_migration")
                    except Exception:
                        pass  # non-critical
                else:
                    return jsonify({"success": False, "error": "Insufficient permissions"}), 403

            request.current_user = user
            request.current_org_id = org_id
            return f(*args, **kwargs)
        return decorated
    return decorator


def super_admin_required(f):
    """Decorator: require the user to be a global super admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = _get_current_user()
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        if not user_role_service.is_super_admin(user.id):
            return jsonify({"success": False, "error": "Super admin access required"}), 403
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


def get_user_org_context():
    """
    Helper to get current user and their org context.
    Returns (user, org_id) tuple. Must be called within a request with @token_required.
    """
    user = _get_current_user()
    org_id = _get_org_id_from_request()
    return user, org_id
