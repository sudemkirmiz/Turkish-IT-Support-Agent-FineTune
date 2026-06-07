import logging
import time
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

try:
    from .conversation_router import detect_intent, extract_tried_steps
    from .json_utils import JSONExtractionError, extract_json
    from .model_service import ModelConfigurationError, ModelIntegrationError, ModelServiceError, analyze_message
    from .prompts import build_contextual_prompt, build_out_of_scope_prompt, build_retry_prompt, build_smalltalk_prompt, build_unclear_prompt
    from .response_normalizer import collect_validation_issues, normalize_model_output
    from .schemas import AnalyzeRequest, ErrorResponse, ITSupportResponse, InvalidModelOutputResponse
    from .session_store import add_message, delete_session, get_or_create_session, get_session, list_sessions, update_active_issue
except ImportError:
    from app.conversation_router import detect_intent, extract_tried_steps
    from app.json_utils import JSONExtractionError, extract_json
    from app.model_service import ModelConfigurationError, ModelIntegrationError, ModelServiceError, analyze_message
    from app.prompts import build_contextual_prompt, build_out_of_scope_prompt, build_retry_prompt, build_smalltalk_prompt, build_unclear_prompt
    from app.response_normalizer import collect_validation_issues, normalize_model_output
    from app.schemas import AnalyzeRequest, ErrorResponse, ITSupportResponse, InvalidModelOutputResponse
    from app.session_store import add_message, delete_session, get_or_create_session, get_session, list_sessions, update_active_issue

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="IT Support Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "it-support-backend"}


@app.post(
    "/analyze",
    response_model=ITSupportResponse,
    responses={400: {"model": ErrorResponse}, 502: {"model": InvalidModelOutputResponse}},
)
def analyze(request: AnalyzeRequest) -> ITSupportResponse | JSONResponse:
    start_time = time.time()
    raw_output = ""
    model_call_count = 0
    model_inference_ms = 0
    session = get_or_create_session(request.session_id, request.os)
    tried_steps = extract_tried_steps(request.message)
    add_message(session, "user", request.message)
    try:
        intent = detect_intent(request.message, session)
        if intent == "follow_up":
            message_for_analysis = build_contextual_prompt(request.message, request.os, session, tried_steps)
            mode = "contextual_model_response"
        elif intent == "smalltalk":
            message_for_analysis = build_smalltalk_prompt(request.message, request.os)
            mode = "smalltalk_model_response"
        elif intent == "out_of_scope":
            message_for_analysis = build_out_of_scope_prompt(request.message, request.os)
            mode = "out_of_scope_model_response"
        elif intent == "unclear":
            message_for_analysis = build_unclear_prompt(request.message, request.os)
            mode = "unclear_model_response"
        else:
            message_for_analysis = request.message
            mode = "initial_model_response"

        logger.info("mode=%s intent=%s model_used=true session_id=%s", mode, intent, session["session_id"])
        first_output, elapsed_ms = _call_model(message_for_analysis, request.os)
        model_call_count += 1
        model_inference_ms += elapsed_ms
        first_result = _validate_model_output(first_output, message_for_analysis, request.os)
        if first_result["ok"]:
            response = _with_metadata(first_result["response"], session["session_id"], mode, start_time, False, first_result["warnings"], model_call_count, model_inference_ms)
            _commit_success(session, request.message, request.os, response, tried_steps)
            return response

        logger.warning(
            "Model output failed validation; retrying once. reasons=%s raw_preview=%s",
            first_result["reasons"],
            first_output[:500],
        )
        retry_message = build_retry_prompt(message_for_analysis, request.os, first_output, first_result["reasons"])
        raw_output, elapsed_ms = _call_model(retry_message, request.os)
        model_call_count += 1
        model_inference_ms += elapsed_ms
        retry_result = _validate_model_output(raw_output, message_for_analysis, request.os)
        if retry_result["ok"]:
            response = _with_metadata(retry_result["response"], session["session_id"], "model_retry", start_time, True, retry_result["warnings"], model_call_count, model_inference_ms)
            _commit_success(session, request.message, request.os, response, tried_steps)
            return response

        logger.error("Model output failed validation after retry. Returning 502 without backend-generated response. reasons=%s", retry_result["reasons"])
        return _invalid_model_response(retry_result["error_type"], raw_output, retry_result["reasons"])
    except ModelConfigurationError as exc:
        logger.error(f"Model configuration error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ModelIntegrationError as exc:
        logger.error(f"Model integration error: {exc}")
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ModelServiceError as exc:
        raise HTTPException(status_code=502, detail="Modelden cevap alınamadı.") from exc


@app.get("/sessions")
def sessions() -> list[dict]:
    return list_sessions()


@app.get("/sessions/{session_id}")
def session_detail(session_id: str) -> dict:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/sessions/{session_id}")
def remove_session(session_id: str) -> dict:
    if not delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True, "session_id": session_id}


def _validate_model_output(raw_output: str, message: str, os: str) -> dict[str, Any]:
    try:
        stripped = raw_output.strip()
        if not stripped.startswith("{") or not stripped.endswith("}"):
            return {"ok": False, "error_type": "invalid_model_json", "reasons": ["model returned content outside JSON"]}
        parsed_output = extract_json(raw_output)
        parsed_output = normalize_model_output(parsed_output, message, os)
        response = ITSupportResponse.model_validate(parsed_output)
        issues = collect_validation_issues(response.model_dump(), message, os)
        if issues["blocking_errors"]:
            return {"ok": False, "error_type": "invalid_model_semantics", "reasons": issues["blocking_errors"], "warnings": issues["advisory_warnings"]}
        if issues["advisory_warnings"]:
            logger.warning("Model output has advisory warnings: %s", issues["advisory_warnings"])
        return {"ok": True, "response": response, "reasons": [], "warnings": issues["advisory_warnings"], "error_type": ""}
    except JSONExtractionError:
        return {"ok": False, "error_type": "invalid_model_json", "reasons": ["model returned invalid JSON"]}
    except ValidationError as exc:
        return {"ok": False, "error_type": "invalid_model_semantics", "reasons": [f"schema validation failed: {err['loc']}: {err['msg']}" for err in exc.errors()]}


def _call_model(message: str, os: str) -> tuple[str, int]:
    started = time.time()
    output = analyze_message(message, os)
    return output, int((time.time() - started) * 1000)


def _invalid_model_response(error_type: str, raw_output: str, reasons: list[str]) -> JSONResponse:
    raw_preview = raw_output[:1500]
    detail = "Model returned invalid JSON" if error_type == "invalid_model_json" else "Model output failed semantic validation"
    return JSONResponse(
        status_code=502,
        content={
            "detail": detail,
            "error_type": error_type,
            "raw_preview": raw_preview,
            "reasons": reasons,
        },
    )


def _with_metadata(response: ITSupportResponse, session_id: str, mode: str, start_time: float, retry_used: bool, warnings: list[str], model_call_count: int, model_inference_ms: int) -> ITSupportResponse:
    if model_call_count < 1:
        raise RuntimeError("successful response attempted without model call")
    response.session_id = session_id
    response.mode = mode
    response.latency_ms = int((time.time() - start_time) * 1000)
    response.model_used = True
    response.repair_used = False
    response.retry_used = retry_used
    response.model_call_count = model_call_count
    response.model_inference_ms = model_inference_ms
    response.advisory_warnings = warnings or None
    logger.info("mode=%s model_used=true repair_used=false retry_used=%s model_call_count=%s model_inference_ms=%s latency_ms=%s", mode, retry_used, model_call_count, model_inference_ms, response.latency_ms)
    return response


def _commit_success(session: dict, message: str, os: str, response: ITSupportResponse, tried_steps: list[str]) -> None:
    analysis = response.model_dump(exclude_none=True)
    add_message(session, "assistant", response.summary, analysis)
    update_active_issue(session, message, os, analysis, tried_steps)

