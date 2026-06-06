output "alb_arn" {
  description = "ARN of the Application Load Balancer."
  value       = aws_lb.this.arn
}

output "alb_dns_name" {
  description = "DNS name of the ALB (point Route 53 ALIAS records here)."
  value       = aws_lb.this.dns_name
}

output "alb_zone_id" {
  description = "Hosted zone ID of the ALB (for Route 53 ALIAS records)."
  value       = aws_lb.this.zone_id
}

output "alb_security_group_id" {
  description = "Security group of the ALB (allow this as ingress on ECS service SGs)."
  value       = aws_security_group.alb.id
}

output "target_group_arns" {
  description = "Map of service name -> target group ARN (wire into the ECS service load_balancer block)."
  value       = { for k, tg in aws_lb_target_group.this : k => tg.arn }
}

output "https_listener_arn" {
  description = "HTTPS listener ARN (null when no certificate was supplied)."
  value       = local.serve_https ? aws_lb_listener.https[0].arn : null
}

output "http_listener_arn" {
  description = "HTTP listener ARN."
  value       = aws_lb_listener.http.arn
}

output "web_acl_arn" {
  description = "WAF web ACL ARN (null when WAF disabled)."
  value       = var.enable_waf ? aws_wafv2_web_acl.this[0].arn : null
}
