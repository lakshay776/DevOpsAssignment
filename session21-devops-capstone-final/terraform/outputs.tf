output "cluster_name" {
  description = "EKS cluster name."
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "Kubernetes API server endpoint."
  value       = aws_eks_cluster.main.endpoint
}

output "vpc_id" {
  description = "VPC the cluster runs in."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnets, one per availability zone."
  value       = aws_subnet.public[*].id
}

output "kubeconfig_command" {
  description = "Run this to point kubectl at the new cluster."
  value       = "aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${var.region}"
}
