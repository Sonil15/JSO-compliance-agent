"""
Data models for JSO Compliance Sentinel.

This module defines the core data structures used throughout the application:
- RecruiterMetrics: Input data representing recruiter activity
- Violation: Compliance rule breach representation
- RiskLevel: Risk classification enum
- ComplianceResult: Complete analysis output
"""

from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Risk classification levels for compliance assessment."""
    SAFE = "SAFE"
    WARNING = "WARNING"
    HIGH_RISK = "HIGH_RISK"


@dataclass
class RecruiterMetrics:
    """
    Recruiter activity metrics for compliance analysis.
    
    Validation Rules:
    - license_id: non-empty string
    - applications_sent_today: non-negative integer
    - duplicate_cvs: non-negative integer
    - employer_response_rate: float between 0.0 and 100.0
    - ip_addresses_used: positive integer (>= 1)
    """
    license_id: str
    applications_sent_today: int
    duplicate_cvs: int
    employer_response_rate: float  # percentage (0-100)
    ip_addresses_used: int
    
    def __post_init__(self):
        """Validate field values after initialization."""
        if not self.license_id or not isinstance(self.license_id, str):
            raise ValueError("license_id must be a non-empty string")
        if not isinstance(self.applications_sent_today, int) or self.applications_sent_today < 0:
            raise ValueError("applications_sent_today must be a non-negative integer")
        if not isinstance(self.duplicate_cvs, int) or self.duplicate_cvs < 0:
            raise ValueError("duplicate_cvs must be a non-negative integer")
        if not isinstance(self.employer_response_rate, (int, float)) or not (0.0 <= self.employer_response_rate <= 100.0):
            raise ValueError("employer_response_rate must be a float between 0.0 and 100.0")
        if not isinstance(self.ip_addresses_used, int) or self.ip_addresses_used < 1:
            raise ValueError("ip_addresses_used must be a positive integer (>= 1)")


@dataclass
class Violation:
    """
    Represents a compliance rule violation.
    
    Validation Rules:
    - rule_id: non-empty string (e.g., "RULE_1", "RULE_2")
    - description: non-empty string
    - penalty_points: positive integer
    """
    rule_id: str
    description: str
    penalty_points: int
    
    def __post_init__(self):
        """Validate field values after initialization."""
        if not self.rule_id or not isinstance(self.rule_id, str):
            raise ValueError("rule_id must be a non-empty string")
        if not self.description or not isinstance(self.description, str):
            raise ValueError("description must be a non-empty string")
        if not isinstance(self.penalty_points, int) or self.penalty_points <= 0:
            raise ValueError("penalty_points must be a positive integer")


@dataclass
class ComplianceResult:
    """
    Complete compliance analysis result.
    
    Validation Rules:
    - compliance_score: integer between 0 and 100 (inclusive)
    - violations: list (may be empty)
    - recommendations: non-empty list when violations exist
    """
    metrics: RecruiterMetrics
    violations: list[Violation]
    compliance_score: int  # 0-100
    risk_level: RiskLevel
    report: str
    recommendations: list[str]
    
    def __post_init__(self):
        """Validate field values after initialization."""
        if not isinstance(self.compliance_score, int) or not (0 <= self.compliance_score <= 100):
            raise ValueError("compliance_score must be an integer between 0 and 100")
        if not isinstance(self.violations, list):
            raise ValueError("violations must be a list")
        if not isinstance(self.recommendations, list):
            raise ValueError("recommendations must be a list")
        if self.violations and not self.recommendations:
            raise ValueError("recommendations must be non-empty when violations exist")
