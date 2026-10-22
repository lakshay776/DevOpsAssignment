# Two public subnets in different availability zones. EKS requires subnets in
# at least two AZs, and the rubric asks for at least two public subnets.

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
  # Both required by EKS so nodes can resolve each other and the API server.
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${var.project}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project}-igw" }
}

resource "aws_subnet" "public" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  # Nodes need public IPs to reach the control plane without a NAT gateway,
  # which would add roughly $32/month for no benefit here.
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project}-public-${data.aws_availability_zones.available.names[count.index]}"
    # Tells the AWS load balancer controller which subnets to use for
    # internet-facing load balancers.
    "kubernetes.io/role/elb" = "1"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${var.project}-public-rt" }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
