import asyncio
from copy import deepcopy
from datetime import datetime, timezone

from langgraph.graph import END, START, StateGraph

from app.graph.state import WorkflowState
from app.schemas.analyze import AnalyzeRequest
from app.tools.service_tools import (
    get_indicators,
    get_sentiment,
    get_stock_price,
    get_user_portfolio,
    predict_pattern,
    suggest_trade,
)


def _append_trace(
    state: WorkflowState,
    node_name: str,
    *,
    tools_used: list[str] | None = None,
    intermediate_key: str | None = None,
    intermediate_value: dict | None = None,
) -> dict:
    trace = deepcopy(
        state.get(
            "trace",
            {
                "tools_used": [],
                "execution_order": [],
                "intermediate_data": {},
            },
        )
    )
    trace["execution_order"].append(node_name)
    if tools_used:
        trace["tools_used"].extend(tools_used)
    if intermediate_key and intermediate_value is not None:
        trace["intermediate_data"][intermediate_key] = intermediate_value
    return trace


def build_workflow(runtime):
    async def event_node(state: WorkflowState) -> WorkflowState:
        request_model = AnalyzeRequest.model_validate(state["request"])
        trace = _append_trace(
            state,
            "event_node",
            intermediate_key="request",
            intermediate_value=request_model.model_dump(),
        )
        return {
            "validated_request": request_model.model_dump(),
            "trace": trace,
        }

    async def data_fetch_node(state: WorkflowState) -> WorkflowState:
        request = AnalyzeRequest.model_validate(state["validated_request"])
        price, indicators, sentiment, pattern = await asyncio.gather(
            get_stock_price(
                ticker=request.ticker,
                client=runtime.http_client,
                settings=runtime.settings,
                logger=runtime.logger,
            ),
            get_indicators(
                ticker=request.ticker,
                client=runtime.http_client,
                settings=runtime.settings,
                logger=runtime.logger,
            ),
            get_sentiment(
                ticker=request.ticker,
                client=runtime.http_client,
                settings=runtime.settings,
                logger=runtime.logger,
            ),
            predict_pattern(
                ticker=request.ticker,
                client=runtime.http_client,
                settings=runtime.settings,
                logger=runtime.logger,
            ),
        )
        market_data = {
            "price": price,
            "indicators": indicators,
            "sentiment": sentiment,
            "pattern": pattern,
        }
        trace = _append_trace(
            state,
            "data_fetch_node",
            tools_used=["get_stock_price", "get_indicators", "get_sentiment", "predict_pattern"],
            intermediate_key="market_data",
            intermediate_value=market_data,
        )
        return {"market_data": market_data, "trace": trace}

    async def analysis_node(state: WorkflowState) -> WorkflowState:
        request = AnalyzeRequest.model_validate(state["validated_request"])
        portfolio = await get_user_portfolio(
            user_id=request.user_id,
            client=runtime.http_client,
            settings=runtime.settings,
            logger=runtime.logger,
        )
        analysis = runtime.analysis_service.combine_signals(
            ticker=request.ticker,
            market_data=state["market_data"],
            portfolio=portfolio,
        )
        trace = _append_trace(
            state,
            "analysis_node",
            tools_used=["get_user_portfolio"],
            intermediate_key="analysis",
            intermediate_value={"portfolio": portfolio, "signals": analysis},
        )
        return {"portfolio": portfolio, "analysis": analysis, "trace": trace}

    async def decision_node(state: WorkflowState) -> WorkflowState:
        request = AnalyzeRequest.model_validate(state["validated_request"])
        fallback = suggest_trade(
            signals=state["analysis"],
            portfolio=state["portfolio"],
        )
        try:
            decision = await runtime.decision_service.decide_action(
                request=request,
                analysis=state["analysis"],
                portfolio=state["portfolio"],
                fallback=fallback,
            )
        except Exception as exc:
            runtime.logger.warning(f"Gemini decision fallback engaged: {exc}")
            decision = {
                **fallback,
                "decision_source": "heuristic_fallback",
                "fallback_used": True,
            }
        trace = _append_trace(
            state,
            "decision_node",
            intermediate_key="decision",
            intermediate_value=decision,
        )
        return {"decision": decision, "trace": trace}

    async def risk_check_node(state: WorkflowState) -> WorkflowState:
        request = AnalyzeRequest.model_validate(state["validated_request"])
        risk_checked = runtime.risk_service.apply(
            ticker=request.ticker,
            decision=state["decision"],
            analysis=state["analysis"],
            portfolio=state["portfolio"],
            price=state["market_data"]["price"],
        )
        trace = _append_trace(
            state,
            "risk_check_node",
            intermediate_key="risk_check",
            intermediate_value=risk_checked,
        )
        return {"decision": risk_checked, "trace": trace}

    async def response_node(state: WorkflowState) -> WorkflowState:
        trace = _append_trace(
            state,
            "response_node",
        )
        response = {
            "action": state["decision"]["action"],
            "confidence": state["decision"]["confidence"],
            "reason": state["decision"]["reason"],
            "trace": {
                **trace,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        trace["intermediate_data"]["final_response"] = response
        return {"response": response, "trace": trace}

    graph = StateGraph(WorkflowState)
    graph.add_node("event_node", event_node)
    graph.add_node("data_fetch_node", data_fetch_node)
    graph.add_node("analysis_node", analysis_node)
    graph.add_node("decision_node", decision_node)
    graph.add_node("risk_check_node", risk_check_node)
    graph.add_node("response_node", response_node)

    graph.add_edge(START, "event_node")
    graph.add_edge("event_node", "data_fetch_node")
    graph.add_edge("data_fetch_node", "analysis_node")
    graph.add_edge("analysis_node", "decision_node")
    graph.add_edge("decision_node", "risk_check_node")
    graph.add_edge("risk_check_node", "response_node")
    graph.add_edge("response_node", END)

    return graph.compile()
