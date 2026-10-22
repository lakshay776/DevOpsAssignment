"""Domain metrics, on top of the HTTP metrics the instrumentator provides.

Request rate and latency say the service is alive. These say whether the
campus is actually getting fixed, which is what the Grafana dashboard is for.
"""

from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Issue, Status

issues_created_total = Counter(
    "campusdesk_issues_created_total",
    "Issues reported, by category and priority.",
    ["category", "priority"],
)

issues_resolved_total = Counter(
    "campusdesk_issues_resolved_total",
    "Issues moved to resolved, by category.",
    ["category"],
)

issues_open = Gauge(
    "campusdesk_issues_open",
    "Current open backlog, by priority.",
    ["priority"],
)

resolution_seconds = Histogram(
    "campusdesk_issue_resolution_seconds",
    "Time from report to resolution.",
    # Campus repairs run in hours and days, not milliseconds, so the default
    # buckets (which top out at 10s) would put everything in +Inf.
    buckets=(300, 900, 3600, 10800, 21600, 43200, 86400, 259200, 604800),
)


def refresh_open_gauge(db: Session) -> None:
    """Recompute the backlog gauge from the database.

    A gauge has to reflect current state, not accumulate, so it is recomputed
    rather than incremented. Called after any write that can change the
    backlog, and once at startup so a freshly scheduled pod reports real
    numbers instead of zeroes.
    """
    counts = dict(
        db.execute(
            select(Issue.priority, func.count(Issue.id))
            .where(Issue.status != Status.RESOLVED)
            .group_by(Issue.priority)
        ).all()
    )
    for priority in ("low", "medium", "high", "urgent"):
        # Every label has to be set explicitly, including the zeroes, or a
        # priority that drops to zero keeps its last value forever.
        key = next((k for k in counts if getattr(k, "value", k) == priority), None)
        issues_open.labels(priority=priority).set(counts.get(key, 0) if key else 0)
