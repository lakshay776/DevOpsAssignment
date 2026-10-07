# Session 20: Monitoring, Observability and GitOps

Prometheus and Grafana for metrics, then GitOps with Argo CD: Git holds the desired state, and a
controller keeps the cluster matching it.

The source is the `session20-monitoring-observability-gitops` folder of
[Nency-Ravaliya/devops-heros](https://github.com/Nency-Ravaliya/devops-heros/tree/main/session20-monitoring-observability-gitops).
Each numbered folder keeps the course's own README with the instructions for that module. This
file records what was run and what came out. Every screenshot in `screenshots/` was taken
automatically with Playwright: browser pages were driven directly, and terminal output was
rendered to an image from the exact command and its output.

Environment: macOS, Docker Desktop, a single-node kind cluster named `session20`.

## Differences from the course instructions

| Where | Course says | What was done, and why |
|---|---|---|
| 04 Grafana | `http://localhost:3000` | Port 3000 is taken by VS Code on this machine, so `docker-compose.yml` reads `${GRAFANA_PORT:-3000}` and this run used `GRAFANA_PORT=3003`. The default is unchanged. |
| 07, 08 Git remote | Push to a GitHub repository | A local [Gitea](https://about.gitea.com/) server ran as a container on kind's Docker network, so pods reached it at `http://gitea:3000`. Argo CD watched it exactly as it would watch GitHub, and nothing was published. `argocd-application.yaml` in both folders points at the Gitea repos. |
| 07 Argo CD UI | `port-forward ... 8080:443` | 8080 is also taken by VS Code, so the UI ran on `8085:443`. |
| 02, 05 images | Pulled by the cluster | The kind node hit Docker Hub's anonymous rate limit (`429 Too Many Requests`). `busybox:1.36` and `nginx:1.27-alpine` were imported from the host's Docker cache with `docker save --platform linux/arm64 ... \| ctr images import`. `kind load docker-image` failed with `content digest not found`, a known problem with multi-arch images. |

---

## 01: Monitoring vs Observability

This module is concepts only, so it has no commands. Monitoring answers *is something wrong?*
from known signals such as dashboards and alerts. Observability answers *why?* by exploring
metrics, logs and traces together.

## 02: Metrics, Logs and Traces

```bash
kind create cluster --name session20
kubectl apply -f k8s-demo/
```

![cluster](screenshots/02-cluster.png)

The demo pod is a busybox loop that writes log lines, and `kubectl logs` reads them back. Logs
tell you *what happened*.

![k8s demo](screenshots/02-k8s-demo.png)

The demo Service targets port 8080, but busybox listens on nothing, so the Service has no
working backend. That's harmless here, since the module only uses the logs.

![cleanup](screenshots/02-cleanup.png)

## 03: Prometheus

![compose](screenshots/03-compose.png)

`up` returns `up{instance="prometheus:9090", job="prometheus"} 1`, the result the module expects.
`1` means the last scrape of that target succeeded.

![up](screenshots/03-query-up.png)

| `prometheus_http_requests_total` | `sum(up)` |
|---|---|
| ![](screenshots/03-query-http-requests.png) | ![](screenshots/03-query-sum-up.png) |

`rate(process_cpu_seconds_total[1m])` as a graph, and the target list. Prometheus is
scraping itself:

| CPU rate graph | Targets |
|---|---|
| ![](screenshots/03-query-cpu-graph.png) | ![](screenshots/03-targets.png) |

`/metrics` is the plain-text format Prometheus scrapes:

![metrics endpoint](screenshots/03-metrics-endpoint.png)

**Practice answers.** Prometheus collects metrics. A scrape is one HTTP GET of a target's
`/metrics`. `up` is target health (1 = the last scrape worked). PromQL is its query language.
Prometheus is a metrics system, not log storage.

## 04: Grafana

```bash
GRAFANA_PORT=3003 docker compose up -d
```

![compose](screenshots/04-compose.png)

Everything below was done through the Grafana UI, not the API:

| Log in as admin/admin | Password-change prompt (skipped for the lab) |
|---|---|
| ![](screenshots/04-01-login.png) | ![](screenshots/04-02-change-password-prompt.png) |

Connections → Data sources → Add → Prometheus, with URL `http://prometheus:9090`. That's the
Compose service name, because Grafana runs in its own container, where `localhost` would be
Grafana itself.

| Add data source | URL set |
|---|---|
| ![](screenshots/04-03-add-data-source.png) | ![](screenshots/04-04-data-source-url.png) |

**Save & test** reports *Successfully queried the Prometheus API*:

![save and test](screenshots/04-05-save-and-test.png)

New dashboard → Add visualization → Prometheus → query `up` → Stat panel:

| Pick data source | Panel editor |
|---|---|
| ![](screenshots/04-06-select-data-source.png) | ![](screenshots/04-07-stat-panel-editor.png) |

The saved dashboard shows `1`, meaning the target is up:

![dashboard](screenshots/04-08-dashboard.png)

## 05: Introduction to GitOps

The Deployment was applied by hand once, to see the starting point that GitOps replaces:

![apply](screenshots/05-apply.png)

## 06: Git as Source of Truth

The commands ran in a scratch copy of `gitops-repo/`, so this coursework repo doesn't end up with
a nested `.git` inside it. The second commit changes the desired state from 2 replicas to 3, and
the log records who changed what:

![git](screenshots/06-git.png)

## 07: Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

![install](screenshots/07-install.png)

`app/deployment.yaml` and `app/service.yaml` were pushed to the Gitea repo `gitops-demo`. The
Application, the one manual step, was applied from outside that path:

![register](screenshots/07-register.png)
![verify](screenshots/07-verify.png)

| Argo CD login | Applications |
|---|---|
| ![](screenshots/07-01-argocd-login.png) | ![](screenshots/07-01-argocd-applications.png) |

The resource tree shows Synced and Healthy at commit `e2e9b61`, with 5 pods:

![tree](screenshots/07-01-argocd-app-tree.png)

The app itself, through `kubectl port-forward svc/session20-gitops-app -n session20 9090:80`:

![nginx](screenshots/07-01-nginx-app.png)

### Scaling by committing to Git

No `kubectl scale` was used. Only a commit and a push:

![scale down](screenshots/07-scale-down.png)
![scale up](screenshots/07-scale-up.png)

The course README says the change arrives "within ~30 seconds", but here each one took 3–5
minutes (294 s and 198 s). Argo CD *polls* the repo every 3 minutes by default, and then it
syncs. A webhook from the Git server would make it near-instant.

| Commit history in Git | Tree after the last push (3 pods) |
|---|---|
| ![](screenshots/07-gitea-commits.png) | ![](screenshots/07-02-after-scale-up-argocd-app-tree.png) |

### Cleanup, and a correction

The course README says deleting the Application "also removes your app from the cluster". It
doesn't: without the `resources-finalizer.argocd.argoproj.io` finalizer on the Application, Argo
CD deletes only its own record and leaves the workload running. The namespace had to be deleted
separately:

![cleanup](screenshots/07-cleanup.png)

## 08: Mini Project

Namespace, Deployment (2 replicas), Service and Argo CD Application. The workload manifests live
in the Gitea repo `session20-mini`, and the Application stays outside it.

![cluster](screenshots/08-cluster.png)
![repo](screenshots/08-repo.png)
![apply](screenshots/08-apply.png)

**Step 7.** A change in Git (replicas 2 → 3) reached the cluster about 4 minutes after the push:

![git change](screenshots/08-git-change.png)

| Desired state in Git | Commit history |
|---|---|
| ![](screenshots/08-gitea-desired-state.png) | ![](screenshots/08-gitea-commits.png) |

**Step 8: self-healing.** `kubectl scale --replicas=1` dropped the Deployment to 1/1, and within
the same second Argo CD set it back to 3. With `selfHeal: true`, a change to a live object it
manages triggers an immediate comparison with Git, with no waiting for the poll. The events show
the round trip: 3 → 1 → 3.

![self heal](screenshots/08-self-heal.png)

**Step 9: observing the system:**

![observe](screenshots/08-observe.png)

| Applications | Resource tree |
|---|---|
| ![](screenshots/08-argocd-applications.png) | ![](screenshots/08-argocd-app-tree.png) |

![cleanup](screenshots/08-cleanup.png)

---

## Viva answers

1. **Monitoring vs observability:** monitoring checks known signals to say *whether* something is
   wrong. Observability lets you investigate *why*, including problems nobody predicted.
2. **Metrics vs logs vs traces:** metrics are numbers over time (how much, how often). Logs are
   individual events (what happened). Traces follow one request across services (where the time
   went).
3. **Prometheus:** a time-series database that pulls (scrapes) metrics from targets' `/metrics`
   endpoints and answers PromQL queries.
4. **Grafana:** a visualization layer that queries data sources such as Prometheus and draws
   dashboards. It stores no metrics itself.
5. **GitOps:** running deployments by changing Git. A controller applies whatever Git says,
   instead of people running `kubectl` against the cluster.
6. **Git as source of truth:** Git is the one authoritative description of the system, with
   history, review, diffs, authorship and a point to roll back to.
7. **Argo CD:** a Kubernetes controller that watches a Git repo, compares it with the cluster and
   applies the difference.
8. **Desired state:** what Git declares, for example `replicas: 3`.
9. **Actual state:** what is running in the cluster right now.
10. **Reconciliation:** the loop of comparing desired and actual state and acting to close the
    gap.
11. **Self-healing:** Argo CD reverts manual changes to the objects it manages, as in step 8,
    where `kubectl scale` to 1 was undone within a second.
12. **Changing replicas from 2 to 3 in Git:** on its next poll Argo CD sees the new commit, marks
    the app OutOfSync, applies the new Deployment spec, and the ReplicaSet creates the third pod.
