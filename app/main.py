"""
FastAPI wrapper for the Startup Validation Pipeline.
GET  /            → demo frontend (static HTML)
POST /validate    → run validation, return report JSON
POST /validate/pdf → run validation, return PDF report
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from app.pipeline import run_pipeline
from app.render import markdown_to_pdf

app = FastAPI(title="Startup Validation Agent", version="0.2.0")

INDEX_HTML = (Path(__file__).parent / "templates" / "index.html").read_text()


class ValidateRequest(BaseModel):
    idea: str


class ValidateResponse(BaseModel):
    markdown: str
    score: int
    verdict: str = ""
    evaluation_reasoning: str = ""
    unresolved_claims_stripped: int = 0
    error: str | None = None


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(INDEX_HTML)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


@app.post("/validate", response_model=ValidateResponse)
async def validate(req: ValidateRequest):
    if not req.idea.strip():
        raise HTTPException(status_code=400, detail="Idea text is required")
    try:
        result = await run_pipeline(req.idea.strip())
        ev = result.get("evaluation")
        return ValidateResponse(
            markdown=result.get("markdown", ""),
            score=round(ev.overall_score) if ev else 0,
            verdict=ev.recommendation.verdict if ev else "insufficient-info",
            evaluation_reasoning=ev.reasoning if ev else "",
            unresolved_claims_stripped=result.get("unresolved_claims_stripped", 0),
            error=result.get("error"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate/pdf")
async def validate_pdf(req: ValidateRequest):
    if not req.idea.strip():
        raise HTTPException(status_code=400, detail="Idea text is required")
    try:
        result = await run_pipeline(req.idea.strip())
        md = result.get("markdown", "")
        if not md:
            raise HTTPException(status_code=500, detail="No report generated")
        pdf_bytes = markdown_to_pdf(md)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline; filename=validation-report.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
