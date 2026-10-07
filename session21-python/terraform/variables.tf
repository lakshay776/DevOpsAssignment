variable "aws_region" {
  description = "AWS region for the VPC and EKS cluster"
  type        = string
  default     = "ap-south-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "taskboard-eks"
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "dev"
}
