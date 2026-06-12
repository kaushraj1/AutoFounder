output "vpc_id" {
  value = data.aws_vpc.foundation.id
}

output "private_subnet_ids" {
  value = [for s in data.aws_subnet.private : s.id]
}

output "public_subnet_ids" {
  value = [for s in data.aws_subnet.public : s.id]
}

output "security_group_ids" {
  description = "Role -> SG ID map consumed by ecs/, data-layer/, and alb/."
  value = {
    ecs_tasks = aws_security_group.ecs_tasks.id
    alb       = aws_security_group.alb.id
    rds       = aws_security_group.rds.id
    redis     = aws_security_group.redis.id
  }
}