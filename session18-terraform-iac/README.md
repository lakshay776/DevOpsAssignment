# Session 18: Terraform & Infrastructure as Code

Terraform basics with the AWS provider: write HCL, then `init`, `plan`, `apply`, read outputs and
state, and `destroy`. Every module creates one S3 bucket.

The source is the `session18-terraform-iac` folder of
[Nency-Ravaliya/devops-heros](https://github.com/Nency-Ravaliya/devops-heros/tree/main/session18-terraform-iac).
Each numbered folder keeps the course's own README with the instructions for that module, and the
course's root README is kept as `INSTRUCTIONS.md`. This file records what was run and what came out.
Every screenshot in `screenshots/` was rendered automatically from a transcript of the exact
command and its real output. Long plans are trimmed to the resource header and the `Plan:` line,
and the screenshot says so where that happened.

Environment: macOS, Docker Desktop, Terraform v1.9.8 (`hashicorp/terraform:1.9` image), AWS
provider v6.67.0 (v6.66.0 in `terraform-s3-demo`, pinned by its lock file), LocalStack 4.14.0
community edition, AWS CLI v2.

> **No real AWS resources were created.** All buckets were created in
> [LocalStack](https://github.com/localstack/localstack), a local AWS emulator running in a Docker
> container. Account IDs such as `000000000000` and the `test` credentials are LocalStack's.

## Differences from the course instructions

| Where | Course says | What was done, and why |
|---|---|---|
| All modules | Run against AWS after `aws configure` | There are no AWS credentials on this machine, and the lab must not create billable resources, so every module ran against LocalStack on host port `18666`. |
| All modules | Only `main.tf` | Each folder has an extra `localstack_override.tf`. Terraform merges any `*_override.tf` file into the matching blocks of the other files, so it adds dummy credentials, `skip_*` checks, `s3_use_path_style` and `endpoints { s3, sts, iam, ec2, dynamodb }` to the existing `provider "aws"` block. The course's `main.tf` was left alone, and the region still comes from `main.tf`. To run against real AWS, delete the override file. |
| All modules | `terraform` installed locally | Terraform ran from the `hashicorp/terraform:1.9` Docker image. `--network host` could not reach host ports on Docker Desktop for Mac (`Connection refused`), so the override endpoints use `http://host.docker.internal:18666`. Transcripts show the command as `terraform <cmd>`. |
| LocalStack version | n/a | `localstack/localstack:latest` (2026.9.1) exited at once with `License activation failed ... set the LOCALSTACK_AUTH_TOKEN`. The community image is pinned to `4.14`. The first try used `4.9`, which silently dropped the tags that AWS provider v6 sends inside `CreateBucket` (`GetBucketTagging => 404 NoSuchTagSet`), so every refresh would have shown tag drift. `4.14` stores them correctly. |
| Apply / destroy | Type `yes` at the prompt | `-auto-approve` was used, and the plan is still printed before the change. |
| `aws` CLI checks | `aws s3 ls`, `aws sts get-caller-identity` | Run with `--endpoint-url http://localhost:18666` and `test` credentials, so they query LocalStack. |
| `terraform-s3-demo/outputs.tf` | `type = string` in each `output` block | **Bug fix.** `output` blocks don't accept `type`, so `terraform init` itself failed with `An argument named "type" is not expected here`. The three `type` lines were removed. |
| `terraform-s3-demo` README | `terraform state show aws_s3_bucket.demo` | The resource is named `aws_s3_bucket.devops553` in `main.tf`, so the README's address fails with `No instance found`. Both are shown below. |
| `terraform-s3-demo` README | Lists a `terraform.tfvars` | No such file is provided, and `.gitignore` excludes `*.tfvars`. A local one set `bucket_name = "session18-s3-demo-lakshay"`, replacing the default `yatri1107`. It was deleted afterwards and is not committed. |
| `terraform-s3-demo/.gitignore` | Ignores `*_override.tf` | Added `!localstack_override.tf`, so the override that documents this run is committed. |
| `07-init-plan-apply/.gitignore` | Ignores `*.tfplan` | The README saves the plan as `tfplan` (no extension), which that pattern doesn't match. Added `tfplan`. |
| 04, 06, 09 `main.tf` | Exercises | The exercise edits were kept: 04 adds `Project` and `Owner` tags, 06 adds the `bucket_name` output, and 09 changes the `Name` tag. |
| Lock files, state | n/a | All buckets were destroyed. `.terraform/`, `terraform.tfstate*`, `terraform.tfvars` and the lock files that `init` generated in 01–09 were removed afterwards. The course ships no lock files there. `terraform-s3-demo/.terraform.lock.hcl` was restored to the course version, because `init` had added a `linux_arm64` hash for the Docker image. |

The override file used in every folder:

```hcl
provider "aws" {
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3       = "http://host.docker.internal:18666"
    sts      = "http://host.docker.internal:18666"
    iam      = "http://host.docker.internal:18666"
    ec2      = "http://host.docker.internal:18666"
    dynamodb = "http://host.docker.internal:18666"
  }
}
```

LocalStack was started with:

```bash
docker run -d --name s18-localstack -p 18666:4566 localstack/localstack:4.14
curl -s localhost:18666/_localstack/health   # "edition": "community", "version": "4.14.0"
```

---

## 01: What is Infrastructure as Code?

```bash
terraform init && terraform fmt && terraform validate
terraform plan
terraform apply
terraform output bucket_name && terraform state list
terraform destroy
```

![init](screenshots/01-init.png)
![plan](screenshots/01-plan.png)

`bucket_prefix = "session18-iac-"` lets Terraform generate a unique name, as the README says it
will.

![apply](screenshots/01-apply.png)
![verify](screenshots/01-verify.png)

After `destroy`, both `state list` and `aws s3 ls` come back empty:

![destroy](screenshots/01-destroy.png)

**Practice answers.**
1. *Ten engineers creating the same infrastructure by hand* end up with ten slightly different
   results: different names, settings and tags, and nobody has a record of who changed what. This is
   configuration drift, and it can't be reviewed or reproduced.
2. *Git* gives infrastructure the same workflow as code: history, diffs, pull-request review,
   blame, and the option to revert to a known-good version.
3. *The same infrastructure in another environment* is a re-run of the same code with different
   variables (see module 05) or a different workspace or state, not a second round of console
   clicking.

## 02: Terraform Architecture

![init](screenshots/02-init.png)
![apply](screenshots/02-apply.png)

`terraform state list` and `terraform show` read back what Terraform recorded in
`terraform.tfstate`, which is the "State" box in the module's diagram:

![inspect](screenshots/02-inspect.png)
![destroy](screenshots/02-destroy.png)

Terraform is declarative: the configuration only says "one bucket with this prefix and tag", and the
AWS provider worked out the API calls (`CreateBucket`, then a series of `GetBucket*` reads).

## 03: Providers

`terraform init` read `source = "hashicorp/aws"` and `version = "~> 6.0"`, then downloaded the
newest matching release, v6.67.0. `terraform providers` shows the requirement tree:

![providers init](screenshots/03-providers-init.png)

The README's authentication check, `aws sts get-caller-identity`, answered by LocalStack:

![sts](screenshots/03-sts.png)
![apply](screenshots/03-apply.png)
![destroy](screenshots/03-destroy.png)

The course warns against putting keys in the provider block. The override file does contain
`access_key = "test"`, but those are LocalStack's fixed dummy values, not secrets. With real AWS,
credentials belong in `aws configure`, environment variables or an IAM role.

## 04: Resources

![apply](screenshots/04-apply.png)
![inspect](screenshots/04-inspect.png)

**Exercise.** The `Project` and `Owner` tags were added to `main.tf`. `terraform fmt` realigned the
`=` signs (it printed `main.tf`), and `plan` shows an **in-place update**: tags can change without
replacing the bucket.

![exercise](screenshots/04-exercise.png)
![destroy](screenshots/04-destroy.png)

## 05: Variables

```bash
cp terraform.tfvars.example terraform.tfvars
terraform init && terraform fmt && terraform validate && terraform plan
```

![tfvars](screenshots/05-tfvars.png)

The plan builds the bucket prefix from the variables: `student-project-dev-`. The `project_name`
from `terraform.tfvars` replaced the `terraform-training` default in `main.tf`.

![plan dev](screenshots/05-plan-dev.png)

**Exercise.** Changing `environment` to `test` changes the prefix and the tag. A `-var` on the
command line takes precedence over the file:

![plan test](screenshots/05-plan-test.png)

This module only asks for `plan`, so nothing was applied. `terraform.tfvars` is gitignored and was
deleted afterwards.

**Practice answer.** Terraform evaluates the configuration with the variable values filled in, so a
different `environment` produces a different desired state (prefix `student-project-test-` and tag
`Environment = "test"`). `plan` compares that new desired state with state and the real world, and
proposes whatever change closes the gap. The code stayed the same, but its input changed.

## 06: Outputs

![apply](screenshots/06-apply.png)

`terraform output` prints all of them. `terraform output bucket_id` prints one as a quoted value,
and `-raw` drops the quotes so scripts can use it:

![output](screenshots/06-output.png)

**Exercise.** After the `bucket_name` output was added, `apply` reported `0 added, 0 changed, 0
destroyed`. Adding an output changes only state, not infrastructure.

![exercise](screenshots/06-exercise.png)

`bucket_region` is a hardcoded string (`"ap-south-1"`) in the course code. `aws_s3_bucket.demo.region`
would read it from the resource instead.

## 07: Init, Plan and Apply

![init](screenshots/07-init.png)
![plan](screenshots/07-plan.png)

**Saved plan.** `terraform plan -out=tfplan` followed by `terraform apply tfplan` applies exactly
the reviewed plan, with no new plan and no prompt:

![saved plan](screenshots/07-saved-plan.png)

`output` and `state list` complete the student exercise. A second `plan` reports **No changes**,
because configuration, state and LocalStack all agree:

![apply](screenshots/07-apply.png)

## 08: Destroy

A bucket was created first, so there was something to destroy:

![setup](screenshots/08-setup.png)

`terraform plan -destroy` previews the deletion without doing it:

![plan destroy](screenshots/08-plan-destroy.png)
![destroy](screenshots/08-destroy.png)

**Practice answers.**
1. *`plan` vs `apply`:* `plan` is read-only and shows what would change. `apply` makes the change,
   either from a new plan after confirmation or from a saved plan file.
2. *`destroy`* deletes every resource tracked in this configuration's state. It is
   `apply -destroy`: a destroy-mode plan followed by approval.
3. *`plan -destroy` first:* it lists exactly what would be deleted with no risk. In production it
   catches a wrong workspace, wrong state or wrong account, or shared resources, before anything
   unrecoverable happens.

## 09: State

![apply](screenshots/09-apply.png)
![state](screenshots/09-state.png)

`terraform state pull` prints the raw JSON state, with resource addresses, every attribute, the
`serial` and the `lineage`:

![state pull](screenshots/09-pull.png)

**Exercise.** The `Name` tag was changed to `Session 18 State Demo - updated`. `plan` showed a `~`
in-place update, and after `apply` the AWS CLI confirms the new tag on the bucket:

![change](screenshots/09-change.png)
![show](screenshots/09-show.png)

After `destroy`, `state list` is empty. `terraform.tfstate` still exists as an empty state file,
and `.gitignore` keeps it out of Git:

![destroy](screenshots/09-destroy.png)

## Terraform S3 Demo

The course's `outputs.tf` broke `init` before anything else could run:

![init error](screenshots/s3-demo-init-error.png)

After the three `type = string` lines were removed, `init` reused v6.66.0 from the committed lock
file, and `validate` passed:

![init](screenshots/s3-demo-init.png)
![apply](screenshots/s3-demo-apply.png)

`state show aws_s3_bucket.demo` (as written in the README) fails, because the resource is
`devops553`:

![state](screenshots/s3-demo-state.png)

`aws s3 ls`, `head-bucket` and `get-bucket-tagging` against LocalStack show the bucket with all four
tags from `main.tf`:

![verify](screenshots/s3-demo-verify.png)
![destroy](screenshots/s3-demo-destroy.png)

`force_destroy = true` in `main.tf` lets `destroy` delete the bucket even if it holds objects.
Without it, deleting a non-empty bucket fails.
