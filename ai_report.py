"""
AI Report Generator for JSO Compliance Sentinel.

This module generates human-readable compliance reports with violation
descriptions and risk level assessments.
"""

from models import ComplianceResult, RiskLevel


def generate_report(result: ComplianceResult) -> str:
    """
    Generate human-readable compliance report.
    
    Args:
        result: ComplianceResult object containing analysis data
        
    Returns:
        Non-empty string containing formatted compliance report
        
    Requirements: 6.1, 6.2
    """
    report_lines = [
        "Compliance Report",
        f"License ID: {result.metrics.license_id}",
        f"Compliance Score: {result.compliance_score}",
        f"Risk Level: {result.risk_level.value}",
        ""
    ]
    
    if result.violations:
        report_lines.append("Detected Issues:")
        for violation in result.violations:
            report_lines.append(f"- {violation.description}")
    else:
        report_lines.append("No compliance issues detected.")
    
    return "\n".join(report_lines)


def generate_recommendations(result: ComplianceResult) -> list[str]:
    """
    Generate actionable recommendations based on violations and risk level.
    
    Args:
        result: ComplianceResult object containing analysis data
        
    Returns:
        List of actionable recommendation strings. At least one recommendation
        when violations exist.
        
    Requirements: 6.3, 6.4, 6.5, 6.6
    """
    recommendations = []
    
    # Generate specific recommendations based on violations
    violation_rules = {v.rule_id for v in result.violations}
    
    if "RULE_1" in violation_rules:
        # High application volume
        if result.risk_level == RiskLevel.HIGH_RISK:
            recommendations.append("URGENT: Immediately reduce application volume to below 50 per day")
        elif result.risk_level == RiskLevel.WARNING:
            recommendations.append("Monitor and reduce application volume to below 50 per day")
        else:
            recommendations.append("Review application volume trends to maintain compliance")
    
    if "RULE_2" in violation_rules:
        # Duplicate CVs
        if result.risk_level == RiskLevel.HIGH_RISK:
            recommendations.append("URGENT: Implement duplicate CV detection system immediately")
        elif result.risk_level == RiskLevel.WARNING:
            recommendations.append("Review CV submission process to prevent duplicates")
        else:
            recommendations.append("Audit recent CV submissions for duplicates")
    
    if "RULE_3" in violation_rules:
        # Low employer response rate
        if result.risk_level == RiskLevel.HIGH_RISK:
            recommendations.append("URGENT: Review and improve candidate quality - employer response rate critically low")
        elif result.risk_level == RiskLevel.WARNING:
            recommendations.append("Improve candidate screening to increase employer response rate above 5%")
        else:
            recommendations.append("Monitor employer response rate trends")
    
    if "RULE_4" in violation_rules:
        # Possible license sharing
        if result.risk_level == RiskLevel.HIGH_RISK:
            recommendations.append("URGENT: Investigate potential license sharing - multiple IP addresses detected")
        elif result.risk_level == RiskLevel.WARNING:
            recommendations.append("Review account access patterns for unusual IP address usage")
        else:
            recommendations.append("Monitor IP address usage for security compliance")
    
    # Add general recommendations based on risk level
    if result.risk_level == RiskLevel.HIGH_RISK and result.violations:
        recommendations.append("Schedule immediate compliance review meeting")
        recommendations.append("Consider temporary license suspension pending investigation")
    elif result.risk_level == RiskLevel.WARNING and result.violations:
        recommendations.append("Schedule compliance review within 48 hours")
    elif result.risk_level == RiskLevel.SAFE and not result.violations:
        # Positive reinforcement for safe status with no violations
        recommendations.append("Excellent compliance record - continue current practices")
        recommendations.append("Maintain regular monitoring of key metrics")
    elif result.risk_level == RiskLevel.SAFE and result.violations:
        # Safe but has violations (edge case)
        recommendations.append("Address minor compliance issues to maintain safe status")
    
    return recommendations
