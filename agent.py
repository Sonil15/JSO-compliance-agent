"""
AI Compliance Agent for JSO Compliance Sentinel.

This module implements the AI reasoning layer using Groq LLM to provide
intelligent compliance analysis and governance recommendations.
"""

import os
from typing import Optional
from groq import Groq
from models import ComplianceResult, RiskLevel

# Shown when the rule engine is SAFE — returned instead of calling the LLM (see analyze_recruiter_behavior).
AI_SKIPPED_SAFE_MESSAGE = (
    "**AI Compliance Agent analysis not run**\n\n"
    "The rule-based engine classified this recruiter as **SAFE**. "
    "LLM reasoning runs only for WARNING or HIGH_RISK classifications."
)

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def analyze_recruiter_behavior(
    activity_data: dict,
    rule_results: ComplianceResult
) -> Optional[str]:
    """
    Analyze recruiter behavior using Groq LLM AI agent.
    
    This function sends structured compliance data to a Groq LLM acting as
    an AI governance agent to provide intelligent behavioral interpretation,
    risk assessment, and governance recommendations.
    
    Args:
        activity_data: Dictionary containing recruiter activity metrics
        rule_results: ComplianceResult from the rule-based engine
        
    Returns:
        AI-generated compliance report string; ``AI_SKIPPED_SAFE_MESSAGE`` when risk is SAFE
        (LLM not invoked); or None if API key is missing (non-SAFE cases only).
    """
    if rule_results.risk_level == RiskLevel.SAFE:
        return AI_SKIPPED_SAFE_MESSAGE

    # Check for API key (supports both env var and Streamlit secrets)
    api_key = None
    
    # Try Streamlit secrets first (for cloud deployment)
    if HAS_STREAMLIT:
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
        except:
            pass
    
    # Fall back to environment variable (for local development)
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        return None
    
    try:
        # Initialize Groq client
        client = Groq(api_key=api_key)
        
        recommendations_block = _format_recommendations(rule_results.recommendations)
        rule_report_block = _format_rule_report(rule_results.report)

        # Construct structured prompt for the AI agent (two-phase reasoning + reconciliation)
        prompt = f"""You are an AI governance agent for a recruitment platform monitoring recruiter compliance and licensing standards.

CONTEXT FOR OPERATORS (JSO-aligned):
- Transparency & auditability: your output may be reviewed by stakeholders; cite concrete metrics and engine outputs when you conclude.
- Fairness: weigh impacts on HR consultants/recruiters and platform quality without inventing facts.
- Privacy: treat candidate-related data as sensitive — do not infer CV text, transcripts, or personal identifiers beyond fields in this prompt; use only aggregate metrics provided for authorized licensing/compliance review.

ANTI-HALLUCINATION:
- Refer only to metrics and engine outputs present below. If something is not provided, say "unknown / not provided".
- Do not infer license terms, contractual thresholds, or internal JSO policy not stated here. You may mention generic recruitment governance practices only when labeled clearly as general practice, not as JSO policy.

INPUT DATA

RECRUITER ACTIVITY METRICS (use these alone for Phase A):
- License ID: {activity_data['license_id']}
- Applications sent today: {activity_data['applications_sent_today']}
- Duplicate CV submissions: {activity_data['duplicate_cvs']}
- Employer response rate: {activity_data['employer_response_rate']}%
- IP addresses used: {activity_data['ip_addresses_used']}

RULE ENGINE FINDINGS (use starting in Phase B — do not lean on these in INDEPENDENT BEHAVIOR & RISK VIEW):
- Compliance Score: {rule_results.compliance_score}/100
- Risk Level: {rule_results.risk_level.value}
- Violations Detected: {len(rule_results.violations)}
{_format_violations(rule_results.violations)}

RULE ENGINE REPORT (rule-based narrative):
{rule_report_block}

RULE ENGINE RECOMMENDATIONS (deterministic bullets):
{recommendations_block}

REASONING PROCESS (two phases; reflect this in your sections):
Phase A — Independent assessment: In section 1 ONLY, interpret patterns, suspected drivers, and your prioritized actions using ONLY RECRUITER ACTIVITY METRICS. Do not reference compliance score, risk level, violations, the rule report, or rule recommendations in that section's reasoning.
Phase B — Reconciliation: In subsequent sections, incorporate rule engine outputs. Explicitly compare your independent priorities with rule recommendations (pair specific rule lines to specific independent actions where possible). State agree, partially agree, or conflict.

RESOLUTION POLICY (state this in ALIGNMENT & CONFLICTS):
- Rule engine outputs are authoritative for enforcement thresholds and scored compliance in this system.
- Your role includes narrative, investigation focus, and flagging tensions; where they conflict, operators should enforce per rule engine but may use your analysis to decide what to verify first.

OUTPUT — structured compliance intelligence report with these sections (use clear headings; bullets encouraged; about 350–550 words total):

1. INDEPENDENT BEHAVIOR & RISK VIEW — From metrics only: key signals, severity, rationale, prioritized actions (Phase A).

2. RULE ENGINE SUMMARY — Neutral restatement of score, risk, violations, the rule report, and numbered/bulleted rule recommendations (Phase B).

3. ALIGNMENT & CONFLICTS — Bullet lists:
   - Agreement: where metrics and rule conclusions match your reasoning.
   - Conflict or tension: where risk/score/recommendations diverge from metric-driven judgment or priorities differ across recommendations.
   - Resolution guidance: apply the resolution policy above so the outcome is auditable.

4. GOVERNANCE & OPERATOR ACTIONS — Consolidated actions for platform administrators (tie-break: enforcement follows rule engine; sequencing/investigation informed by independent view).

5. AUDIT NOTES — What requires human verification, extra data, or follow-up monitoring."""

        # Call Groq LLM
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert licensing governance analyst for recruitment platforms: "
                        "platform quality, auditable compliance reasoning, and clear reconciliation between "
                        "deterministic rule engines and independent metric-based assessment. "
                        "Prioritize fairness toward consultants and privacy around sensitive candidate-related data "
                        "(no invented personal or document content; use only data supplied in the user message for analysis)."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            # model="llama-3.3-70b-versatile",
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=1200,
        )
        
        # Extract and return the AI response
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        # Return error message if API call fails
        return f"AI Agent Error: {str(e)}"


def _format_violations(violations: list) -> str:
    """Format violations list for the LLM prompt."""
    if not violations:
        return "  - No violations detected"
    
    formatted = []
    for v in violations:
        formatted.append(f"  - {v.description} (Penalty: {v.penalty_points} points)")
    
    return "\n".join(formatted)


def _format_recommendations(recommendations: list[str]) -> str:
    """Format rule engine recommendations as a numbered list for the LLM prompt."""
    if not recommendations:
        return "  (none)"
    lines = []
    for i, rec in enumerate(recommendations, start=1):
        lines.append(f"  {i}. {rec}")
    return "\n".join(lines)


def _format_rule_report(report: str) -> str:
    """Indent rule-based narrative report for clarity inside the prompt."""
    text = (report or "").strip()
    if not text:
        return "  (empty)"
    return "\n".join(f"  {line}" for line in text.splitlines())
