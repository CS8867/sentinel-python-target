```python
# ==========================================
# FILE: services.py
# ==========================================
from models import MetricInput, HealthReport
from typing import List

def compute_error_rate(metric: MetricInput) -> float:
    """
    Calculate the error rate for a given service metric.
    Gracefully handles zero traffic and telemetry inconsistency.
    """
    # Guard against zero-traffic states (standard runtime behavior)
    if metric.total_requests == 0:
        return 0.0

    # Guard against invalid/inconsistent telemetry states (e.g., negative counters)
    if metric.total_requests < 0 or metric.failed_requests < 0:
        return 0.0

    # Guard against telemetry reporting failed_requests > total_requests
    if metric.failed_requests > metric.total_requests:
        return 1.0  # Cap at 100% error rate rather than crashing

    error_rate = metric.failed_requests / metric.total_requests
    return round(error_rate, 4)


def classify_health(error_rate: float, latency_ms: float) -> str:
    """Classify service health based on error rate and latency thresholds."""
    if error_rate > 0.05:
        return "CRITICAL"
    elif error_rate > 0.01 or latency_ms > 500:
        return "DEGRADED"
    return "HEALTHY"


def analyze_single_metric(metric: MetricInput) -> HealthReport:
    """Analyze a single service metric and return a health report."""
    error_rate = compute_error_rate(metric)
    status = classify_health(error_rate, metric.latency_ms)
    return HealthReport(
        service_name=metric.service_name,
        status=status,
        error_rate=error_rate,
        latency_ms=metric.latency_ms
    )


def analyze_batch(metrics: List[MetricInput]) -> List[HealthReport]:
    """Analyze a batch of service metrics and return health reports."""
    return [analyze_single_metric(metric) for metric in metrics]


# ==========================================
# FILE: main.py
# ==========================================
from fastapi import FastAPI, HTTPException
from models import MetricInput, BatchMetricInput, HealthReport
from services import analyze_single_metric, analyze_batch
from utils import log_analysis_event, get_timestamp
from typing import List

app = FastAPI(
    title="Sentinel Health Analyzer",
    description="Microservice for real-time service health analysis and incident classification.",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    """Liveness probe for the service."""
    return {"status": "ok", "timestamp": get_timestamp()}


@app.post("/analyze", response_model=HealthReport)
def analyze_metric(metric: MetricInput):
    """Analyze a single service metric and return a health report."""
    try:
        report = analyze_single_metric(metric)
        log_analysis_event(report.service_name, report.status)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze/batch", response_model=List[HealthReport])
def analyze_metric_batch(payload: BatchMetricInput):
    """Analyze a batch of service metrics and return health reports."""
    if not payload.metrics:
        raise HTTPException(status_code=400, detail="Metrics list cannot be empty.")
    try:
        reports = analyze_batch(payload.metrics)
        for report in reports:
            log_analysis_event(report.service_name, report.status)
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")
```