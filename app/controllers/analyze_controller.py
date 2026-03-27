from fastapi import HTTPException, status

from app.schemas.analyze import AnalysisJobListResponse, AnalysisJobResponse, AnalyzeRequest, AnalyzeResponse
from app.services.runtime import OrchestrationRuntime


class AnalyzeController:
    def __init__(self, runtime: OrchestrationRuntime) -> None:
        self.runtime = runtime

    async def analyze(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        try:
            return await self.runtime.run_analysis(payload)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    async def get_job(self, job_id: str) -> AnalysisJobResponse:
        try:
            return await self.runtime.get_job(job_id)
        except Exception as exc:
            code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_502_BAD_GATEWAY
            raise HTTPException(status_code=code, detail=str(exc)) from exc

    async def list_jobs(self, user_id: str | None, limit: int) -> AnalysisJobListResponse:
        try:
            jobs = await self.runtime.list_jobs(user_id=user_id, limit=limit)
            return AnalysisJobListResponse(jobs=jobs)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
