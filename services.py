```python
from typing import List
from fastapi import HTTPException
from models import MetricInput, HealthReport, BatchMetricInput


def compute_error_rate(metric: MetricInput) -> float:
    """Calculate the error rate for a given service metric.
    
    Returns 0.0 if there are no requests to prevent division by zero.
    """
    if metric.total_requests <= 0:
        return 0.0
        
    try:
        error_rate = metric.failed_requests / metric.total_requests
        return round(error_rate, 4)
    except ZeroDivisionError:
        # Fallback safeguard
        return 0.0


def classify_health(error_rate: float, latency_ms: float) -> str:
    """Classify service health based on error rate and latency thresholds."""
    if error_rate > 0.05:
        return "CRITICAL"
    elif error_rate > 0.01 or latency_ms > 500:
        return "DEGRADED"
    return "HEALTHY"


def generate_recommendation(status: str, error_rate: float, latency_ms: float) -> str:
    """Generate an actionable recommendation based on health classification."""
    if status == "CRITICAL":
        return (
            f"Error rate is {error_rate:.1%}. "
            "Immediate investigation required. Check recent deployments and rollback if necessary."
        )
    elif status == "DEGRADED":
        if latency_ms > 500:
            return (
                f"Latency is {latency_ms:.0f}ms. "
                "Review database queries and upstream dependencies for bottlenecks."
            )
        return (
            f"Error rate is {error_rate:.1%}. "
            "Monitor closely and review error logs for recurring patterns."
        )
    return "All systems nominal. No action required."


def analyze_single_metric(metric: MetricInput) -> HealthReport:
    """Run the full analysis pipeline for a single service metric."""
    error_rate = compute_error_rate(metric)
    status = classify_health(error_rate, metric.latency_ms)
    recommendation = generate_recommendation(status, error_rate, metric.latency_ms)

    return HealthReport(
        service_name=metric.service_name,
        status=status,
        error_rate=error_rate,
        avg_latency_ms=metric.latency_ms,
        recommendation=recommendation
    )


def analyze_metric_batch(payload: BatchMetricInput):
    """Analyze a batch of service metrics and return health reports."""
    if not payload.metrics:
        raise HTTPException(status_code=400, detail="Metrics list cannot be empty.")
    try:
        # Assuming analyze_batch and log_analysis_event are defined globally or imported
        reports = [analyze_single_metric(m) for m in payload.metrics]
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```