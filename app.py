"""
Streamlit dashboard for JSO Compliance Sentinel.

This module provides the user interface for the compliance monitoring system,
allowing users to input recruiter metrics and view analysis results.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import streamlit as st
from models import RecruiterMetrics, ComplianceResult, RiskLevel
from compliance_engine import ComplianceEngine
from mock_data import generate_mock_recruiters, get_recruiter_by_id
from agent import analyze_recruiter_behavior, AI_SKIPPED_SAFE_MESSAGE

# Background LLM calls (fragment polls completion on the main thread — see render_ai_analysis_fragment).
_AI_EXECUTOR = ThreadPoolExecutor(max_workers=1)


def _groq_api_configured() -> bool:
    try:
        if bool(st.secrets.get("GROQ_API_KEY")):
            return True
    except Exception:
        pass
    return bool(os.getenv("GROQ_API_KEY"))


def _activity_data_from_metrics(metrics: RecruiterMetrics) -> dict:
    return {
        "license_id": metrics.license_id,
        "applications_sent_today": metrics.applications_sent_today,
        "duplicate_cvs": metrics.duplicate_cvs,
        "employer_response_rate": metrics.employer_response_rate,
        "ip_addresses_used": metrics.ip_addresses_used,
    }


def _run_llm(activity_data: dict, result: ComplianceResult):
    """Runs off-thread; result consumed on main thread in the fragment."""
    return analyze_recruiter_behavior(activity_data, result)


def _consume_ai_future_if_done() -> None:
    """Move a completed Future into session_state (must run on main thread)."""
    fut = st.session_state.get("ai_future")
    if fut is None or not fut.done():
        return
    try:
        st.session_state["ai_report"] = fut.result()
    except Exception as e:
        st.session_state["ai_report"] = f"AI Agent Error: {e}"
    st.session_state.pop("ai_future", None)
    st.session_state["ai_llm_complete"] = True


def _risk_meta(level: RiskLevel) -> tuple[str, str]:
    """Label and short description for risk level."""
    if level == RiskLevel.SAFE:
        return "SAFE", "Within policy thresholds"
    if level == RiskLevel.WARNING:
        return "WARNING", "Review recommended"
    return "HIGH RISK", "Immediate attention"


def _theme_css() -> None:
    """Green / black / white chrome; Orbitron via Google Fonts; complements config.toml."""
    st.markdown(
        """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    /* Default: readable system sans — inputs, outputs, metrics, labels */
    .stApp {
        background-color: #0b0f0b;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif !important;
    }
    input, textarea, select, option, button,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stAlert"] *,
    [data-testid="stAlertContainer"] *,
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stCaptionContainer"],
    [data-testid="stWidgetLabel"],
    [data-testid="stSelectbox"] *,
    [data-testid="stSlider"] *,
    label {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif !important;
    }
    /* Orbitron: headings / chrome only */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        font-family: "Orbitron", sans-serif !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #050806 0%, #0f160f 100%);
        border-right: 1px solid rgba(34, 197, 94, 0.22);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] span { color: #e8ece9; }
    hr { border-color: rgba(34, 197, 94, 0.28) !important; }
    .stMarkdown h1 { color: #f8faf8; letter-spacing: -0.02em; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(34, 197, 94, 0.35) !important;
    }
    /* Primary CTA — Run compliance analysis */
    button[kind="primary"],
    [data-testid="baseButton-primary"] {
        background-color: #22c55e !important;
        border: 1px solid #16a34a !important;
        color: #052e14 !important;
    }
    button[kind="primary"]:hover,
    [data-testid="baseButton-primary"]:hover {
        background-color: #16a34a !important;
        border-color: #15803d !important;
        color: #f8faf8 !important;
    }
</style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title="JSO Compliance Sentinel",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _theme_css()

    _render_sidebar()

    st.markdown("# Licensing governance")
    st.caption(
        "Track license usage. Flag risks. Act faster."
    )

    left, right = st.columns([1.05, 1.2], gap="large")

    with left:
        render_input_form()

    with right:
        if "analysis_result" in st.session_state:
            render_results(st.session_state["analysis_result"])
        else:
            with st.container(border=True):
                st.markdown("### Results")
                st.info(
                    "Enter metrics and click **Run compliance analysis** to see "
                    "the rule-based score, recommendations, and AI analysis (when applicable)."
                )


def _render_sidebar() -> None:
    api_ok = _groq_api_configured()
    with st.sidebar:
        st.markdown("### 🛡️ JSO Sentinel")
        st.caption("Recruiter licensing · compliance prototype")
        st.divider()
        if api_ok:
            st.success("Groq API key detected")
        else:
            st.warning(
                "No **GROQ_API_KEY** — Layer 2 will not run for WARNING / HIGH_RISK. "
                "Set it in `.env` or Streamlit secrets."
            )
        st.divider()
        st.markdown("**Flow**")
        st.markdown(
            """
1. **Layer 1** — Rules + score + risk band  
2. **Layer 2** — LLM only if not SAFE (async)  
3. **Alignment** — Independent view vs rule engine  
            """
        )
        st.divider()
        st.caption("Aggregate metrics only — no CV content sent to the model.")


def render_input_form() -> bool:
    """
    Render input widgets and collect recruiter metrics.

    Returns:
        bool: True if the "Run Compliance Analysis" button was clicked, False otherwise
    """
    with st.container(border=True):
        st.markdown("### Input")

        st.caption("Quick load · mock recruiter")
        mock_recruiters = generate_mock_recruiters()
        mock_options = ["— Select —"] + [r.license_id for r in mock_recruiters]
        selected_mock = st.selectbox(
            "Choose a mock recruiter",
            options=mock_options,
            help="Populate the form with a demo scenario",
        )

        default_license_id = ""
        default_applications = 0
        default_duplicates = 0
        default_response_rate = 50.0
        default_ips = 1

        if selected_mock != "— Select —":
            mock_recruiter = get_recruiter_by_id(selected_mock)
            if mock_recruiter:
                default_license_id = mock_recruiter.license_id
                default_applications = mock_recruiter.applications_sent_today
                default_duplicates = mock_recruiter.duplicate_cvs
                default_response_rate = mock_recruiter.employer_response_rate
                default_ips = mock_recruiter.ip_addresses_used

        license_id = st.text_input(
            "License ID",
            value=default_license_id,
            placeholder="e.g. REC-001",
            help="Unique recruiter / license identifier",
        )

        r1, r2 = st.columns(2)
        with r1:
            applications_sent_today = st.number_input(
                "Applications (today)",
                min_value=0,
                value=default_applications,
                step=1,
            )
        with r2:
            duplicate_cvs = st.number_input(
                "Duplicate CVs",
                min_value=0,
                value=default_duplicates,
                step=1,
            )

        employer_response_rate = st.slider(
            "Employer response rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=default_response_rate,
            step=0.1,
        )

        ip_addresses_used = st.number_input(
            "IP addresses used",
            min_value=1,
            value=default_ips,
            step=1,
            help="Distinct IPs associated with this license session",
        )

        run = st.button(
            "Run compliance analysis",
            type="primary",
            use_container_width=True,
        )

        if run:
            if not license_id or not license_id.strip():
                st.error("Enter a **License ID** before running.")
                return False

            try:
                metrics = RecruiterMetrics(
                    license_id=license_id.strip(),
                    applications_sent_today=int(applications_sent_today),
                    duplicate_cvs=int(duplicate_cvs),
                    employer_response_rate=float(employer_response_rate),
                    ip_addresses_used=int(ip_addresses_used),
                )

                st.session_state.pop("ai_future", None)
                st.session_state.pop("ai_llm_complete", None)

                engine = ComplianceEngine()
                result = engine.analyze(metrics)
                activity_data = _activity_data_from_metrics(metrics)

                st.session_state["analysis_result"] = result
                st.session_state["activity_data"] = activity_data

                if result.risk_level == RiskLevel.SAFE:
                    st.session_state["ai_report"] = AI_SKIPPED_SAFE_MESSAGE
                else:
                    st.session_state["ai_report"] = None

                st.toast("Rule engine finished — results updated on the right.", icon="✅")
                return True

            except ValueError as e:
                st.error(f"Invalid input: {e}")
                return False

    return False


def render_results(result: ComplianceResult) -> None:
    """
    Display compliance analysis results with color-coded indicators.

    Args:
        result: ComplianceResult object containing analysis output

    Requirements: 8.3, 8.4, 8.5, 8.6, 8.7, 8.8
    """
    label, hint = _risk_meta(result.risk_level)
    violation_count = len(result.violations)

    st.markdown("### Results")

    left_metrics, right_metrics = st.columns(2)
    with left_metrics:
        st.metric("Compliance score", f"{result.compliance_score}/100")
        st.metric("Rule violations", violation_count)
    with right_metrics:
        st.metric("Risk band", label)
        st.metric("Apps (today)", result.metrics.applications_sent_today)

    st.divider()

    if result.risk_level == RiskLevel.SAFE:
        st.success(f"**{label}** · {hint}")
    elif result.risk_level == RiskLevel.WARNING:
        st.warning(f"**{label}** · {hint}")
    else:
        st.error(f"**{label}** · {hint}")

    with st.container(border=True):
        st.markdown("#### Rule-based report")
        st.markdown(result.report.replace("\n", "\n\n"))

    if result.recommendations:
        with st.container(border=True):
            st.markdown("#### Rule engine recommendations")
            for recommendation in result.recommendations:
                st.markdown(f"- {recommendation}")

    activity_data = st.session_state.get("activity_data") or _activity_data_from_metrics(result.metrics)
    render_ai_analysis_fragment(activity_data, result)


@st.fragment(run_every=timedelta(seconds=0.5))
def render_ai_analysis_fragment(activity_data: dict, result: ComplianceResult) -> None:
    """
    AI layer runs in a fragment: rule-based sections above render first; Groq runs in a worker
    thread and the fragment polls on the main thread until the future completes.
    """
    st.divider()

    with st.container(border=True):
        st.markdown("#### AI compliance agent")
        st.caption("Groq · llama-3.3-70b — reconciliation & governance narrative")

        if result.risk_level == RiskLevel.SAFE:
            st.info(AI_SKIPPED_SAFE_MESSAGE)
            return

        _consume_ai_future_if_done()

        if not st.session_state.get("ai_llm_complete"):
            if "ai_future" not in st.session_state:
                st.session_state.ai_future = _AI_EXECUTOR.submit(_run_llm, activity_data, result)
            _consume_ai_future_if_done()

            if not st.session_state.get("ai_llm_complete"):
                with st.spinner("Generating AI analysis…"):
                    st.markdown(
                        "Rule-based results are ready above. "
                        "**AI analysis** loads here when the model finishes (runs in the background)."
                    )
                return

        ai_report = st.session_state.get("ai_report")

        if ai_report is None:
            st.warning(
                "**AI layer unavailable** — set `GROQ_API_KEY` (environment or Streamlit secrets) "
                "to enable LLM analysis for WARNING / HIGH_RISK.\n\n"
                "`export GROQ_API_KEY=your_key`"
            )
        elif ai_report.startswith("AI Agent Error:"):
            st.error(ai_report)
        elif ai_report == AI_SKIPPED_SAFE_MESSAGE:
            st.info(ai_report)
        else:
            st.markdown(ai_report)


if __name__ == "__main__":
    main()
