# JSO Compliance Sentinel

An **AI Licensing Governance Agent** prototype for a recruitment platform. The system monitors recruiter license usage, detects compliance violations, evaluates recruiter quality, and generates automated governance reports using a **Hybrid AI Agent Architecture**.

## AI Agent Architecture

JSO Compliance Sentinel demonstrates a **Hybrid Governance Agent** with two layers:

### Layer 1: Deterministic Compliance Engine
- Rule-based compliance checks for transparency and auditing
- Evaluates 4 compliance rules:
  - **RULE_1**: High application volume (> 50 applications/day)
  - **RULE_2**: Duplicate CV submissions (> 5 duplicates)
  - **RULE_3**: Low employer response rate (< 5.0%)
  - **RULE_4**: Possible license sharing (> 3 IP addresses)
- Calculates compliance scores (0-100)
- Classifies risk levels (SAFE, WARNING, HIGH_RISK)

### Layer 2: AI Reasoning Agent (Groq LLM)
- Uses **Groq LLM (llama-3.3-70b-versatile)** for intelligent analysis
- Interprets behavior patterns and context
- Provides governance insights and recommendations
- Generates natural language compliance intelligence reports

### Workflow
```
Recruiter Activity Input
    ↓
Rule-Based Compliance Engine (Layer 1)
    ↓
Structured Behavior Summary
    ↓
Groq LLM Agent (Layer 2)
    ↓
Compliance Intelligence Report
    ↓
Dashboard Display
```

## Project Structure

```
.
├── models.py                  # Core data models
├── compliance_engine.py       # Layer 1: Rule-based compliance engine
├── agent.py                   # Layer 2: AI reasoning agent (Groq LLM)
├── ai_report.py              # Report generation utilities
├── mock_data.py              # Mock data generator
├── app.py                    # Streamlit dashboard UI
├── test_*.py                 # Test suites
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Groq API Key

The AI agent requires a Groq API key. Get your free API key from [Groq Console](https://console.groq.com/).

**Set the environment variable:**

```bash
export GROQ_API_KEY=your_key_here
```

**Or on Windows:**

```cmd
set GROQ_API_KEY=your_key_here
```

**Note:** The system will work without the API key but will only use rule-based analysis (Layer 1). The AI agent (Layer 2) requires the API key.

### 3. Run the Application

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Usage

1. **Load Mock Data (Optional)**: Select a pre-configured recruiter example from the dropdown
2. **Enter Recruiter Metrics**: Input the five required metrics or use loaded mock data
3. **Run Compliance Analysis**: Click the button to analyze
4. **View Results**:
   - Compliance score and risk level
   - Rule-based compliance report
   - Rule engine recommendations
   - **AI Compliance Agent Analysis** (if API key is configured)

## Data Models

### RecruiterMetrics
Represents recruiter activity metrics for compliance analysis.

**Fields:**
- `license_id` (str): Non-empty license identifier
- `applications_sent_today` (int): Non-negative count of applications
- `duplicate_cvs` (int): Non-negative count of duplicate submissions
- `employer_response_rate` (float): Response rate percentage (0.0-100.0)
- `ip_addresses_used` (int): Positive count of IP addresses (≥1)

### Violation
Represents a compliance rule violation.

**Fields:**
- `rule_id` (str): Non-empty rule identifier (e.g., "RULE_1")
- `description` (str): Non-empty violation description
- `penalty_points` (int): Positive penalty value

### RiskLevel
Enum for risk classification.

**Values:**
- `SAFE`: Compliance score ≥ 80
- `WARNING`: Compliance score 50-79
- `HIGH_RISK`: Compliance score < 50

### ComplianceResult
Complete compliance analysis result.

**Fields:**
- `metrics` (RecruiterMetrics): Input metrics
- `violations` (list[Violation]): Detected violations
- `compliance_score` (int): Score 0-100
- `risk_level` (RiskLevel): Risk classification
- `report` (str): Human-readable report
- `recommendations` (list[str]): Actionable recommendations

## Testing

The application is ready to use. No test suite is included in this minimal prototype.

To verify the application works:

```bash
streamlit run app.py
```

Then test with the provided mock data examples.

## Key Features

✅ **Hybrid AI Architecture**: Combines deterministic rules with LLM reasoning  
✅ **Real-time Compliance Monitoring**: Instant analysis of recruiter behavior  
✅ **Risk Classification**: Automatic categorization (SAFE, WARNING, HIGH_RISK)  
✅ **AI-Powered Insights**: Natural language governance recommendations  
✅ **Mock Data**: 10 pre-configured test scenarios  
✅ **Performance**: < 100ms analysis time (rule engine)  
✅ **Clean UI**: Color-coded Streamlit dashboard  
✅ **Fallback Mode**: Works without AI agent (rule-based only)

## Technology Stack

- **Python 3.10+**: Core language
- **Streamlit**: Dashboard UI framework
- **Groq SDK**: LLM API integration
- **llama-3.3-70b-versatile**: AI reasoning model
- **Pytest**: Testing framework

## License & Compliance

This is a prototype demonstration system. For production use:
- Add authentication and authorization
- Implement audit logging
- Add data encryption
- Comply with data protection regulations
- Add rate limiting for API calls
- Implement proper error handling and monitoring
