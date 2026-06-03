```python
from models import MetricInput, HealthReport
from typing import List


def compute_error_rate(metric: MetricInput) -> float:
    """
    Calculate the error rate for a given service metric.
    
    Includes robust SRE guardrails to safely handle zero-traffic scenarios
    and inconsistent telemetry pipeline payloads without raising runtime errors.
    """
    # Guard against zero or negative traffic (e.g., cold starts or inactive services)
    if metric.total_requests <= 0:
        return 0.0

    # Guard against negative failed requests anomalies
    safe_failed_requests = max(0, metric.failed_requests)

    # Guard against inconsistent state where failed requests exceed total requests.
    # We cap at 1.0 (100%) to trigger a CRITICAL health status without crashing the API.
    if safe_failed_requests > metric.total_requests:
        return 1.0

    error_rate = safe_failed_requests / metric.total_requests
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
```