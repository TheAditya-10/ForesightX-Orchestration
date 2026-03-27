from fastapi import APIRouter, Depends, Query, Request

from app.controllers.analyze_controller import AnalyzeController
from app.schemas.analyze import AnalysisJobListResponse, AnalysisJobResponse, AnalyzeRequest, AnalyzeResponse


router = APIRouter(tags=["analysis"])


def get_controller(request: Request) -> AnalyzeController:
    return AnalyzeController(runtime=request.app.state.runtime)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    payload: AnalyzeRequest,
    controller: AnalyzeController = Depends(get_controller),
) -> AnalyzeResponse:
    return await controller.analyze(payload)


@router.get("/analysis/jobs/{job_id}", response_model=AnalysisJobResponse)
async def get_analysis_job(
    job_id: str,
    controller: AnalyzeController = Depends(get_controller),
) -> AnalysisJobResponse:
    return await controller.get_job(job_id)


@router.get("/analysis/jobs", response_model=AnalysisJobListResponse)
async def list_analysis_jobs(
    user_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    controller: AnalyzeController = Depends(get_controller),
) -> AnalysisJobListResponse:
    return await controller.list_jobs(user_id=user_id, limit=limit)
