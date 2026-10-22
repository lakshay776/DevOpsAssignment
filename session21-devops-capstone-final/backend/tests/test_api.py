"""API tests: probes, issue CRUD, filtering, worklog and stats."""


# ------------------------------------------------------------------ probes

def test_health_is_up(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "UP"}


def test_ready_checks_the_database(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "READY"}


def test_metrics_exposes_prometheus_text(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    # The custom domain metric must be present, not just the HTTP ones.
    assert "campusdesk_issues_open" in r.text


# ------------------------------------------------------------------ create

def test_create_issue_returns_201_and_defaults(client):
    r = client.post(
        "/api/issues",
        json={"title": "Tap leaking in washroom", "building": "Library"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["id"] > 0
    assert body["status"] == "open"
    assert body["priority"] == "medium"
    assert body["category"] == "other"
    assert body["resolved_at"] is None


def test_create_rejects_a_too_short_title(client):
    r = client.post("/api/issues", json={"title": "ac", "building": "Library"})
    assert r.status_code == 422


def test_create_rejects_a_missing_building(client):
    r = client.post("/api/issues", json={"title": "Broken chair in room 12"})
    assert r.status_code == 422


# -------------------------------------------------------------------- read

def test_list_returns_created_issues(client, sample_issue):
    r = client.get("/api/issues")
    assert r.status_code == 200
    assert [i["id"] for i in r.json()] == [sample_issue["id"]]


def test_list_filters_by_status_and_building(client, sample_issue):
    client.post("/api/issues", json={"title": "Wifi dropping out", "building": "Hostel A"})

    assert len(client.get("/api/issues").json()) == 2
    assert len(client.get("/api/issues?building=Hostel A").json()) == 1
    assert len(client.get("/api/issues?priority=high").json()) == 1
    assert len(client.get("/api/issues?status=resolved").json()) == 0


def test_get_single_issue_includes_worklog(client, sample_issue):
    r = client.get(f"/api/issues/{sample_issue['id']}")
    assert r.status_code == 200
    assert r.json()["updates"] == []


def test_get_missing_issue_is_404(client):
    assert client.get("/api/issues/9999").status_code == 404


# ------------------------------------------------------------------ update

def test_update_changes_only_the_fields_sent(client, sample_issue):
    r = client.put(f"/api/issues/{sample_issue['id']}", json={"status": "in_progress"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "in_progress"
    # Untouched fields must survive the partial update.
    assert body["title"] == sample_issue["title"]
    assert body["priority"] == sample_issue["priority"]


def test_resolving_stamps_resolved_at(client, sample_issue):
    body = client.put(f"/api/issues/{sample_issue['id']}", json={"status": "resolved"}).json()
    assert body["status"] == "resolved"
    assert body["resolved_at"] is not None


def test_reopening_clears_resolved_at(client, sample_issue):
    client.put(f"/api/issues/{sample_issue['id']}", json={"status": "resolved"})
    body = client.put(f"/api/issues/{sample_issue['id']}", json={"status": "open"}).json()
    assert body["resolved_at"] is None


def test_update_missing_issue_is_404(client):
    assert client.put("/api/issues/9999", json={"status": "open"}).status_code == 404


# ------------------------------------------------------------------ delete

def test_delete_removes_the_issue(client, sample_issue):
    assert client.delete(f"/api/issues/{sample_issue['id']}").status_code == 204
    assert client.get(f"/api/issues/{sample_issue['id']}").status_code == 404


def test_delete_missing_issue_is_404(client):
    assert client.delete("/api/issues/9999").status_code == 404


# ----------------------------------------------------------------- worklog

def test_add_and_list_worklog_notes(client, sample_issue):
    issue_id = sample_issue["id"]
    r = client.post(
        f"/api/issues/{issue_id}/updates",
        json={"note": "Spare bulb ordered", "author": "maintenance"},
    )
    assert r.status_code == 201
    assert r.json()["note"] == "Spare bulb ordered"

    listed = client.get(f"/api/issues/{issue_id}/updates").json()
    assert len(listed) == 1
    assert client.get(f"/api/issues/{issue_id}").json()["updates"][0]["author"] == "maintenance"


def test_worklog_on_missing_issue_is_404(client):
    assert client.post("/api/issues/9999/updates", json={"note": "x"}).status_code == 404


def test_deleting_an_issue_cascades_to_its_worklog(client, sample_issue):
    issue_id = sample_issue["id"]
    client.post(f"/api/issues/{issue_id}/updates", json={"note": "Looked at it"})
    assert client.delete(f"/api/issues/{issue_id}").status_code == 204
    assert client.get(f"/api/issues/{issue_id}/updates").status_code == 404


# ------------------------------------------------------------------- stats

def test_stats_on_an_empty_database(client):
    body = client.get("/api/stats").json()
    assert body["total"] == 0
    assert body["avg_resolution_hours"] is None


def test_stats_counts_and_groups(client, sample_issue):
    client.post(
        "/api/issues",
        json={"title": "Fire alarm beeping", "building": "Hostel A", "priority": "urgent"},
    )
    client.put(f"/api/issues/{sample_issue['id']}", json={"status": "resolved"})

    body = client.get("/api/stats").json()
    assert body["total"] == 2
    assert body["resolved"] == 1
    assert body["open"] == 1
    assert body["urgent_open"] == 1
    assert body["by_building"]["Hostel A"] == 1
    assert body["by_category"]["electrical"] == 1
    # Resolved immediately, so the average is ~0 hours but no longer None.
    assert body["avg_resolution_hours"] is not None
