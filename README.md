# DevOps Coursework

Hands-on notes and code for the DevOps module, one folder per topic. Each folder has its own
README with the commands that were run and their output, plus screenshots where a screenshot
adds something the text does not.

| Folder | Topic |
|---|---|
| `Linux Fundamentals/` | Hard vs soft links, `useradd` vs `adduser`, `journalctl`, command cheat sheet |
| `Shell Scripting/` | `sysinfo.sh`: variables, user input, `mkdir`/`touch`, output redirection |
| `Networking Fundamentals/` | `ping`, `ip`, `ss`, `curl`, `wget`, `nslookup`, `traceroute`, `hostname` |
| `Git and Github/` | `git commit -a` vs `-m`, `git cherry-pick` |
| `Docker Fundamentals/` | Six Hello World containers: Node.js, Python, Java, Apache, React, Nginx |
| `DockerFiles and Images/` | Multi-stage Go build, `scratch` runtime image at ~7 MB |
| `Docker Networks/` | Multi-network containers, host network, bind mounts, overlay networks |
| `Kubernetes Fundamentals/` | kind cluster, control-plane components, Pods, namespaces, `--dry-run` |
| `Kubernetes Pods and Deployments/` | ReplicaSet self-healing, rolling update and rollback, `ImagePullBackOff`, DaemonSet |
| `Kubernetes Networking and Services/` | ClusterIP, NodePort, LoadBalancer, ExternalName, headless, empty endpoints |
| `Kubernetes Ingress ConfigMaps and Secrets/` | ingress-nginx, config and secret injection, path-based routing |

Environment: macOS with Docker Desktop; Linux-only commands were run in Ubuntu 24.04 containers.
The Kubernetes work runs on a local two-node [kind](https://kind.sigs.k8s.io/) cluster defined in
`Kubernetes Fundamentals/kind-cluster.yaml`.

The Docker and Linux folders record their output as screenshots; the Kubernetes folders record it
as text transcripts, which stay searchable and diffable.

## Running the containers

Every folder under `Docker Fundamentals/` is a self-contained image. Build and run any of them
the same way:

```bash
cd "Docker Fundamentals/nodejs-app"
docker build -t hello-node .
docker run --rm -p 3000:3000 hello-node
```

| App | Container port | Runs as |
|---|---|---|
| `nodejs-app` | 3000 | `node` |
| `python-app` | 5000 | `appuser` |
| `java-app` | 8080 | `nobody` |
| `nginx-app` | 80 | root (privileged port) |
| `Apache-app` | 80 | root (privileged port) |
| `React-app` | 80 | root (privileged port) |
| `DockerFiles and Images` | 8080 | UID 65534 |

The shell script runs directly:

```bash
./"Shell Scripting/sysinfo.sh"
```

## Running the Kubernetes work

```bash
kind create cluster --config "Kubernetes Fundamentals/kind-cluster.yaml"
kubectl apply -f "Kubernetes Pods and Deployments/manifests/"
```

Host ports 8088 (Ingress), 30080 (NodePort) and 8443 are mapped into the cluster; 8080-8083 were
left alone because the Docker modules use them. Tear down with
`kind delete cluster --name devops-hw`.

## Implementation notes

Beyond getting each task to run, these are the deliberate choices made along the way:

- **Every Dockerfile is commented.** Each one now explains *why* it is written the way it is:
  layer-cache ordering, why `EXPOSE` does not publish a port, why the `scratch` stage needs a
  numeric UID, why exec-form `CMD` matters for `docker stop`.
- **Containers dropped off root where the port allows it.** The Node, Python and Java images run
  as unprivileged users, and the Go `scratch` image runs as UID 65534. The three images bound to
  port 80 stay on root, since binding a privileged port requires it.
- **`sysinfo.sh` is hardened, not just working.** It uses `#!/usr/bin/env bash` rather than a
  hardcoded interpreter path, `set -euo pipefail` so a failing command stops the run instead of
  leaving variables half-populated, defaults for empty prompt input, and a process count that
  excludes the `ps` header row. The `ps` header is printed separately from the sorted body, so
  it stays at the top of the table instead of being sorted into the middle of the results.
- **Python image logs properly.** Added `PYTHONUNBUFFERED=1`, without which Flask's log lines sit
  in a buffer and never reach `docker logs`.

All seven images were rebuilt and each was curled on its port to confirm it still serves as an
unprivileged user. `sysinfo.sh` was run end to end; its full output is in
`Shell Scripting/README.md`.
