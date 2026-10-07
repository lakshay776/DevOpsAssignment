# Session 19: Cloud and Terraform

Cloud basics on AWS, then Terraform to build a small network and app stack. The homework
write-up, with the architecture diagram and screenshots, is in [Homework.md](Homework.md).

| Folder | Topic |
|---|---|
| [`01-cloud-service-models/`](01-cloud-service-models/) | IaaS, PaaS and SaaS: what you manage vs what the provider manages |
| [`02-regions-and-availability-zones/`](02-regions-and-availability-zones/) | Regions, Availability Zones and why spreading across AZs matters |
| [`03-vpc-and-subnets/`](03-vpc-and-subnets/) | VPC CIDR ranges, public vs private subnets |
| [`04-route-tables-and-internet-gateway/`](04-route-tables-and-internet-gateway/) | Route tables, the Internet Gateway and the `0.0.0.0/0` route |
| [`05-security-groups/`](05-security-groups/) | Security groups as stateful instance firewalls |
| [`06-terraform-vpc/`](06-terraform-vpc/) | Terraform lab: VPC, subnet, IGW, route table, association and security group |
| [`07-terraform-workflow/`](07-terraform-workflow/) | `init`, `validate`, `plan`, `apply`, `destroy` |
| [`08-mini-project/`](08-mini-project/) | Mini project: VPC plus an EC2 web server and an S3 bucket |

Screenshots of the init/plan, apply, outputs, AWS verification and destroy steps are in
`screenshots/`.
