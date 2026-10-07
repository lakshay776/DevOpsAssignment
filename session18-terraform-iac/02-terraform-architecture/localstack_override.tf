# LocalStack override (not part of the course material).
#
# Terraform merges any file named *_override.tf into the matching blocks of the
# other .tf files in this folder. This one adds settings to the existing
# provider "aws" block (region stays as main.tf/providers.tf sets it), so every
# API call goes to a LocalStack container on this machine instead of real AWS.
# Nothing billable is created. Delete this file to run against a real AWS account.
#
# host.docker.internal is used because Terraform itself ran in the
# hashicorp/terraform Docker image; LocalStack listened on host port 18666.
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
