variable "region" {
  description = "AWS region to build in."
  type        = string
  default     = "eu-north-1"
}

variable "aws_profile" {
  description = "Local AWS CLI profile. Left empty in CI, where credentials come from the environment."
  type        = string
  default     = null
}

variable "project" {
  description = "Name prefix for every resource."
  type        = string
  default     = "campusdesk"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS control plane."
  type        = string
  default     = "1.31"
}

variable "node_instance_type" {
  description = "Instance type for the worker node group. t3.small is the cheapest that comfortably runs the system pods plus this app."
  type        = string
  default     = "t3.small"
}

variable "node_desired_size" {
  description = "Worker nodes to run."
  type        = number
  default     = 2
}
