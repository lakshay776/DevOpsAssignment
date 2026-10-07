# Session 15: Helm

Helm, the package manager for Kubernetes: one chart of templated YAML, different values per
environment, and a release history you can upgrade and roll back.

The source is the `session-15-helm` folder of
[Nency-Ravaliya/devops-heros](https://github.com/Nency-Ravaliya/devops-heros/tree/main/session-15-helm).
Each numbered folder keeps the course's own README with the instructions for that module, and the
course overview is in [INSTRUCTIONS.md](INSTRUCTIONS.md). This file records what was run and what
came out. Every screenshot in `screenshots/` was taken automatically with Playwright: browser pages
were loaded directly, and terminal output was rendered to an image from the exact command and its
output.

Environment: macOS (Apple Silicon), Docker Desktop, Helm v4.3.0, a single-node kind cluster named
`s15` (Kubernetes v1.37.0).

## Differences from the course instructions

| Where | Course says | What was done, and why |
|---|---|---|
| All | Helm 3 (`v3.15.0` in the expected output) | Helm 4.3.0 is installed here. Every command in the course still works. Two differences showed up: `helm create` now also generates `templates/httproute.yaml`, and `--atomic` is deprecated in favour of `--rollback-on-failure` (see 08). |
| 04 | `helm lint my-app/` | The course ships `Chart.yaml` at the root of `04-chart-yaml/`, so `my-app/` didn't exist and lint failed with `stat my-app/Chart.yaml: no such file or directory`. `Chart.yaml` was moved to `04-chart-yaml/my-app/Chart.yaml` and given the `home:` field from section 3. A `templates/configmap.yaml` was added that uses the `.Chart.*` labels from section 6, so the chart has a template to render. |
| 05 | `./chart` | There is no `chart/` folder. The course's chart for this module is `my-app/` (a `helm create` chart), so the commands used `./my-app` with the module's `values-prod.yaml`. That file sets `image.tag: latest`, not the README's `v2.0.0`, which doesn't exist as an nginx tag. It was left as shipped. The `app.name` key in both values files isn't read by the `helm create` templates, so it has no effect. |
| 08 | `helm install rollback-demo ./app-chart` | `app-chart` lives in `07-install-upgrade/`, so 08 was run from there. |
| 09 | `image.tag: "1.24"` | The course's `guestbook-chart/values.yaml` had `tag: "latest"`. It was changed to `"1.24"` to match the README. The chart's templates were already present and matched the README, so nothing had to be built. |
| 09, mini | NodePort 30080 / 30090 | kind doesn't publish NodePorts to the Mac without extra port mappings, so the browser screenshots used `kubectl port-forward` on host ports 18302 and 18303. |
| Images | Pulled by the cluster | To avoid Docker Hub's rate limit on the kind node, the nginx `1.24`, `1.25` and `latest` images and `busybox` were pulled on the host from `public.ecr.aws/docker/library/`, then imported into the node with `docker save \| ctr images import`. `nginx:1.16.0` (the default tag of the `helm create` charts) isn't on that mirror, so it was pulled from Docker Hub on the host. The Bitnami image was pulled by the node itself. |
| Helm repos | `helm repo add` into your Helm config | The `bitnami` repo was added to a Helm config in a scratch folder (`HELM_CONFIG_HOME` and related variables), so the machine's own Helm repo list was left unchanged. |

---

## 01: What is Helm

```bash
helm version
helm list
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install my-nginx bitnami/nginx
```

![version](screenshots/01-version.png)

`helm list` on the empty cluster prints only the header, as the README expects.

![repo](screenshots/01-repo.png)

The install worked. The chart's notes now warn that since August 2025 Bitnami offers only a limited
free set of images and charts. `bitnami/nginx` was still available and ran as `bitnami/nginx:latest`:

![install](screenshots/01-install.png)
![check](screenshots/01-install-check.png)

The Service is `LoadBalancer`, so on kind its external IP stays `<pending>`. A port-forward
(`18300:80`) reached the page:

![bitnami nginx](screenshots/01-nginx-browser.png)

`helm uninstall` removed the Deployment, Service and pod together:

![uninstall](screenshots/01-uninstall.png)

## 02: Helm Charts

`helm create` ran in a scratch folder, so the course's committed `demo-chart/` wasn't overwritten.
It creates a `charts/` directory, which the committed copies don't have, because Git doesn't track
empty folders. Helm 4 also adds `httproute.yaml`, which the README's list doesn't mention.

![create](screenshots/02-create.png)

The rendered YAML starts with the ServiceAccount named `my-release-demo-chart`, as the README
shows:

![template](screenshots/02-template.png)

The course's `demo-chart` is version `0.1.1`, so `helm list` shows `demo-chart-0.1.1` rather than
the README's `0.1.0`. `helm test` also ran the chart's busybox connection test, and it passed:

![install](screenshots/02-install.png)
![uninstall](screenshots/02-uninstall.png)

The second chart in this folder, `myapp`, is another `helm create` output. Both charts lint
cleanly:

![lint](screenshots/02-lint.png)

The `helm test` pod is a hook, and `helm uninstall` didn't delete it (it shows up as
`Completed` in 03's pod list). It was deleted by hand.

## 03: Chart Structure

`{{ .Release.Name }}` became `my-release`, so the Deployment is `my-release-app` and the Service is
`my-release-svc`:

![template](screenshots/03-template.png)
![install](screenshots/03-install.png)

The nginx page through `kubectl port-forward svc/my-release-svc 18301:80`:

![browser](screenshots/03-browser.png)

## 04: Chart.yaml

The chart as shipped, with the README's command:

![before](screenshots/04-lint-before.png)

After moving the file into `my-app/`, lint passes. `helm template` shows the Chart.yaml fields
resolved in the labels: `chart: "my-app-0.1.0"` and `app-version: "1.0"`.

![lint](screenshots/04-lint.png)

The README's error case was reproduced on a scratch copy with the `apiVersion` line deleted:

![lint error](screenshots/04-lint-error.png)

## 05: values.yaml

```bash
helm template my-app ./my-app | grep "replicas:"                     # 1 (values.yaml)
helm template my-app ./my-app --set replicaCount=3 | grep "replicas:" # 3
helm template my-app ./my-app -f values-prod.yaml                    # 5
helm template my-app ./my-app -f values-prod.yaml --set replicaCount=2  # 2
```

![template](screenshots/05-template.png)

The last line shows the priority order: `values.yaml` < `-f file` < `--set`. Installed with
`-f values-prod.yaml`, the release ran 5 pods. An upgrade adding `--set replicaCount=3` brought it
down to 3. `helm get values` lists only the user-supplied values:

![install](screenshots/05-install.png)

## 06: Templates

![template](screenshots/06-template.png)

`replicas: 2` comes from `values.yaml`, and `--set replicaCount=5` changes it to `5`. With
`--set service.enabled=false`, the `{{- if }}` block leaves out the whole Service, and only the
Deployment is rendered:

![values](screenshots/06-values.png)

## 07: Install and Upgrade

![install](screenshots/07-install.png)

`helm upgrade --set replicaCount=3` made revision 2 and scaled the Deployment to three pods:

![upgrade](screenshots/07-upgrade.png)

`install` vs `upgrade` vs `upgrade --install`. `install` refuses a name that's in use, and `upgrade`
refuses a release that doesn't exist. `upgrade --install` handles both cases: it upgraded `web-app`
to revision 3 and installed `new-app` at revision 1. Each revision is stored as a Secret of type
`helm.sh/release.v1`, which is how Helm 3 and later keep release state without Tiller:

![upgrade --install](screenshots/07-upgrade-install.png)
![uninstall](screenshots/07-uninstall.png)

## 08: Rollback

Revision 2 used `nginx:doesnotexist`. The new pod went to `ImagePullBackOff` (the registry answered
`not found`). The README shows only the broken pod, but the old revision-1 pod kept running,
because a rolling update doesn't remove old pods until new ones are ready. Helm still reports
revision 2 as `deployed`, since a plain `helm upgrade` doesn't wait for pods:

![broken](screenshots/08-broken.png)

A line about a leftover `new-app` pod from module 07, still terminating, was trimmed from this
screenshot.

`helm rollback rollback-demo 1` created revision 3, "Rollback to 1", and the history was kept:

![rollback](screenshots/08-rollback.png)

`--atomic --timeout 60s` still works in Helm 4 but prints `Flag --atomic has been deprecated, use
--rollback-on-failure instead`. Helm waited 60 seconds, marked revision 4 `failed`, and rolled back
on its own (revision 5, "Rollback to 3"). The new flag name behaved the same way (revisions 6
and 7). The Deployment ended on `nginx:1.24`:

![atomic](screenshots/08-atomic.png)

## 09: Deploying an Application

The chart's templates were already in the course folder and matched the README. Lint passes, and
the rendered output contains no leftover `{{` (count `0`):

![lint](screenshots/09-lint.png)
![template](screenshots/09-template.png)

The Deployment, NodePort Service (`80:30080`) and ConfigMap were all created. The ConfigMap reaches
the container as environment variables `welcome` and `appName` through `envFrom`:

![install](screenshots/09-install.png)

The page itself is plain nginx, because nothing in the chart reads those variables:

![guestbook](screenshots/09-guestbook-browser.png)

![upgrade](screenshots/09-upgrade.png)

Rolling back to revision 1 brought it down to one pod. `helm uninstall` removed the Deployment,
Service and ConfigMap together:

![rollback](screenshots/09-rollback.png)

## Mini Project: Notes App

The chart files were already in the course folder and matched the README.

![lint](screenshots/mini-01-lint.png)

Rendered with defaults, and with `-f values-prod.yaml` (3 replicas, `nginx:1.25`, `production`):

![template](screenshots/mini-02-template.png)

**Install (development):** 1 pod, `nginx:1.24`, `ENVIRONMENT=development`:

![install](screenshots/mini-03-install.png)

**Upgrade to production values:** 3 pods, `nginx:1.25.5`, `ENVIRONMENT=production`, revision 2:

![upgrade prod](screenshots/mini-04-upgrade-prod.png)

The default page looks the same for both versions, so the screenshots load a missing path
(`/notes`). nginx's 404 page shows the server version, and you can see the change from 1.24.0 to
1.25.5:

| Before upgrade (revision 1) | After upgrade (revision 2) |
|---|---|
| ![](screenshots/mini-03-browser-dev-1.24.png) | ![](screenshots/mini-04-browser-prod-1.25.png) |

**Bad upgrade (step 13).** The course command,
`helm upgrade notes-dev notes-chart --set image.tag=broken-tag-does-not-exist`, doesn't pass
`-f notes-chart/values-prod.yaml`. Helm doesn't reuse earlier values on upgrade, so besides breaking
the image, revision 3 quietly went back to `replicaCount: 1` and `environment: development`. The
Deployment dropped from 3 pods to 1 healthy old pod plus 1 pod in `ImagePullBackOff`. To break only
the image, add `-f notes-chart/values-prod.yaml` or `--reuse-values` to the command.

![bad upgrade](screenshots/mini-05-bad-upgrade.png)

**Rollback to revision 2:** 3 healthy pods on `nginx:1.25`, `production`, recorded as revision 4:

![rollback](screenshots/mini-06-rollback.png)
![after rollback](screenshots/mini-06-browser-after-rollback.png)

**Clean up:** no pods are left, and only the built-in `kubernetes` Service remains:

![cleanup](screenshots/mini-07-cleanup.png)

---

## Interview answers

1. **What is Helm?** The package manager for Kubernetes. It turns a set of manifests into a
   parameterised chart that you install, upgrade, roll back and uninstall as one unit.
2. **Chart vs Release:** a chart is the template package (`notes-chart`). A release is one
   installed instance of it (`notes-dev`), with its own revision history.
3. **values.yaml vs `--set`:** `values.yaml` holds the defaults kept in Git. `-f` files layer
   environment overrides on top, and `--set` wins over both (shown in 05, where it gave
   `replicas: 2`). Use values files for anything that matters, so the configuration can be audited.
   As step 13 of the mini project showed, every upgrade has to pass them again.
4. **What does `--atomic` do?** It makes `helm upgrade` wait for the resources to become ready, and
   rolls back to the last good revision if they don't within `--timeout`. In 08, the failed
   revision 4 was followed automatically by "Rollback to 3". In Helm 4 the flag is
   `--rollback-on-failure`.
5. **Upgrade stuck in `pending-upgrade`:** list the release Secrets with
   `kubectl get secrets -l owner=helm` (as in 07). Delete the Secret for the stuck pending
   revision, or run `helm rollback <release> <last-good-revision>`. Then upgrade again.
6. **Helm 2 vs Helm 3:** Helm 3 removed Tiller and acts with your own kubeconfig permissions. It
   stores release state as Secrets of type `helm.sh/release.v1` in the release namespace, which 07
   shows directly.
