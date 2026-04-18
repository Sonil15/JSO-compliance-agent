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


def main() -> None:
    """Main Streamlit application entry point."""
    st.title("JSO Licensing Governance Dashboard")
    st.write(
        "This dashboard monitors recruiter license usage and detects compliance violations "
        "using a **Hybrid AI Agent System** combining rule-based compliance checks with LLM-powered reasoning."
    )
    
    # Display API key status
    api_key_configured = False
    try:
        api_key_configured = bool(st.secrets.get("GROQ_API_KEY"))
    except:
        api_key_configured = bool(os.getenv("GROQ_API_KEY"))
    
    api_key_status = "✅ Connected" if api_key_configured else "⚠️ Not configured (using rule-based mode only)"
    st.caption(f"AI Agent Status: {api_key_status}")
    
    # Render input form and get metrics
    render_input_form()
    
    # Display results if analysis has been run
    if 'analysis_result' in st.session_state:
        render_results(st.session_state['analysis_result'])


def render_input_form() -> bool:
    """
    Render input widgets and collect recruiter metrics.
    
    Returns:
        bool: True if the "Run Compliance Analysis" button was clicked, False otherwise
    """
    st.subheader("Enter Recruiter Metrics")
    
    # Mock data loading section
    st.write("**Load Mock Data (Optional)**")
    mock_recruiters = generate_mock_recruiters()
    mock_options = ["-- Select a mock recruiter --"] + [r.license_id for r in mock_recruiters]
    
    selected_mock = st.selectbox(
        "Choose a mock recruiter to load",
        options=mock_options,
        help="Select a pre-configured recruiter example to populate the form"
    )
    
    # Initialize default values
    default_license_id = ""
    default_applications = 0
    default_duplicates = 0
    default_response_rate = 50.0
    default_ips = 1
    
    # Load mock data if selected
    if selected_mock != "-- Select a mock recruiter --":
        mock_recruiter = get_recruiter_by_id(selected_mock)
        if mock_recruiter:
            default_license_id = mock_recruiter.license_id
            default_applications = mock_recruiter.applications_sent_today
            default_duplicates = mock_recruiter.duplicate_cvs
            default_response_rate = mock_recruiter.employer_response_rate
            default_ips = mock_recruiter.ip_addresses_used
    
    st.write("---")
    
    # Input widgets for all five metrics
    license_id = st.text_input(
        "License ID",
        value=default_license_id,
        placeholder="e.g., REC-001",
        help="Unique identifier for the recruiter"
    )
    
    applications_sent_today = st.number_input(
        "Applications sent today",
        min_value=0,
        value=default_applications,
        step=1,
        help="Number of job applications submitted today"
    )
    
    duplicate_cvs = st.number_input(
        "Duplicate CVs",
        min_value=0,
        value=default_duplicates,
        step=1,
        help="Number of duplicate CV submissions detected"
    )
    
    employer_response_rate = st.slider(
        "Employer response rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=default_response_rate,
        step=0.1,
        help="Percentage of employers who responded to applications"
    )
    
    ip_addresses_used = st.number_input(
        "IP addresses used",
        min_value=1,
        value=default_ips,
        step=1,
        help="Number of different IP addresses used for access"
    )
    
    # Run analysis button
    if st.button("Run Compliance Analysis"):
        # Validate license_id is not empty
        if not license_id or not license_id.strip():
            st.error("Please enter a License ID before running analysis.")
            return False
        
        # Create RecruiterMetrics object from inputs
        try:
            metrics = RecruiterMetrics(
                license_id=license_id.strip(),
                applications_sent_today=int(applications_sent_today),
                duplicate_cvs=int(duplicate_cvs),
                employer_response_rate=float(employer_response_rate),
                ip_addresses_used=int(ip_addresses_used)
            )
            
            # Layer 1 only here — LLM runs inside st.fragment so rule-based UI appears immediately
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
    st.subheader("Compliance Analysis Results")
    
    # Display compliance score with color-coded styling based on risk level
    if result.risk_level == RiskLevel.SAFE:
        st.success(f"✅ SAFE - Compliance Score: {result.compliance_score}/100")
    elif result.risk_level == RiskLevel.WARNING:
        st.warning(f"⚠️ WARNING - Compliance Score: {result.compliance_score}/100")
    else:  # HIGH_RISK
        st.error(f"🚨 HIGH RISK - Compliance Score: {result.compliance_score}/100")
    
    # Display rule-based report
    st.subheader("Rule-Based Compliance Report")
    st.write(result.report)
    
    # Display recommendations from rule engine
    if result.recommendations:
        st.subheader("Rule Engine Recommendations")
        for recommendation in result.recommendations:
            st.write(f"• {recommendation}")
    
    activity_data = st.session_state.get("activity_data") or _activity_data_from_metrics(result.metrics)
    render_ai_analysis_fragment(activity_data, result)


@st.fragment(run_every=timedelta(seconds=0.5))
def render_ai_analysis_fragment(activity_data: dict, result: ComplianceResult) -> None:
    """
    AI layer runs in a fragment: rule-based sections above render first; Groq runs in a worker
    thread and the fragment polls on the main thread until the future completes.
    """
    st.markdown("---")
    st.subheader("🤖 AI Compliance Agent Analysis")

    if result.risk_level == RiskLevel.SAFE:
        st.info(AI_SKIPPED_SAFE_MESSAGE)
        return

    _consume_ai_future_if_done()

    if not st.session_state.get("ai_llm_complete"):
        if "ai_future" not in st.session_state:
            st.session_state.ai_future = _AI_EXECUTOR.submit(_run_llm, activity_data, result)
        _consume_ai_future_if_done()

        if not st.session_state.get("ai_llm_complete"):
            with st.spinner("Generating AI compliance analysis…"):
                st.caption(
                    "Rule-based results above are ready. AI analysis loads here when complete "
                    "(runs in the background)."
                )
            return

    ai_report = st.session_state.get("ai_report")

    if ai_report is None:
        st.warning(
            "⚠️ AI Agent not configured. Set GROQ_API_KEY environment variable to enable AI-powered analysis.\n\n"
            "Example: `export GROQ_API_KEY=your_key_here`"
        )
    elif ai_report.startswith("AI Agent Error:"):
        st.error(ai_report)
    elif ai_report == AI_SKIPPED_SAFE_MESSAGE:
        st.info(ai_report)
    else:
        st.markdown(ai_report)
        st.caption("*Generated by Groq LLM (llama-3.3-70b-versatile)*")


if __name__ == "__main__":
    main()
