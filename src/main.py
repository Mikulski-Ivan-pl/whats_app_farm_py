import logging
import time

from fastapi import FastAPI, HTTPException

from llm import get_reply, summarize
from schemas import ReplyRequest, ReplyResponse, SummarizeRequest, SummarizeResponse, ToolCall

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

_SLOW_THRESHOLD_SEC = 10

app = FastAPI(title="LLM Service")


@app.post("/reply", response_model=ReplyResponse)
def reply(body: ReplyRequest):
    logger.info(
        "reply request phone=%s messages=%d has_summary=%s model=%s tools=%d",
        body.phone,
        len(body.messages),
        bool(body.summary),
        body.model or "auto",
        len(body.tools),
    )
    t0 = time.monotonic()
    try:
        text, tool_calls = get_reply(
            [m.model_dump() for m in body.messages],
            body.summary,
            body.system_prompt,
            body.model,
            [t.model_dump() for t in body.tools] or None,
            [tc.model_dump() for tc in body.previous_tool_calls] or None,
            [tr.model_dump() for tr in body.tool_results] or None,
        )
        elapsed = time.monotonic() - t0
        log = logger.warning if elapsed >= _SLOW_THRESHOLD_SEC else logger.info
        if tool_calls:
            log("reply tool_calls phone=%s count=%d duration=%.1fs", body.phone, len(tool_calls), elapsed)
            return ReplyResponse(tool_calls=[ToolCall(**tc) for tc in tool_calls])
        log("reply ok phone=%s reply_len=%d duration=%.1fs", body.phone, len(text), elapsed)
        return ReplyResponse(reply=text)
    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.error("reply failed phone=%s duration=%.1fs err=%s", body.phone, elapsed, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize", response_model=SummarizeResponse)
def summarize_endpoint(body: SummarizeRequest):
    logger.info(
        "summarize request phone=%s messages=%d model=%s",
        body.phone,
        len(body.messages),
        body.model or "auto",
    )
    t0 = time.monotonic()
    try:
        text = summarize([m.model_dump() for m in body.messages], body.previous_summary, body.model)
        elapsed = time.monotonic() - t0
        log = logger.warning if elapsed >= _SLOW_THRESHOLD_SEC else logger.info
        log("summarize ok phone=%s summary_len=%d duration=%.1fs", body.phone, len(text), elapsed)
        return SummarizeResponse(summary=text)
    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.error("summarize failed phone=%s duration=%.1fs err=%s", body.phone, elapsed, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
