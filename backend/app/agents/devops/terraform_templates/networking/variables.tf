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
  description = "Foundation VPC ID. From Settings.foundation_vpc_id."
  type        = string
}

variable "private_subnet_ids" {
  description = "Foundation private subnets. From Settings.foundation_private_subnet_ids."
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "Foundation public subnets. From Settings.foundation_public_subnet_ids."
  type        = list(string)
}

variable "availability_zones" {
  description = "AZs the foundation subnets live in."
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}