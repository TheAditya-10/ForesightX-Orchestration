from fastapi import HTTPException, status

from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.runtime import OrchestrationRuntime


class AnalyzeController:
    def __init__(self, runtime: OrchestrationRuntime) -> None:
        self.runtime = runtime

    async def analyze(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        try:
            return await self.runtime.run_analysis(payload)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
