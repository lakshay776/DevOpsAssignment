"""CampusDesk API.

Campus facility issues: report them, track them, close them.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app import metrics
from app.config import settings
from app.db import Base, SessionLocal, engine, get_db
from app.models import Category, Issue, IssueUpdate, Priority, Status
from app.schemas import (
    IssueCreate,
    IssueDetail,
    IssueOut,
    IssuePatch,
    IssueUpdateCreate,
    IssueUpdateOut,
    Stats,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Starlette 1.x removed `on_event`, so startup work lives here.

    Alembic owns the schema in every real deployment. `create_all` is a
    convenience for `docker compose up` on a fresh volume and is a no-op once
    the migration has run.
    """
    if not settings.testing:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            metrics.refresh_open_gauge(db)
        finally:
            db.close()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

# Must be attached before the app starts serving, or /metrics 404s.
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


# ---------------------------------------------------------------- probes

@app.get("/")
def root() -> dict:
    return {"app": settings.app_name, "docs": "/docs", "health": "/health"}


@app.get("/health")
def health() -> dict:
    """Liveness: the process is up. Deliberately does not touch the database -
    a slow query should not get the pod killed and restarted."""
    return {"status": "UP"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    """Readiness: the database is reachable, so this pod can serve traffic."""
    try:
        db.execute(select(1))
    except Exception as exc:  # noqa: BLE001 - surfaced to the probe as 503
        raise HTTPException(status_code=503, detail=f"database unreachable: {exc}") from exc
    return {"status": "READY"}


# ---------------------------------------------------------------- issues

@app.get("/api/issues", response_model=list[IssueOut])
def list_issues(
    db: Session = Depends(get_db),
    status_filter: Status | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    category: Category | None = None,
    building: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Issue]:
    stmt = select(Issue)
    if status_filter:
        stmt = stmt.where(Issue.status == status_filter)
    if priority:
        stmt = stmt.where(Issue.priority == priority)
    if category:
        stmt = stmt.where(Issue.category == category)
    if building:
        stmt = stmt.where(Issue.building == building)
    stmt = stmt.order_by(Issue.created_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())


@app.get("/api/issues/{issue_id}", response_model=IssueDetail)
def get_issue(issue_id: int, db: Session = Depends(get_db)) -> Issue:
    # selectinload avoids the N+1 that lazy-loading the worklog would cause.
    issue = db.execute(
        select(Issue).options(selectinload(Issue.updates)).where(Issue.id == issue_id)
    ).scalar_one_or_none()
    if issue is None:
        raise HTTPException(status_code=404, detail="issue not found")
    return issue


@app.post("/api/issues", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
def create_issue(payload: IssueCreate, db: Session = Depends(get_db)) -> Issue:
    issue = Issue(**payload.model_dump())
    db.add(issue)
    db.commit()
    db.refresh(issue)

    metrics.issues_created_total.labels(
        category=issue.category.value, priority=issue.priority.value
    ).inc()
    metrics.refresh_open_gauge(db)
    return issue


@app.put("/api/issues/{issue_id}", response_model=IssueOut)
def update_issue(issue_id: int, payload: IssuePatch, db: Session = Depends(get_db)) -> Issue:
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="issue not found")

    was_resolved = issue.status == Status.RESOLVED
    # exclude_unset so an omitted field keeps its value instead of being
    # overwritten with the schema default.
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(issue, field, value)

    now = datetime.now(timezone.utc)
    if issue.status == Status.RESOLVED and not was_resolved:
        issue.resolved_at = now
        metrics.issues_resolved_total.labels(category=issue.category.value).inc()
        created = issue.created_at
        if created is not None:
            # Postgres returns tz-aware values; SQLite in tests returns naive
            # ones. Normalise before subtracting or this raises TypeError.
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            metrics.resolution_seconds.observe((now - created).total_seconds())
    elif issue.status != Status.RESOLVED and was_resolved:
        # Reopened: clear the stamp so the next resolution is timed correctly.
        issue.resolved_at = None

    db.commit()
    db.refresh(issue)
    metrics.refresh_open_gauge(db)
    return issue


@app.delete("/api/issues/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(issue_id: int, db: Session = Depends(get_db)) -> Response:
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="issue not found")
    db.delete(issue)
    db.commit()
    metrics.refresh_open_gauge(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------- worklog

@app.get("/api/issues/{issue_id}/updates", response_model=list[IssueUpdateOut])
def list_updates(issue_id: int, db: Session = Depends(get_db)) -> list[IssueUpdate]:
    if db.get(Issue, issue_id) is None:
        raise HTTPException(status_code=404, detail="issue not found")
    return list(
        db.execute(
            select(IssueUpdate)
            .where(IssueUpdate.issue_id == issue_id)
            .order_by(IssueUpdate.created_at)
        ).scalars().all()
    )


@app.post(
    "/api/issues/{issue_id}/updates",
    response_model=IssueUpdateOut,
    status_code=status.HTTP_201_CREATED,
)
def add_update(
    issue_id: int, payload: IssueUpdateCreate, db: Session = Depends(get_db)
) -> IssueUpdate:
    if db.get(Issue, issue_id) is None:
        raise HTTPException(status_code=404, detail="issue not found")
    note = IssueUpdate(issue_id=issue_id, **payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# ---------------------------------------------------------------- stats

@app.get("/api/stats", response_model=Stats)
def stats(db: Session = Depends(get_db)) -> Stats:
    by_status = dict(
        db.execute(select(Issue.status, func.count(Issue.id)).group_by(Issue.status)).all()
    )

    def count_for(state: Status) -> int:
        return next((v for k, v in by_status.items() if k == state), 0)

    urgent_open = db.execute(
        select(func.count(Issue.id)).where(
            Issue.status != Status.RESOLVED, Issue.priority == Priority.URGENT
        )
    ).scalar_one()

    by_building = {
        str(getattr(b, "value", b)): c
        for b, c in db.execute(
            select(Issue.building, func.count(Issue.id)).group_by(Issue.building)
        ).all()
    }
    by_category = {
        str(getattr(c, "value", c)): n
        for c, n in db.execute(
            select(Issue.category, func.count(Issue.id)).group_by(Issue.category)
        ).all()
    }

    # Averaging in Python rather than SQL keeps this portable across Postgres
    # and the SQLite database the tests use.
    spans = [
        (i.resolved_at, i.created_at)
        for i in db.execute(
            select(Issue).where(Issue.resolved_at.is_not(None))
        ).scalars().all()
    ]
    avg_hours: float | None = None
    if spans:
        total = 0.0
        for resolved, created in spans:
            if resolved.tzinfo is None:
                resolved = resolved.replace(tzinfo=timezone.utc)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            total += (resolved - created).total_seconds()
        avg_hours = round(total / len(spans) / 3600, 2)

    return Stats(
        total=sum(by_status.values()),
        open=count_for(Status.OPEN),
        in_progress=count_for(Status.IN_PROGRESS),
        resolved=count_for(Status.RESOLVED),
        urgent_open=urgent_open,
        by_building=by_building,
        by_category=by_category,
        avg_resolution_hours=avg_hours,
    )
