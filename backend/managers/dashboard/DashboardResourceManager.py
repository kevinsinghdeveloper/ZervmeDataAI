"""Dashboard Resource Manager - read-only dashboard data for DynamicReportRenderer."""
import json
import logging
from abstractions.IResourceManager import IResourceManager
from abstractions.models.ResponseModel import ResponseModel
from abstractions.models.RequestResourceModel import RequestResourceModel
from database.schemas.report import ReportItem
from database.schemas.report_job import ReportJobItem

logger = logging.getLogger(__name__)


class DashboardResourceManager(IResourceManager):

    def _get_org_id(self, user_id: str) -> str:
        """Resolve org_id from user_id via the users repository."""
        user = self._db.users.get_by_id(str(user_id))
        return user.org_id if user else None

    def get(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "get_report_dashboard":
            return self._get_dashboard_for_report(req)
        elif action == "get_overview":
            return self._get_dashboard_overview(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def post(self, req: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Dashboard is read-only", status_code=405)

    def put(self, req: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Dashboard is read-only", status_code=405)

    def delete(self, req: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Dashboard is read-only", status_code=405)

    def _get_dashboard_for_report(self, req: RequestResourceModel) -> ResponseModel:
        try:
            org_id = self._get_org_id(req.user_id)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)

            report_id = req.data.get("report_id")
            if not report_id:
                return ResponseModel(success=False, error="report_id is required", status_code=400)

            # Fetch the report
            report_item = self._db.reports.get_by_key({"org_id": org_id, "id": report_id})
            if not report_item:
                return ResponseModel(success=False, error="Report not found", status_code=404)
            report = ReportItem.from_item(report_item)

            # Find the latest completed job for this report
            all_jobs = self._db.report_jobs.list_all(org_id=org_id)
            completed_jobs = [
                ReportJobItem.from_item(j) for j in all_jobs
                if j.get("report_id") == report_id and j.get("status") == "completed"
            ]
            completed_jobs.sort(
                key=lambda j: j.completed_at or "",
                reverse=True,
            )

            if not completed_jobs:
                return ResponseModel(
                    success=True,
                    data={
                        "report": report.to_api_dict(),
                        "template": None,
                        "data": None,
                        "message": "No completed jobs found for this report",
                    },
                )

            latest_job = completed_jobs[0]

            # Parse result_data from the job
            result_data = {}
            if latest_job.result_data:
                try:
                    result_data = (
                        json.loads(latest_job.result_data)
                        if isinstance(latest_job.result_data, str)
                        else latest_job.result_data
                    )
                except (json.JSONDecodeError, TypeError):
                    result_data = {"raw": latest_job.result_data}

            # Build a template for DynamicReportRenderer
            template = self._build_report_template(report, result_data)

            return ResponseModel(
                success=True,
                data={
                    "report": report.to_api_dict(),
                    "template": template,
                    "data": result_data,
                    "jobId": latest_job.id,
                    "completedAt": latest_job.completed_at,
                },
            )
        except Exception as e:
            logger.error("Failed to get dashboard for report: %s", str(e))
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _get_dashboard_overview(self, req: RequestResourceModel) -> ResponseModel:
        try:
            org_id = self._get_org_id(req.user_id)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)

            # Count projects
            projects = self._db.projects.list_all(org_id=org_id)
            project_count = len(projects) if projects else 0

            # Count reports
            reports = self._db.reports.list_all(org_id=org_id)
            report_count = len(reports) if reports else 0

            # Count jobs and compute stats
            all_jobs = self._db.report_jobs.list_all(org_id=org_id)
            total_jobs = len(all_jobs) if all_jobs else 0
            completed_jobs = sum(1 for j in (all_jobs or []) if j.get("status") == "completed")
            failed_jobs = sum(1 for j in (all_jobs or []) if j.get("status") == "failed")
            running_jobs = sum(1 for j in (all_jobs or []) if j.get("status") == "running")

            # Recent jobs (last 10, sorted by created_at desc)
            job_items = [ReportJobItem.from_item(j) for j in (all_jobs or [])]
            job_items.sort(key=lambda j: j.created_at or "", reverse=True)
            recent_jobs = [j.to_api_dict() for j in job_items[:10]]

            return ResponseModel(
                success=True,
                data={
                    "overview": {
                        "projectCount": project_count,
                        "reportCount": report_count,
                        "totalJobs": total_jobs,
                        "completedJobs": completed_jobs,
                        "failedJobs": failed_jobs,
                        "runningJobs": running_jobs,
                    },
                    "recentJobs": recent_jobs,
                },
            )
        except Exception as e:
            logger.error("Failed to get dashboard overview: %s", str(e))
            return ResponseModel(success=False, error=str(e), status_code=500)

    @staticmethod
    def _build_report_template(report: ReportItem, result_data: dict) -> dict:
        """Build a basic report template with text summary and table sections."""
        sections = []

        # Text summary section
        sections.append({
            "type": "text",
            "title": "Summary",
            "content": f"Report: {report.name}",
        })

        # If result_data has a summary key, add it
        if isinstance(result_data, dict) and result_data.get("summary"):
            sections.append({
                "type": "text",
                "title": "Analysis Summary",
                "content": result_data["summary"],
            })

        # If result_data has tabular data, add a table section
        if isinstance(result_data, dict) and result_data.get("rows"):
            rows = result_data["rows"]
            columns = list(rows[0].keys()) if rows else []
            sections.append({
                "type": "table",
                "title": "Data",
                "columns": columns,
                "dataKey": "rows",
            })

        # If result_data has charts config, pass through
        if isinstance(result_data, dict) and result_data.get("charts"):
            for chart in result_data["charts"]:
                sections.append({
                    "type": "chart",
                    "title": chart.get("title", "Chart"),
                    "chartType": chart.get("chartType", "bar"),
                    "dataKey": chart.get("dataKey", "rows"),
                    "config": chart.get("config", {}),
                })

        return {
            "reportName": report.name,
            "reportId": report.id,
            "sections": sections,
        }
