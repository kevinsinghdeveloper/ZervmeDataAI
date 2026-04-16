"""Legacy Admin Resource Manager - kept for backward compatibility.
New admin functionality is in SuperAdminResourceManager, OrganizationResourceManager, etc.
"""
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel


class AdminResourceManager(IResourceManager):

    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        action = request_resource_model.data.get("action")
        if action == "dashboard":
            return self._get_dashboard(request_resource_model)
        return ResponseModel(success=False, error="Unknown action", status_code=400)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Legacy admin endpoint deprecated", status_code=410)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Legacy admin endpoint deprecated", status_code=410)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Legacy admin endpoint deprecated", status_code=410)

    def _get_dashboard(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Basic dashboard stats using new tables."""
        try:
            user_scan = self._db.users.raw_scan(Select="COUNT")
            org_scan = self._db.organizations.raw_scan(Select="COUNT")

            return ResponseModel(
                success=True,
                data={
                    "totalUsers": user_scan.get("Count", 0),
                    "totalOrganizations": org_scan.get("Count", 0),
                },
                status_code=200,
            )
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)
