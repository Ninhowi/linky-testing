from __future__ import annotations

import csv
import os
import time
from collections.abc import Callable
from pathlib import Path


DEFAULT_PERFORMANCE_REPORT = Path("reports/performance_results.csv")


def _report_path() -> Path:
    return Path(os.environ.get("PERFORMANCE_REPORT_PATH", DEFAULT_PERFORMANCE_REPORT))


def measure_seconds(action: Callable[[], object]) -> float:
    """Measure elapsed time for one UI business action."""
    start = time.perf_counter()
    action()
    return round(time.perf_counter() - start, 3)


def write_performance_result(
    *,
    test_id: str,
    feature: str,
    metric: str,
    duration: float,
    threshold: float,
) -> None:
    """Append one performance result row to CSV."""
    path = _report_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    is_new_file = not path.exists()
    status = "PASS" if duration <= threshold else "FAIL"

    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if is_new_file:
            writer.writerow(
                [
                    "Test ID",
                    "Feature",
                    "Metric",
                    "Actual Time (s)",
                    "Threshold (s)",
                    "Status",
                ]
            )

        writer.writerow(
            [
                test_id,
                feature,
                metric,
                duration,
                threshold,
                status,
            ]
        )


def assert_performance(
    *,
    test_id: str,
    feature: str,
    metric: str,
    duration: float,
    threshold: float,
) -> None:
    """Save the metric and fail the test if the threshold is exceeded."""
    write_performance_result(
        test_id=test_id,
        feature=feature,
        metric=metric,
        duration=duration,
        threshold=threshold,
    )

    assert duration <= threshold, (
        f"{test_id} failed: {metric} took {duration}s, "
        f"threshold is {threshold}s"
    )
