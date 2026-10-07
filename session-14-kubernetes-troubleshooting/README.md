# Session 14: Kubernetes Troubleshooting

How to answer *"my application is not working, why?"* in Kubernetes: `get` → `describe` → events →
`logs` → `exec` → test connectivity → root cause → fix → verify.

The source is the `session-14-kubernetes-troubleshooting` folder of
[Nency-Ravaliya/devops-heros](https://github.com/Nency-Ravaliya/devops-heros/tree/main/session-14-kubernetes-troubleshooting).
The course overview is kept as [INSTRUCTIONS.md](INSTRUCTIONS.md), and each numbered folder keeps
the course's own README with the instructions for that module. This file records what was run and
what came out. Every screenshot in `screenshots/` was rendered automatically (Playwright) from the
exact command and its real output. Long `describe` output was cut down with `sed`/`grep` to the
relevant sections; the filter is visible in each command.

Environment: macOS (Apple Silicon), Docker Desktop, a single-node kind cluster named `s14`
(Kubernetes v1.37.0, 15 CPUs / ~7.7 GiB allocatable).

## Differences from the course instructions

| Where | Course says | What was done, and why |
|---|---|---|
| All modules, images | Pulled by the cluster | To avoid Docker Hub's anonymous rate limit on the kind node, the working images (`nginx:1.27`, `nginx:alpine`, `nginx:1.16.0`, `busybox:1.36`, `python:3.11-alpine`, `postgres:16-alpine`, `curlimages/curl:8.6.0`) were pulled on the host (mostly from `public.ecr.aws/docker/library`, the same official images) and imported into the node with `docker save \| ctr images import`. That is why most events say *already present on machine* instead of *Pulling/Pulled*. The deliberately broken images were **not** preloaded: their failures below are real registry answers (`not found`, `pull access denied`), not rate limits. |
| 02 describe | `kubectl apply -f pod.yaml` | There is no `pod.yaml` in this folder; the manifest is `demo-pod.yaml` (the error is in the screenshot). Used `demo-pod.yaml`. The folder also ships a Helm chart, `demo-chart/`, that the README never mentions; it was installed to practise `describe deployment/service/node`. |
| 09 `service.yaml` | Selector `app: web` (as the README shows) | The shipped file had `selector: app: web-ahsgdf`, which matches no pod, so `web-service` had no endpoints. Diagnosed with `describe service` / `get endpoints` / `--show-labels` and fixed to `app: web`. |
| 09 `dns-test-pod.yaml` | `registry.k8s.io/e2e-test-images/dnsutils:1.3` | That image does not exist (`not found`, screenshot below). The image used in the Kubernetes DNS debugging docs is `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.3`; the file now uses it. |
| 09 step 8 | `kubectl exec dns-test -- wget ...` | `jessie-dnsutils` has `nslookup`/`dig` but no `wget` or `curl` (`executable file not found`). The HTTP test was run from a throwaway `busybox:1.36` pod (`kubectl run http-test --rm -i ...`). |
| 09 `pod.yaml` | (not referenced) | A stray copy of 03's `logs-demo` pod. Not used by the 09 README, left unchanged. |
| Mini-project | No fixed manifest | Added `mini-project/fixed-pod.yaml` (`nginx:1.27`). The selector challenge was done with `sed ... service.yaml \| kubectl apply -f -` so the committed `service.yaml` stays correct. |
| Scenarios | `triage_all.sh` says "Follow the diagnostic guide in README.md" | There is no scenarios README or fix files. Each scenario was diagnosed below and a `fixed.yaml` was added next to each `broken.yaml`. |
| Scenarios 1 and 5 fixes | (none) | A Pod's default `restartPolicy` is `Always`, so a script that finishes with exit 0 is restarted too. With only `DATABASE_URL` added, scenario 1 went `Completed` → `CrashLoopBackOff` (screenshot below). Both fixed manifests keep the process running after it succeeds. |
| Scenario 5 comment | "allocates 200MB" | `range(100)` × 10 MiB is ~1000 MiB, so the fix sizes the limit for that (1200Mi), not 200 MB. Verified with the cgroup's `memory.current` (~1010 MiB). |
| Scenario 4 fix | (none) | The cluster had no `production` namespace and no database. `fixed.yaml` creates `production`, a `postgres-db` Deployment and Service, and the client using `postgres-db.production.svc.cluster.local`. The client checks the TCP port with `nc -z` (Postgres does not speak HTTP) and prints the result instead of hiding it with `curl -s ... \|\| true`. |
| INSTRUCTIONS.md folder list | `08-pending-pod`, `09-service-dns` | The real folder names are `08-pending-pods` and `09-service-dns-troubleshooting`. |

---

## 01: kubectl get

```bash
kubectl apply -f pod.yaml
kubectl get pods / pods -o wide / services / deployments / nodes / all
```

![get](screenshots/01-get.png)

`-o wide` adds the pod IP and node. Watching while the pod is deleted from a second terminal shows
it go `Running` → `Terminating` → `Completed` and disappear:

![get -w](screenshots/01-get-watch.png)

## 02: kubectl describe

`kubectl apply -f pod.yaml` fails because the file is called `demo-pod.yaml`. The describe output
shows labels, IP, the container's image/state/ready, conditions and the events at the bottom:

![describe pod](screenshots/02-describe.png)

The included Helm chart (`helm install demo demo-chart`) gives a Deployment and Service to
describe. It deploys `nginx:1.16.0` (the chart's `appVersion`), with liveness/readiness probes on `/`:

![describe deployment](screenshots/02-describe-deployment.png)

The Service's `Endpoints` line shows the pod IP. The node's conditions and allocated resources
show the node is healthy and nearly empty. `helm test` succeeded:

![describe service and node](screenshots/02-describe-service-node.png)

## 03: kubectl logs

```bash
kubectl logs logs-demo
kubectl logs -f logs-demo
kubectl logs logs-demo --previous
kubectl logs logs-demo -c app
```

![logs](screenshots/03-logs.png)

`--previous` fails here because the container has never restarted. It is useful when a container
has crashed, as in 06.

## 04: kubectl exec

The interactive `bash` session was driven non-interactively (commands piped in), so `ls` prints
one name per line. `curl localhost` from inside returns the nginx page, which proves the app works
before you look at Services or DNS:

![exec](screenshots/04-exec.png)

## 05: Events

Earlier modules' events in `default` were filtered out of the first command so the screenshot stays
readable. `kubectl events --watch` printed the `Killing` event live when the pod was deleted. The
only `Warning` came from module 02: the chart's readiness probe failed while the pod was being
uninstalled.

![events](screenshots/05-events.png)

## 06: CrashLoopBackOff

**Symptom:** `CrashLoopBackOff`, restarts climbing. **Diagnosis:** `describe` shows
`Last State: Terminated, Reason: Error, Exit Code: 1` and `BackOff` events. `logs` and
`logs --previous` show `Something went wrong!`. **Root cause:** the command ends in `exit 1`.

![broken](screenshots/06-crashloop-broken.png)

**Fix:** `fixed-pod.yaml` prints a healthy message and sleeps, so the pod is `Running` with 0 restarts:

![fixed](screenshots/06-crashloop-fixed.png)

On this Kubernetes version `get` sometimes showed `Error` instead of `CrashLoopBackOff` for a few
seconds after each crash, before the kubelet updated the status. `describe` and the events agreed
either way.

## 07: ImagePullBackOff

**Symptom:** `ErrImagePull`, then `ImagePullBackOff`. **Diagnosis:** the events say
`nginx:this-image-does-not-exist: not found` (a real registry answer, not a rate limit).
**Root cause:** the tag does not exist.

![broken](screenshots/07-imagepull-broken.png)

**Fix:** `fixed-pod.yaml` uses `nginx:1.27`:

![fixed](screenshots/07-imagepull-fixed.png)

## 08: Pending pods

**Symptom:** `Pending`, `NODE <none>`, `PodScheduled False`. **Diagnosis:** a `FailedScheduling`
event: `0/1 nodes are available: 1 node(s) didn't match Pod's node affinity/selector`.
**Root cause:** the pod asks for `kubernetes.io/hostname=node-that-does-not-exist`, while the only
node is `s14-control-plane`.

![broken](screenshots/08-pending-broken.png)

**Fix:** `fixed-pod.yaml` drops the nodeSelector, and the pod is scheduled immediately:

![fixed](screenshots/08-pending-fixed.png)

## 09: Service and DNS troubleshooting

**Service as shipped.** The pods are healthy, but `web-service` has empty `Endpoints`. The pods are
labelled `app=web` while the Service selects `app=web-ahsgdf`:

![service broken](screenshots/09-service-broken.png)

**DNS test pod as shipped.** Its image does not exist. The fix was to switch to `jessie-dnsutils:1.3`:

![dns-test image](screenshots/09-dns-test-image.png)

**Service fixed** (selector `app: web`). Both pod IPs appear as endpoints:

![service fixed](screenshots/09-service-fixed.png)

**DNS and HTTP.** `web-service` and `web-service.default.svc.cluster.local` resolve to the
ClusterIP through CoreDNS (`10.96.0.10`). `resolv.conf` shows the search domains that make the
short name work. `wget` is missing from the dnsutils image, so the HTTP test ran from busybox and
returned the nginx page:

![dns and http](screenshots/09-dns-http.png)

**broken-service.** It resolves in DNS but has `<none>` endpoints (selector `app=does-not-exist`),
so `wget` gets `Connection refused`. This is the module's step 17: DNS works, so the problem is the
selector, not DNS. Deleting it leaves `web-service` working:

![broken service](screenshots/09-broken-service.png)

**CoreDNS.** Both pods are Running behind the `kube-dns` Service (`10.96.0.10`), and the logs show no errors:

![coredns](screenshots/09-coredns.png)

## Mini-project: troubleshooting challenge

Deploy, then check the pods, Service and endpoints. `curl localhost` inside a pod works, and the
Service has both pod IPs:

![deploy](screenshots/mp-1-deploy.png)

**Broken pod.** `ImagePullBackOff`. The events say `nginx:this-tag-does-not-exist: not found`:

![broken pod](screenshots/mp-2-broken-pod.png)
![fixed pod](screenshots/mp-3-pod-fixed.png)

**Service selector challenge.** With the selector changed to `app: wrong-app`, the endpoints are `<none>` and
HTTP to the Service is refused. `--show-labels` shows `app=troubleshooting-app` on the pods.
Re-applying the correct `service.yaml` restores the endpoints, the nginx page, and DNS:

![service broken](screenshots/mp-4-service-broken.png)
![service fixed](screenshots/mp-5-service-fixed.png)

**Section 7 answers (broken pod)**

1. **Status:** `ErrImagePull`, then `ImagePullBackOff` (0/1 ready).
2. **Actual error:** `failed to resolve reference "docker.io/library/nginx:this-tag-does-not-exist": ... not found`.
3. **Command:** `kubectl describe pod project-broken-pod`, in the Events section.
4. **What's wrong with the image:** the repository `nginx` exists, but the tag `this-tag-does-not-exist` does not.
5. **Fix:** use a real tag (`nginx:1.27`), delete the pod and re-apply it (`fixed-pod.yaml`), as
   the course does in 06–08. A container's `image` is one of the few Pod fields that can be changed
   in place, so applying the fix without deleting the pod would also have worked. In a real app the
   pod would come from a Deployment, and you would fix the Deployment's image.

**Section 11 troubleshooting table**

| Problem | What I Saw | Command I Used | Root Cause | Fix |
| :--- | :--- | :--- | :--- | :--- |
| **Broken Pod** | `project-broken-pod` 0/1 `ImagePullBackOff` | `kubectl get pod`, `kubectl describe pod` (Events) | Image tag does not exist | `fixed-pod.yaml` with `nginx:1.27` |
| **Service Problem** | Service exists but `ENDPOINTS <none>`, wget `Connection refused` | `kubectl get endpoints`, `kubectl get pods --show-labels`, `kubectl describe service` | Selector `app=wrong-app` matches no pod (pods are `app=troubleshooting-app`) | Re-apply `service.yaml` with `app: troubleshooting-app` |
| **Image Problem** | `Failed to pull image ... not found` in Events | `kubectl describe pod` | Wrong image reference (`nginx:this-tag-does-not-exist`) | Correct the tag, recreate the pod |

## Scenarios: triage gauntlet

`triage_all.sh` deploys five broken pods. Five seconds later: `Error` (crash), `ErrImagePull`,
`Pending`, `Running` (the DNS failure is silent), and `OOMKilled`:

![triage](screenshots/scenarios-0-triage-broken.png)

### Scenario 1: CrashLoopBackOff (missing env var)

`describe` shows `Exit Code: 1` and `Environment: <none>`. `logs --previous` prints
`[FATAL ERROR]: DATABASE_URL environment variable is MISSING!`.

![broken](screenshots/scenario-1-crashloop-broken.png)

Adding only `DATABASE_URL` was not enough. The script then exits 0, and with `restartPolicy: Always`
the pod still ends up in `CrashLoopBackOff` (Last State `Completed`, exit code 0):

![env only](screenshots/scenario-1-env-only.png)

`fixed.yaml` sets `DATABASE_URL` and keeps the app running after it starts:

![fixed](screenshots/scenario-1-crashloop-fixed.png)

### Scenario 2: ImagePullBackOff (bad image name)

The events say `pull access denied, repository does not exist or may require authorization` for
`docker.io/library/yatri-api-service`. Checking from the host confirms the repository isn't public.
That message means either a typo or a private registry, and here the repository simply does not exist.

![broken](screenshots/scenario-2-imagepull-broken.png)

`fixed.yaml` points at an image that exists (`nginx:alpine` stands in for the app):

![fixed](screenshots/scenario-2-imagepull-fixed.png)

### Scenario 3: Pending (impossible resource requests)

The pod requests `cpu: 500`, `memory: 1000Gi`. The `FailedScheduling` event says
`1 Insufficient cpu, 1 Insufficient memory`, and the node only has 15 CPUs and ~7.7 GiB allocatable.

![broken](screenshots/scenario-3-pending-broken.png)

`fixed.yaml` requests `100m` CPU / `64Mi` (limit `128Mi`), and the pod is scheduled at once:

![fixed](screenshots/scenario-3-pending-fixed.png)

### Scenario 4: DNS failure (wrong hostname)

The pod is `Running` and its logs look fine, because `curl -s ... || true` hides the error. Running
the same curl with `kubectl exec` shows `curl: (6) Could not resolve host`, and `nslookup` gives
`NXDOMAIN`. The `production` namespace doesn't exist and there is no postgres Service anywhere.
DNS itself is healthy: `kubernetes.default` resolves and CoreDNS is Running. So the hostname is the
problem, not CoreDNS.

![broken](screenshots/scenario-4-dns-broken.png)

`fixed.yaml` creates the `postgres-db` Service in `production` and uses its real name. The client
logs `Database reachable at postgres-db.production.svc.cluster.local:5432`:

![fixed](screenshots/scenario-4-dns-fixed.png)

### Scenario 5: OOMKilled

`describe` shows `Last State: Terminated, Reason: OOMKilled, Exit Code: 137` with
`Limits: memory: 20Mi`. `logs --previous` is empty: the process was killed before its buffered
`print` was flushed, which is typical for OOM kills. Describe, not logs, is where this shows up.

![broken](screenshots/scenario-5-oomkilled-broken.png)

`fixed.yaml` sets the request/limit to `1100Mi`/`1200Mi`. The app allocates its ~1000 MiB and keeps
running, with cgroup `memory.current` ≈ 1010 MiB against `memory.max` = 1200 MiB:

![fixed](screenshots/scenario-5-oomkilled-fixed.png)

All five fixed:

![all fixed](screenshots/scenarios-all-fixed.png)

---

## README questions (mini-project section 12)

1. **What does `kubectl get` tell us?** The current state of resources at a glance: what exists,
   STATUS, READY, RESTARTS and AGE. It tells you *what* is happening, not why.
2. **`get` vs `describe`?** `get` is a one-line summary per object. `describe` is the detailed view
   of one object: spec, container state and last state, exit codes, conditions, and the related
   events. That is usually where the *why* is.
3. **Why `kubectl logs`?** To see what the application itself printed (stdout/stderr), such as the
   `DATABASE_URL ... MISSING` error in scenario 1. Use `--previous` for the container that just crashed.
4. **When `kubectl exec`?** When the container is running and you need to check from inside:
   `curl localhost`, configuration files, `nslookup`, connectivity to another service (scenario 4).
   It doesn't help when the container keeps crashing.
5. **CrashLoopBackOff?** The container starts and then exits, again and again, and the kubelet waits
   longer between restarts each time. It is a symptom. The cause is in the exit code, the logs and
   the events. Exit 0 counts too when `restartPolicy` is `Always`.
6. **ImagePullBackOff?** The kubelet could not pull the image (wrong name or tag, private registry
   without credentials, registry or network problem) and is backing off between retries.
7. **Why Pending?** The scheduler can't place the pod: no node matches its nodeSelector or affinity
   (08), requests are larger than any node's free capacity (scenario 3), taints without
   tolerations, or an unbound PVC. The `FailedScheduling` event says which.
8. **Why can a Service have no endpoints?** Its selector matches no Ready pod: wrong labels (09,
   mini-project), pods not running or not Ready, or pods in a different namespace.
9. **Selector vs labels?** A Service sends traffic to the pods whose labels match its selector. The
   matching pods' IPs become its endpoints (EndpointSlices). If they don't match, the Service exists
   but routes nowhere.
10. **What is Kubernetes DNS?** CoreDNS, running in `kube-system` behind the `kube-dns` Service
    (`10.96.0.10` here), gives every Service a name, `<service>.<namespace>.svc.cluster.local`. Pods
    get it as their nameserver in `/etc/resolv.conf`, along with search domains, so `web-service`
    resolves from the same namespace.
