# Production — multi-AZ, HA (one NAT gateway per AZ), longer log retention.
environment              = "production"
aws_region               = "ap-south-1"
vpc_cidr                 = "10.10.0.0/16"
az_count                 = 3
single_nat_gateway       = false
enable_flow_logs         = true
flow_logs_retention_days = 90

# --- ALB + ECS (AF-018 / AF-013) ---
certificate_arn = null              # set to an ap-south-1 ACM cert ARN to enable HTTPS
redis_node_type = "cache.r7g.large" # memory-optimized for production

services = {
  backend = {
    port                  = 8000
    health_check_path     = "/health"
    image_tag             = "prod-latest"
    cpu                   = 1024
    memory                = 2048
    desired_count         = 2
    min_capacity          = 2
    max_capacity          = 10
    secret_keys           = ["supabase/jwt_secret", "gemini/api_key", "stripe/secret_key", "stripe/webhook_secret"]
    container_environment = { APP_ENV = "production" }
  }
  web = {
    port                  = 3000
    health_check_path     = "/"
    host_header           = "app.autofounder.ai"
    priority              = 10
    image_tag             = "prod-latest"
    cpu                   = 512
    memory                = 1024
    desired_count         = 2
    min_capacity          = 2
    max_capacity          = 10
    container_environment = { NODE_ENV = "production" }
  }
}
