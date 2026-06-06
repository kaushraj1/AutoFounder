# Staging — mirrors production config; cost-trimmed (single NAT, 2 AZs).
environment        = "staging"
aws_region         = "ap-south-1"
vpc_cidr           = "10.20.0.0/16"
az_count           = 2
single_nat_gateway = true
enable_flow_logs   = true

# --- ALB + ECS (AF-018 / AF-013) ---
certificate_arn = null              # set to an ap-south-1 ACM cert ARN to enable HTTPS
redis_node_type = "cache.t4g.micro" # small for staging

services = {
  backend = {
    port                  = 8000
    health_check_path     = "/health"
    image_tag             = "staging-latest"
    cpu                   = 512
    memory                = 1024
    desired_count         = 1
    min_capacity          = 1
    max_capacity          = 4
    secret_keys           = ["supabase/jwt_secret", "gemini/api_key"]
    container_environment = { APP_ENV = "staging" }
  }
  web = {
    port                  = 3000
    health_check_path     = "/"
    host_header           = "app.autofounder.ai"
    priority              = 10
    image_tag             = "staging-latest"
    cpu                   = 256
    memory                = 512
    desired_count         = 1
    min_capacity          = 1
    max_capacity          = 4
    container_environment = { NODE_ENV = "production" }
  }
}
