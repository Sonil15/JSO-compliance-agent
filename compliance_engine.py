"""
Compliance Engine for JSO Compliance Sentinel.

This module implements the core compliance analysis logic:
- Rule evaluation against recruiter metrics
- Compliance score calculation
- Risk level classification
- Coordination of analysis workflow
"""

from models import RecruiterMetrics, Violation, RiskLevel, ComplianceResult


class ComplianceEngine:
    """
    Core engine for evaluating compliance rules and analyzing recruiter metrics.
    
    The ComplianceEngine evaluates four compliance rules:
    - RULE_1: High application volume (> 50 applications/day)
    - RULE_2: Duplicate CV submissions (> 5 duplicates)
    - RULE_3: Low employer response rate (< 5.0%)
    - RULE_4: Possible license sharing (> 3 IP addresses)
    """
    
    def evaluate_rules(self, metrics: RecruiterMetrics) -> list[Violation]:
        """
        Evaluate all compliance rules against recruiter metrics.
        
        Args:
            metrics: RecruiterMetrics object containing recruiter activity data
            
        Returns:
            List of Violation objects for rules that were breached (may be empty)
            
        Preconditions:
            - metrics is a valid RecruiterMetrics object
            - All metric values are within valid ranges
            
        Postconditions:
            - Returns list of Violation objects (may be empty)
            - Each violation has valid rule_id, description, and penalty_points
            - No duplicate violations for same rule
            - No mutations to input metrics
        """
        violations = []
        
        # Rule 1: High application volume
        # Validates: Requirements 2.1
        if metrics.applications_sent_today > 50:
            violations.append(Violation(
                rule_id="RULE_1",
                description="High application volume detected",
                penalty_points=20
            ))
        
        # Rule 2: Duplicate CV submissions
        # Validates: Requirements 2.2
        if metrics.duplicate_cvs > 5:
            violations.append(Violation(
                rule_id="RULE_2",
                description="Duplicate CV submissions detected",
                penalty_points=30
            ))
        
        # Rule 3: Low employer response rate
        # Validates: Requirements 2.3
        if metrics.employer_response_rate < 5.0:
            violations.append(Violation(
                rule_id="RULE_3",
                description="Very low employer response rate",
                penalty_points=25
            ))
        
        # Rule 4: Possible license sharing
        # Validates: Requirements 2.4
        if metrics.ip_addresses_used > 3:
            violations.append(Violation(
                rule_id="RULE_4",
                description="Possible license sharing detected",
                penalty_points=25
            ))
        
        return violations


    def calculate_score(self, violations: list[Violation]) -> int:
        """
        Calculate compliance score starting at 100 and applying deductions.

        Args:
            violations: List of Violation objects with penalty points

        Returns:
            Integer compliance score between 0 and 100 (inclusive)

        Preconditions:
            - violations is a valid list (may be empty)
            - Each violation has valid penalty_points (positive integer)

        Postconditions:
            - Returns integer between 0 and 100 (inclusive)
            - Score = 100 - sum(violation.penalty_points for all violations)
            - Score is clamped to [0, 100] range
            - If violations is empty, returns 100
        """
        base_score = 100
        total_deductions = 0

        # Sum all penalty points
        for violation in violations:
            total_deductions += violation.penalty_points

        # Calculate final score and clamp to [0, 100]
        score = base_score - total_deductions
        score = max(0, min(100, score))

        return score

    def classify_risk(self, score: int) -> RiskLevel:
        """
        Classify risk level based on compliance score thresholds.

        Args:
            score: Integer compliance score between 0 and 100

        Returns:
            RiskLevel enum value (SAFE, WARNING, or HIGH_RISK)

        Preconditions:
            - score is integer in [0, 100]

        Postconditions:
            - Returns valid RiskLevel enum
            - score >= 80 → RiskLevel.SAFE
            - 50 <= score < 80 → RiskLevel.WARNING
            - score < 50 → RiskLevel.HIGH_RISK
            - Classification is deterministic (same score always returns same level)
        """
        if score >= 80:
            return RiskLevel.SAFE
        elif score >= 50:
            return RiskLevel.WARNING
        else:
            return RiskLevel.HIGH_RISK

    def analyze(self, metrics: RecruiterMetrics) -> ComplianceResult:
        """
        Analyze recruiter metrics and return comprehensive compliance result.

        This method orchestrates the complete compliance analysis workflow:
        1. Evaluate all compliance rules to detect violations
        2. Calculate compliance score based on violations
        3. Classify risk level based on score
        4. Generate human-readable report
        5. Generate actionable recommendations

        Args:
            metrics: RecruiterMetrics object containing recruiter activity data

        Returns:
            ComplianceResult object with complete analysis results

        Preconditions:
            - metrics is a valid RecruiterMetrics object
            - All metric fields satisfy validation rules
            - metrics.license_id is non-empty

        Postconditions:
            - Returns valid ComplianceResult object
            - result.compliance_score is between 0 and 100
            - result.risk_level correctly corresponds to score
            - result.violations contains all detected violations
            - result.report is non-empty string
            - No mutations to input metrics

        Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
        """
        from ai_report import generate_report, generate_recommendations

        # Step 1: Evaluate all compliance rules
        violations = self.evaluate_rules(metrics)

        # Step 2: Calculate compliance score with deductions
        score = self.calculate_score(violations)

        # Step 3: Classify risk level
        risk_level = self.classify_risk(score)

        # Step 4 & 5: Generate report and recommendations
        # We need to create a temporary result object for the report generator
        # but we'll build the final result directly to avoid validation issues

        # Create a simple temporary object for report generation
        class TempResult:
            def __init__(self, metrics, violations, compliance_score, risk_level):
                self.metrics = metrics
                self.violations = violations
                self.compliance_score = compliance_score
                self.risk_level = risk_level

        temp_result = TempResult(metrics, violations, score, risk_level)

        # Generate report and recommendations
        report = generate_report(temp_result)
        recommendations = generate_recommendations(temp_result)

        # Step 6: Create final result with all components
        final_result = ComplianceResult(
            metrics=metrics,
            violations=violations,
            compliance_score=score,
            risk_level=risk_level,
            report=report,
            recommendations=recommendations
        )

        return final_result




