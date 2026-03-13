"""
AI Compliance Agent for JSO Compliance Sentinel.

This module implements the AI reasoning layer using Groq LLM to provide
intelligent compliance analysis and governance recommendations.
"""

import os
from typing import Optional
from groq import Groq
from models import ComplianceResult

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
        AI-generated compliance report string, or None if API key is missing
    """
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
        
        # Construct structured prompt for the AI agent
        prompt = f"""You are an AI governance agent for a recruitment platform monitoring recruiter compliance and licensing standards.

Analyze the following recruiter behavior and provide governance insights:

RECRUITER ACTIVITY METRICS:
- License ID: {activity_data['license_id']}
- Applications sent today: {activity_data['applications_sent_today']}
- Duplicate CV submissions: {activity_data['duplicate_cvs']}
- Employer response rate: {activity_data['employer_response_rate']}%
- IP addresses used: {activity_data['ip_addresses_used']}

RULE ENGINE FINDINGS:
- Compliance Score: {rule_results.compliance_score}/100
- Risk Level: {rule_results.risk_level.value}
- Violations Detected: {len(rule_results.violations)}
{_format_violations(rule_results.violations)}

Provide a structured compliance intelligence report with these sections:

1. BEHAVIOR SUMMARY: Brief interpretation of the recruiter's activity patterns
2. RISK ASSESSMENT: Explain the compliance risks and their implications
3. DETECTED GOVERNANCE ISSUES: Key concerns from a governance perspective
4. RECOMMENDED ACTIONS: Specific actions for platform administrators

Keep the response concise (approximately 150 words total). Be direct and actionable."""

        # Call Groq LLM
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert AI compliance agent specializing in recruitment platform governance and licensing standards."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=400
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
