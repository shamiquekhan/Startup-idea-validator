import asyncio
import streamlit as st
from app.pipeline import run_pipeline

st.set_page_config(
    page_title="Startup Validation Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #666;
        margin-bottom: 2rem;
    }
    .score-badge {
        display: inline-block;
        font-size: 2.5rem;
        font-weight: 700;
        padding: 0.5rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .score-high { background: #dcfce7; color: #166534; }
    .score-medium { background: #fef9c3; color: #854d0e; }
    .score-low { background: #fee2e2; color: #991b1b; }
    .verdict-badge {
        display: inline-block;
        font-size: 1rem;
        font-weight: 600;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        margin: 0.5rem 0;
    }
    .verdict-build { background: #dcfce7; color: #166534; }
    .verdict-narrow { background: #fef9c3; color: #854d0e; }
    .verdict-pivot { background: #ffedd5; color: #9a3412; }
    .verdict-abandon { background: #fee2e2; color: #991b1b; }
    .verdict-insufficient-info { background: #f3f4f6; color: #4b5563; }
    .reasoning-box { background: #f9fafb; padding: 1rem; border-radius: 8px; margin: 0.75rem 0; border-left: 4px solid #2563eb; }
    .kill-box { background: #fef2f2; padding: 1rem; border-radius: 8px; margin: 0.75rem 0; border-left: 4px solid #dc2626; }
    .steps-box { background: #f0fdf4; padding: 1rem; border-radius: 8px; margin: 0.75rem 0; border-left: 4px solid #16a34a; }
    .input-note { background: #fef9c3; padding: 0.75rem; border-radius: 6px; font-size: 0.9rem; margin: 0.5rem 0; }
    .stripped-note {
        margin-top: 1rem; padding: 0.75rem; background: #fef3c7; border-radius: 6px; font-size: 0.9rem;
    }
    .stTextArea textarea {
        font-family: inherit;
        min-height: 120px;
    }
    .stButton>button {
        background: #2563eb;
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
    }
    .stButton>button:hover {
        background: #1d4ed8;
    }
    .stButton>button:disabled {
        background: #93c5fd;
    }
</style>
""", unsafe_allow_html=True)

def render_report(markdown: str, score: int, verdict: str, reasoning: str, unresolved_claims_stripped: int):
    col1, col2 = st.columns([1, 3])
    
    score_class = "score-high" if score >= 60 else "score-medium" if score >= 35 else "score-low"
    verdict_classes = {
        "build": "verdict-build",
        "narrow": "verdict-narrow",
        "pivot": "verdict-pivot",
        "abandon": "verdict-abandon",
        "insufficient-info": "verdict-insufficient-info",
    }
    v_class = verdict_classes.get(verdict, "verdict-insufficient-info")
    verdict_label = verdict.replace("-", " ").replace("_", " ").title()
    if verdict == "insufficient-info":
        verdict_label = "Insufficient Info — Provide More Details"

    with col1:
        st.markdown(f'<div class="score-badge {score_class}">{score}/100</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="verdict-badge {v_class}">{verdict_label}</div>', unsafe_allow_html=True)

    if reasoning:
        st.markdown(f'<div class="reasoning-box"><strong>Assessment:</strong> {reasoning}</div>', unsafe_allow_html=True)

    if unresolved_claims_stripped > 0:
        st.markdown(
            f'<div class="stripped-note">⚠ {unresolved_claims_stripped} unsupported claim(s) were removed by the validator.</div>',
            unsafe_allow_html=True
        )

    st.divider()
    st.markdown(markdown.replace("# Startup Validation Report\n\n", ""))

async def run_validation(idea: str):
    return await run_pipeline(idea.strip())

def main():
    st.markdown('<div class="main-header">Startup Validation Agent</div>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Paste a startup idea and get a structured, source-cited evaluation across 8 dimensions — with a clear verdict and kill criteria.</p>', unsafe_allow_html=True)

    idea = st.text_area(
        "Startup Idea",
        placeholder="Describe your startup idea in detail. The more specific you are about customer, problem, and solution, the better the evaluation.\n\nExample: Small businesses waste hours manually tracking expenses across multiple bank accounts. I want to build an expense tracker that auto-categorizes transactions and generates reports. Target: freelancers and micro-businesses.",
        label_visibility="collapsed",
        key="idea_input",
    )

    if st.button("Validate Idea", disabled=not idea.strip(), type="primary"):
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        async def run_with_progress():
            progress_placeholder.info("🔍 Running research pipeline (30–90 seconds)...")
            result = await run_pipeline(idea.strip())
            return result

        with st.spinner("Running validation pipeline..."):
            try:
                result = asyncio.run(run_with_progress())
            except Exception as e:
                st.error(f"Error: {str(e)}")
                return

        progress_placeholder.empty()
        status_placeholder.empty()

        if result.get("error"):
            st.error(result["error"])
            if result.get("markdown"):
                st.markdown(result["markdown"])
            return

        score = round(result.get("evaluation", {}).overall_score) if result.get("evaluation") else 0
        verdict = result.get("evaluation", {}).recommendation.verdict if result.get("evaluation") else "insufficient-info"
        reasoning = result.get("evaluation", {}).reasoning if result.get("evaluation") else ""
        unresolved = result.get("unresolved_claims_stripped", 0)
        markdown = result.get("markdown", "")

        render_report(markdown, score, verdict, reasoning, unresolved)

    st.markdown("---")
    st.caption("Built with LangGraph • Streamlit • FastAPI")

if __name__ == "__main__":
    main()