```python
from models import MetricInput, HealthReport
from typing import List


def compute_error_rate(metric: MetricInput) -> float:
    """Calculate the error rate for a given service metric with guards against zero traffic."""
    # Guard against zero traffic to avoid DivisionByZero / RuntimeErrors
    if metric.total_requests <= 0:
        return 0.0

    # Guard against telemetry inconsistency (more failures reported than total requests)
    if metric.failed_requests > metric.total_requests:
        return 1.0

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
    """Analyze a single service metric and return a compiled health report."""
    error_rate = compute_error_rate(metric)
    status = classify_health(error_rate, metric.latency_ms)
    
    return HealthReport(
        service_name=metric.service_name,
        status=status,
        error_rate=error_rate,
        latency_ms=metric.latency_ms
    )


def analyze_batch(metrics: List[MetricInput]) -> List[HealthReport]:
    """Analyze a batch of service metrics and return a list of health reports."""
    return [analyze_single_metric(metric) for metric in metrics]
```