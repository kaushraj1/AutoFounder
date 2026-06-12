variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "organization_id" {
  type = string
}

variable "run_id" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "services" {
  description = "Service routing entries. Keyed by service name."
  type = map(object({
    container_port    = number
    health_check_path = string
  }))
  default = {}
}