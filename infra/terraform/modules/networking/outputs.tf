output "vpc_id" {
  description = "ID of the VPC."
  value       = aws_vpc.this.id
}

output "vpc_cidr_block" {
  description = "Primary CIDR block of the VPC."
  value       = aws_vpc.this.cidr_block
}

output "availability_zones" {
  description = "Availability Zones the network spans."
  value       = local.azs
}

output "public_subnet_ids" {
  description = "IDs of the public subnets (ALB, NAT gateways)."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets (ECS Fargate tasks, ElastiCache, interface endpoints)."
  value       = aws_subnet.private[*].id
}

output "public_route_table_id" {
  description = "ID of the shared public route table."
  value       = aws_route_table.public.id
}

output "private_route_table_ids" {
  description = "IDs of the per-AZ private route tables."
  value       = aws_route_table.private[*].id
}

output "nat_gateway_ids" {
  description = "IDs of the NAT gateways."
  value       = aws_nat_gateway.this[*].id
}

output "nat_public_ips" {
  description = "Elastic IP addresses of the NAT gateways (egress allow-list source IPs)."
  value       = aws_eip.nat[*].public_ip
}

output "internet_gateway_id" {
  description = "ID of the internet gateway."
  value       = aws_internet_gateway.this.id
}

output "vpc_endpoint_security_group_id" {
  description = "Security group ID guarding the interface VPC endpoints."
  value       = aws_security_group.vpc_endpoints.id
}

output "s3_gateway_endpoint_id" {
  description = "ID of the S3 gateway VPC endpoint."
  value       = aws_vpc_endpoint.s3.id
}

output "interface_endpoint_ids" {
  description = "Map of interface endpoint short service name -> endpoint ID."
  value       = { for k, ep in aws_vpc_endpoint.interface : k => ep.id }
}
