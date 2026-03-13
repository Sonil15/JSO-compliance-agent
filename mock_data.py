"""
Mock data generator for JSO Compliance Sentinel.

This module provides functions to generate realistic test data for demonstration
purposes without requiring production data.
"""

from models import RecruiterMetrics


def generate_mock_recruiters() -> list[RecruiterMetrics]:
    """
    Generate 8-10 mock recruiter records with diverse compliance patterns.
    
    Returns a list containing examples of:
    - SAFE patterns (score 80+): No violations or minimal violations
    - WARNING patterns (score 50-79): 1-2 violations
    - HIGH_RISK patterns (score <50): 3-4 violations
    
    All fields satisfy validation rules from RecruiterMetrics.
    
    Returns:
        list[RecruiterMetrics]: List of 10 diverse recruiter records
    
    **Validates: Requirements 7.1, 7.2, 7.3**
    """
    return [
        # SAFE examples (score 100 - no violations)
        RecruiterMetrics(
            license_id="REC-001",
            applications_sent_today=30,
            duplicate_cvs=2,
            employer_response_rate=15.5,
            ip_addresses_used=1
        ),
        RecruiterMetrics(
            license_id="REC-002",
            applications_sent_today=45,
            duplicate_cvs=3,
            employer_response_rate=22.0,
            ip_addresses_used=2
        ),
        
        # SAFE with single violation (score 80)
        RecruiterMetrics(
            license_id="REC-003",
            applications_sent_today=55,  # Triggers RULE_1 (-20)
            duplicate_cvs=4,
            employer_response_rate=18.5,
            ip_addresses_used=2
        ),
        
        # WARNING examples (score 50-79)
        RecruiterMetrics(
            license_id="REC-004",
            applications_sent_today=60,  # Triggers RULE_1 (-20)
            duplicate_cvs=8,  # Triggers RULE_2 (-30)
            employer_response_rate=12.0,
            ip_addresses_used=2
        ),
        RecruiterMetrics(
            license_id="REC-005",
            applications_sent_today=40,
            duplicate_cvs=7,  # Triggers RULE_2 (-30)
            employer_response_rate=3.5,  # Triggers RULE_3 (-25)
            ip_addresses_used=1
        ),
        RecruiterMetrics(
            license_id="REC-006",
            applications_sent_today=52,  # Triggers RULE_1 (-20)
            duplicate_cvs=2,
            employer_response_rate=4.2,  # Triggers RULE_3 (-25)
            ip_addresses_used=3
        ),
        
        # HIGH_RISK examples (score <50)
        RecruiterMetrics(
            license_id="REC-007",
            applications_sent_today=75,  # Triggers RULE_1 (-20)
            duplicate_cvs=10,  # Triggers RULE_2 (-30)
            employer_response_rate=2.5,  # Triggers RULE_3 (-25)
            ip_addresses_used=2
        ),
        RecruiterMetrics(
            license_id="REC-008",
            applications_sent_today=65,  # Triggers RULE_1 (-20)
            duplicate_cvs=6,  # Triggers RULE_2 (-30)
            employer_response_rate=8.0,
            ip_addresses_used=5  # Triggers RULE_4 (-25)
        ),
        RecruiterMetrics(
            license_id="REC-009",
            applications_sent_today=80,  # Triggers RULE_1 (-20)
            duplicate_cvs=12,  # Triggers RULE_2 (-30)
            employer_response_rate=1.5,  # Triggers RULE_3 (-25)
            ip_addresses_used=4  # Triggers RULE_4 (-25)
        ),
        
        # Edge case: Borderline metrics
        RecruiterMetrics(
            license_id="REC-010",
            applications_sent_today=50,  # Just at threshold (no violation)
            duplicate_cvs=5,  # Just at threshold (no violation)
            employer_response_rate=5.0,  # Just at threshold (no violation)
            ip_addresses_used=3  # Just at threshold (no violation)
        ),
    ]


def get_recruiter_by_id(license_id: str) -> RecruiterMetrics | None:
    """
    Retrieve mock recruiter data by license ID.
    
    Args:
        license_id: The license ID to search for
    
    Returns:
        RecruiterMetrics if found, None otherwise
    
    **Validates: Requirements 7.4, 7.5**
    """
    recruiters = generate_mock_recruiters()
    for recruiter in recruiters:
        if recruiter.license_id == license_id:
            return recruiter
    return None
