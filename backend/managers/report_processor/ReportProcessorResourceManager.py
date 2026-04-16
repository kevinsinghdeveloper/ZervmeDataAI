"""Report Processor Resource Manager - ETL job execution with job tracking."""
import json
import logging
from datetime import datetime
from abstractions.IResourceManager import IResourceManager
from abstractions.models.ResponseModel import ResponseModel
from abstractions.models.RequestResourceModel import RequestResourceModel
from database.schemas.report_job import ReportJobItem

logger = logging.getLogger(__name__)


class ReportProcessorResourceManager(IResourceManager):

    @property
    def _etl(self):
        """Shortcut to the ETL service instance."""
        return self._service_managers.get("etl")

    def _get_org_id(self, user_id: str) -> str:
        """Resolve org_id from user_id via the users repository."""
        user = self._db.users.get_by_id(str(user_id))
        return user.org_id if user else None

    def get(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "get_status":
            return self._get_status(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def post(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "start_job":
            return self._start_job(req)
        elif action == "stop_job":
            return self._stop_job(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def put(self, req: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def delete(self, req: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def _start_job(self, req: RequestResourceModel) -> ResponseModel:
        job = None
        org_id = None
        try:
            report_name = req.data.get("report_name")
            if not report_name:
                return ResponseModel(success=False, error="report_name is required", status_code=400)

            org_id = self._get_org_id(req.user_id)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)

            report_id = req.data.get("report_id", "")

            # Create job record in pending state
            now = datetime.utcnow().isoformat()
            job = ReportJobItem(
                org_id=org_id,
                report_id=report_id,
                status="pending",
                created_at=now,
                updated_at=now,
            )
            self._db.report_jobs.create(job.to_item())
            logger.info("Created report job %s for org %s", job.id, org_id)

            # Transition to running
            self._update_job_status(org_id, job.id, "running", started_at=now)

            # Execute ETL
            task_params = req.data.get("task_params", {})
            llm_config = req.data.get("llm_config", {})
            result = self._etl.run_report(report_name, task_params, llm_config)

            # Mark completed and store result
            completed_at = datetime.utcnow().isoformat()
            result_json = json.dumps(result) if not isinstance(result, str) else result
            self._update_job_status(
                org_id, job.id, "completed",
                completed_at=completed_at,
                result_data=result_json,
            )
            logger.info("Job %s completed successfully", job.id)

            job.status = "completed"
            job.started_at = now
            job.completed_at = completed_at
            job.result_data = result_json
            return ResponseModel(success=True, data={"job": job.to_api_dict()}, status_code=201)

        except Exception as e:
            logger.error("Job failed: %s", str(e))
            if job and org_id:
                try:
                    self._update_job_status(
                        org_id, job.id, "failed",
                        error_message=str(e),
                        completed_at=datetime.utcnow().isoformat(),
                    )
                except Exception as update_err:
                    logger.error("Failed to update job status: %s", str(update_err))
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _get_status(self, req: RequestResourceModel) -> ResponseModel:
        try:
            job_id = req.data.get("job_id")
            if not job_id:
                return ResponseModel(success=False, error="job_id is required", status_code=400)

            org_id = self._get_org_id(req.user_id)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)

            item = self._db.report_jobs.get_by_key({"org_id": org_id, "id": job_id})
            if not item:
                return ResponseModel(success=False, error="Job not found", status_code=404)

            job = ReportJobItem.from_item(item)
            return ResponseModel(success=True, data={"job": job.to_api_dict()})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _stop_job(self, req: RequestResourceModel) -> ResponseModel:
        try:
            job_id = req.data.get("job_id")
            if not job_id:
                return ResponseModel(success=False, error="job_id is required", status_code=400)
            return ResponseModel(success=True, message=f"Stop requested for job {job_id}")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update_job_status(self, org_id: str, job_id: str, status: str, **kwargs) -> None:
        """Update a report job's status and optional fields in DynamoDB."""
        now = datetime.utcnow().isoformat()

        expr_parts = []
        values = {}
        names = {"#st": "status"}

        expr_parts.append("#st = :vstatus")
        values[":vstatus"] = status

        expr_parts.append("updated_at = :vupdated")
        values[":vupdated"] = now

        idx = 0
        for key, val in kwargs.items():
            if val is not None:
                expr_parts.append(f"{key} = :v{idx}")
                values[f":v{idx}"] = val
                idx += 1

        self._db.report_jobs.raw_update_item(
            Key={"org_id": org_id, "id": job_id},
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeValues=values,
            ExpressionAttributeNames=names,
        )
