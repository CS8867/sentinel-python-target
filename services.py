```python
import logging
from typing import List
from fastapi import HTTPException
from models import MetricInput, HealthReport, BatchMetricInput

# Configure logger for tracking telemetry events
logger = logging.getLogger(__name__)


def log_analysis_event(service_name: str, status: str):
    """Log the outcome of a service health analysis."""
    logger.info(f"SLA Analysis completed for '{service_name}' - Status: {status}")


def compute_error_rate(metric: MetricInput) -> float:
    """
    Calculate the error rate for a given service metric.
    Gracefully handles idle states and detects genuine telemetry inconsistencies.
    """
    # 1. Handle Negative Values
    if metric.total_requests < 0 or metric.failed_requests < 0:
        raise RuntimeError(
            f"SLA metric computation failed for '{metric.service_name}': "
            f"telemetry pipeline returned negative metrics (total={metric.total_requests}, failed={metric.failed_requests})."
        )

    # 2. Handle Idle Service (Zero Traffic)
    if metric.total_requests == 0:
        if metric.failed_requests > 0:
            raise RuntimeError(
                f"SLA metric computation failed for '{metric.service_name}': "
                f"telemetry pipeline returned inconsistent state (failed_requests={metric.failed_requests} but total_requests=0)."
            )
        return 0.0

    # 3. Handle Logical Telemetry Inconsistencies
    if metric.failed_requests > metric.total_requests:
        raise RuntimeError(
            f"SLA metric computation failed for '{metric.service_name}': "
            f"telemetry pipeline returned inconsistent state (failed_requests={metric.failed_requests} exceeds total_requests={metric.total_requests})."
        )

    error_rate = metric.failed_requests / metric.total_requests
    return round(error_rate, 4)


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


def analyze_batch(metrics: List[MetricInput]) -> List[HealthReport]:
    """Analyze a list of metric inputs and map them to health reports."""
    return [analyze_single_metric(metric) for metric in metrics]


def analyze_metric_batch(payload: BatchMetricInput) -> List[HealthReport]:
    """Analyze a batch of service metrics and return health reports."""
    if not payload.metrics:
        raise HTTPException(status_code=400, detail="Metrics list cannot be empty.")
    try:
        reports = analyze_batch(payload.metrics)
        for report in reports:
            log_analysis_event(report.service_name, report.status)
        return reports
    except Exception as e:
        logger.error(f"Batch analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```