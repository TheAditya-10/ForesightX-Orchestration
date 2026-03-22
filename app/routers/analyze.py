from fastapi import APIRouter, Depends, Request

from app.controllers.analyze_controller import AnalyzeController
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse


router = APIRouter(tags=["analysis"])


def get_controller(request: Request) -> AnalyzeController:
    return AnalyzeController(runtime=request.app.state.runtime)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    payload: AnalyzeRequest,
    controller: AnalyzeController = Depends(get_controller),
) -> AnalyzeResponse:
    return await controller.analyze(payload)
