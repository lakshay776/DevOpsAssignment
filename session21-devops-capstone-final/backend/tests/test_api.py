def test_health(client):
    assert client.get("/health").json() == {"status": "UP"}

def test_ready(client):
    assert client.get("/ready").json() == {"status": "READY"}

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "TaskBoard API"

def test_create_task(client):
    response = client.post("/api/tasks", json={"title": "Deploy application", "priority": "HIGH", "assignee": "Student"})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Deploy application"
    assert body["status"] == "TODO"

def test_create_task_rejects_empty_title(client):
    assert client.post("/api/tasks", json={"title": ""}).status_code == 422

def test_create_task_rejects_unknown_priority(client):
    assert client.post("/api/tasks", json={"title": "x", "priority": "URGENT"}).status_code == 422

def test_list_and_get_task(client):
    created = client.post("/api/tasks", json={"title": "Write tests"}).json()
    assert [t["id"] for t in client.get("/api/tasks").json()] == [created["id"]]
    assert client.get(f"/api/tasks/{created['id']}").json()["title"] == "Write tests"

def test_get_missing_task_returns_404(client):
    assert client.get("/api/tasks/9999").status_code == 404

def test_update_task(client):
    created = client.post("/api/tasks", json={"title": "Build image"}).json()
    response = client.put(f"/api/tasks/{created['id']}", json={"status": "DONE"})
    assert response.status_code == 200
    assert response.json()["status"] == "DONE"
    assert response.json()["title"] == "Build image"

def test_delete_task(client):
    created = client.post("/api/tasks", json={"title": "Temporary"}).json()
    assert client.delete(f"/api/tasks/{created['id']}").status_code == 204
    assert client.get(f"/api/tasks/{created['id']}").status_code == 404

def test_stats(client):
    for status in ["TODO", "TODO", "IN_PROGRESS", "DONE"]:
        client.post("/api/tasks", json={"title": status, "status": status})
    assert client.get("/api/tasks/stats").json() == {"total": 4, "todo": 2, "inProgress": 1, "done": 1}

def test_metrics_exposed(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
