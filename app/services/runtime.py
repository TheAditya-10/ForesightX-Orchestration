import httpx

from app.graph.workflow import build_workflow
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.analysis_service import SignalAnalysisService
from app.services.decision_service import GeminiDecisionService
from app.services.risk_service import RiskManagementService
from app.utils.config import OrchestrationSettings
from shared import get_logger


class OrchestrationRuntime:
    def __init__(self, settings: OrchestrationSettings, http_client: httpx.AsyncClient) -> None:
        self.settings = settings
        self.http_client = http_client
        self.logger = get_logger(settings.service_name, "runtime")
        self.analysis_service = SignalAnalysisService(service_name=settings.service_name)
        self.decision_service = GeminiDecisionService(settings=settings)
        self.risk_service = RiskManagementService(settings=settings)
        self.workflow = None

    async def start(self) -> None:
        self.workflow = build_workflow(self)

    async def close(self) -> None:
        await self.http_client.aclose()

    async def run_analysis(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        if self.workflow is None:
            raise RuntimeError("Workflow not initialized")
        result = await self.workflow.ainvoke({"request": payload.model_dump()})
        return AnalyzeResponse.model_validate(result["response"])
