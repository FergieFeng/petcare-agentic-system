import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.jd_analysis import JDAnalysisError, run_jd_analysis

SAMPLE_INPUT_PATH = ROOT / "docs" / "agent_specs" / "jd_analysis" / "fixtures" / "sample_input.json"


def _load_sample_jd() -> str:
    data = json.loads(SAMPLE_INPUT_PATH.read_text(encoding="utf-8"))
    return data.get("job_description", "")


st.set_page_config(page_title="JD Analysis Tester", page_icon=":mag:", layout="wide")
st.title("JD Analysis Agent Tester")
st.caption("Paste a job description, run extraction, and inspect structured JSON output.")

with st.sidebar:
    st.subheader("Quick Actions")
    if st.button("Load Sample JD"):
        st.session_state["jd_text"] = _load_sample_jd()
    st.markdown(
        "- Fill `.env` with `OPENAI_API_KEY`\n"
        "- Install deps: `pip install -r requirements.txt`\n"
        "- Run: `streamlit run src/ui/app.py`"
    )

jd_text = st.text_area(
    "Job Description Input",
    value=st.session_state.get("jd_text", ""),
    height=300,
    placeholder="Paste plain-text JD here...",
)

run_clicked = st.button("Run JD Analysis", type="primary")
if run_clicked:
    with st.spinner("Running JD Analysis..."):
        try:
            result = run_jd_analysis(jd_text)
            st.success("Analysis complete.")
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("Structured JSON")
                st.json(result)
            with col2:
                st.subheader("Warnings")
                warnings = result.get("warnings", [])
                if warnings:
                    for w in warnings:
                        st.warning(w)
                else:
                    st.info("No warnings.")
        except JDAnalysisError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")
