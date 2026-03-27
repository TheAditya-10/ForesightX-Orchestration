import httpx
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import AnalysisJob, AnalysisJobEvent
from app.db.session import get_job_with_events
from app.graph.workflow import build_workflow
from app.schemas.analyze import AnalysisJobEventResponse, AnalysisJobResponse, AnalyzeRequest, AnalyzeResponse
from app.services.analysis_service import SignalAnalysisService
from app.services.decision_service import GeminiDecisionService
from app.services.risk_service import RiskManagementService
from app.utils.config import OrchestrationSettings
from shared import get_logger


class OrchestrationRuntime:
    def __init__(
        self,
        settings: OrchestrationSettings,
        http_client: httpx.AsyncClient,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.settings = settings
        self.http_client = http_client
        self.session_factory = session_factory
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
        async with self.session_factory() as session:
            job = AnalysisJob(
                user_id=payload.user_id,
                ticker=payload.ticker,
                event=payload.event,
                status="running",
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)
            try:
                result = await self.workflow.ainvoke({"request": payload.model_dump()})
                response = AnalyzeResponse.model_validate(result["response"])
                trace = response.trace.model_dump()
                job.status = "completed"
                job.action = response.action
                job.confidence = Decimal(str(response.confidence))
                job.reasons = response.reason
                job.completed_at = datetime.now(timezone.utc)
                session.add_all(self._build_job_events(job=job, trace=trace))
                await session.commit()
                return response.model_copy(update={"job_id": str(job.id)})
            except Exception as exc:
                job.status = "failed"
                job.failure_reason = str(exc)[:512]
                job.completed_at = datetime.now(timezone.utc)
                failure_event = AnalysisJobEvent(
                    analysis_job_id=job.id,
                    sequence_number=1,
                    node_name="failure",
                    tools_used=[],
                    payload={"error": str(exc)},
                )
                session.add(failure_event)
                await session.commit()
                raise

    async def get_job(self, job_id: str) -> AnalysisJobResponse:
        async with self.session_factory() as session:
            job = await get_job_with_events(session, job_id)
            if job is None:
                raise RuntimeError(f"Analysis job {job_id} not found")
            return self._serialize_job(job)

    async def list_jobs(self, user_id: str | None = None, limit: int = 20) -> list[AnalysisJobResponse]:
        async with self.session_factory() as session:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            query = (
                select(AnalysisJob)
                .options(selectinload(AnalysisJob.events))
                .order_by(AnalysisJob.created_at.desc())
                .limit(limit)
            )
            if user_id:
                query = query.where(AnalysisJob.user_id == user_id)
            result = await session.execute(query)
            jobs = result.scalars().unique().all()
            return [self._serialize_job(job) for job in jobs]

    def _build_job_events(self, job: AnalysisJob, trace: dict) -> list[AnalysisJobEvent]:
        events: list[AnalysisJobEvent] = []
        tools_by_node = self._group_tools_by_node(trace)
        payload_by_node = trace.get("intermediate_data", {})
        for sequence_number, node_name in enumerate(trace.get("execution_order", []), start=1):
            payload_key = self._payload_key_for_node(node_name)
            events.append(
                AnalysisJobEvent(
                    analysis_job_id=job.id,
                    sequence_number=sequence_number,
                    node_name=node_name,
                    tools_used=tools_by_node.get(node_name, []),
                    payload=payload_by_node.get(payload_key),
                )
            )
        return events

    def _group_tools_by_node(self, trace: dict) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        tools = list(trace.get("tools_used", []))
        if tools:
            grouped["data_fetch_node"] = tools[:4]
            if len(tools) > 4:
                grouped["analysis_node"] = tools[4:]
        return grouped

    @staticmethod
    def _payload_key_for_node(node_name: str) -> str:
        mapping = {
            "event_node": "request",
            "data_fetch_node": "market_data",
            "analysis_node": "analysis",
            "decision_node": "decision",
            "risk_check_node": "risk_check",
            "response_node": "final_response",
        }
        return mapping.get(node_name, node_name)

    @staticmethod
    def _serialize_job(job: AnalysisJob) -> AnalysisJobResponse:
        return AnalysisJobResponse(
            job_id=str(job.id),
            user_id=job.user_id,
            ticker=job.ticker,
            event=job.event,
            status=job.status,
            action=job.action,
            confidence=float(job.confidence) if job.confidence is not None else None,
            reasons=job.reasons or [],
            failure_reason=job.failure_reason,
            created_at=job.created_at,
            completed_at=job.completed_at,
            events=[
                AnalysisJobEventResponse(
                    sequence_number=event.sequence_number,
                    node_name=event.node_name,
                    tools_used=event.tools_used,
                    payload=event.payload,
                    created_at=event.created_at,
                )
                for event in job.events
            ],
        )
