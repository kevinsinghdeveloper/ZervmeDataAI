"""
Zerve DataAI - Backend Web Service Entry Point

Follows the BE-ToStructured pattern: registers all controllers with their
resource managers, wiring together the 4-layer architecture
(abstractions -> controllers -> managers -> services).
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Ensure the backend directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database.DatabaseService import DatabaseService
from utils.json_utils import AppJSONProvider
from utils.user_role_service import init_user_role_service
from utils.rbac_utils import init_rbac_db

# Controllers
from controllers.auth.AuthController import AuthController
from controllers.config.ConfigController import ConfigController
from controllers.users.UserController import UserController
from controllers.audit.AuditController import AuditController
from controllers.admin.AdminController import AdminController
from controllers.organizations.OrganizationController import OrganizationController
from controllers.projects.ProjectController import ProjectController
from controllers.ai_chat.AIChatController import AIChatController
from controllers.notifications.NotificationController import NotificationController
from controllers.super_admin.SuperAdminController import SuperAdminController
from controllers.reports.ReportController import ReportController
from controllers.report_processor.ReportProcessorController import ReportProcessorController
from controllers.datasets.DatasetController import DatasetController
from controllers.model_configs.ModelConfigController import ModelConfigController
from controllers.dashboard.DashboardController import DashboardController

# Resource Managers
from managers.auth.AuthResourceManager import AuthResourceManager
from managers.config.ConfigResourceManager import ConfigResourceManager
from managers.users.UserResourceManager import UserResourceManager
from managers.audit.AuditResourceManager import AuditResourceManager
from managers.admin.AdminResourceManager import AdminResourceManager
from managers.organizations.OrganizationResourceManager import OrganizationResourceManager
from managers.projects.ProjectResourceManager import ProjectResourceManager
from managers.ai_chat.AIChatResourceManager import AIChatResourceManager
from managers.notifications.NotificationResourceManager import NotificationResourceManager
from managers.super_admin.SuperAdminResourceManager import SuperAdminResourceManager
from managers.reports.ReportResourceManager import ReportResourceManager
from managers.report_processor.ReportProcessorResourceManager import ReportProcessorResourceManager
from managers.datasets.DatasetResourceManager import DatasetResourceManager
from managers.model_configs.ModelConfigResourceManager import ModelConfigResourceManager
from managers.dashboard.DashboardResourceManager import DashboardResourceManager

# Services
from services.email.EmailService import EmailService
from services.user.UserService import UserService
from services.ai.AIService import AIService
from services.notification.NotificationService import NotificationService
from services.oauth.OAuthManager import OAuthManager
from services.etl.ETLService import ETLService

# Utils
from utils.register_components import register_controller


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.json_provider_class = AppJSONProvider
    app.json = AppJSONProvider(app)

    # CORS configuration
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=True)

    # App configuration
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50")) * 1024 * 1024
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")

    # Initialize database via DatabaseService
    db_service = DatabaseService()
    try:
        db_service.initialize()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("The app will start but database operations may fail.")

    # Initialize user role service and RBAC with injected repository
    if db_service.user_roles:
        init_user_role_service(db_service.user_roles)
    init_rbac_db(db_service)

    # ----- Initialize Services -----

    # Email Service
    email_service = EmailService()
    try:
        email_service.initialize()
        print("Email service initialized.")
    except Exception as e:
        print(f"Warning: Email service initialization failed: {e}")

    # User Service (Cognito admin operations)
    user_service = UserService()
    user_service.initialize()
    print("User service initialized.")

    # Storage Service
    uploads_bucket = os.getenv("UPLOADS_BUCKET")
    if uploads_bucket:
        from services.storage.S3StorageService import S3StorageService
        storage_service = S3StorageService(config={
            "bucket_name": uploads_bucket,
            "region": os.getenv("AWS_REGION_NAME", "us-east-1"),
        })
        storage_service.initialize()
        print(f"Storage: S3 bucket '{uploads_bucket}'")
    else:
        from services.storage.LocalStorageService import LocalStorageService
        storage_service = LocalStorageService(
            base_dir=os.getenv("UPLOAD_DIR", "uploads")
        )
        print("Storage: Local filesystem")

    # AI Service
    ai_service = AIService()
    ai_service.set_db(db_service)
    ai_service.initialize()
    print("AI service initialized.")

    # Notification Service
    notification_service = NotificationService()
    notification_service.set_db(db_service)
    notification_service.initialize()
    notification_service.set_email_service(email_service)
    print("Notification service initialized.")

    # OAuth Manager
    oauth_manager = OAuthManager()
    print(f"OAuth providers: {oauth_manager.list_providers() or 'none'}")

    # ETL Service
    etl_service = ETLService()
    etl_service.set_db(db_service)
    etl_service.initialize()
    print("ETL service initialized.")

    # ----- Service Managers Dictionary -----
    service_managers = {
        "db": db_service,
        "email": email_service,
        "storage": storage_service,
        "user": user_service,
        "ai": ai_service,
        "notification": notification_service,
        "oauth": oauth_manager,
        "etl": etl_service,
    }

    # ----- Register Controllers with Resource Managers -----

    # Auth
    auth_manager = AuthResourceManager(service_managers=service_managers)
    register_controller(app, AuthController, auth_manager)

    # Config (theme, first-user setup)
    config_manager = ConfigResourceManager(service_managers=service_managers)
    register_controller(app, ConfigController, config_manager)

    # Users (RBAC)
    user_manager = UserResourceManager(service_managers=service_managers)
    register_controller(app, UserController, user_manager)

    # Audit
    audit_manager = AuditResourceManager(service_managers=service_managers)
    register_controller(app, AuditController, audit_manager)

    # Admin (legacy - kept for backward compat)
    admin_manager = AdminResourceManager(service_managers=service_managers)
    register_controller(app, AdminController, admin_manager)

    # Organizations
    org_manager = OrganizationResourceManager(service_managers=service_managers)
    register_controller(app, OrganizationController, org_manager)

    # Projects
    project_manager = ProjectResourceManager(service_managers=service_managers)
    register_controller(app, ProjectController, project_manager)

    # AI Chat
    ai_chat_manager = AIChatResourceManager(service_managers=service_managers)
    register_controller(app, AIChatController, ai_chat_manager)

    # Notifications
    notification_manager = NotificationResourceManager(service_managers=service_managers)
    register_controller(app, NotificationController, notification_manager)

    # Super Admin
    super_admin_manager = SuperAdminResourceManager(service_managers=service_managers)
    register_controller(app, SuperAdminController, super_admin_manager)

    # Reports
    report_manager = ReportResourceManager(service_managers=service_managers)
    register_controller(app, ReportController, report_manager)

    # Report Processor (ETL pipeline)
    report_processor_manager = ReportProcessorResourceManager(service_managers=service_managers)
    register_controller(app, ReportProcessorController, report_processor_manager)

    # Datasets
    dataset_manager = DatasetResourceManager(service_managers=service_managers)
    register_controller(app, DatasetController, dataset_manager)

    # Model Configs
    model_config_manager = ModelConfigResourceManager(service_managers=service_managers)
    register_controller(app, ModelConfigController, model_config_manager)

    # Dashboard (read-only report dashboard)
    dashboard_manager = DashboardResourceManager(service_managers=service_managers)
    register_controller(app, DashboardController, dashboard_manager)

    # ----- Health Check -----
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "zerve-dataai-backend",
            "version": "2.0.0",
        }), 200

    # ----- Error Handlers -----
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({"success": False, "error": "File too large"}), 413

    return app


if __name__ == "__main__":
    app = create_app()
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "8000"))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    print(f"Starting Zerve DataAI Backend on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
