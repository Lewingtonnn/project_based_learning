variable "aws_region" {
  description = "The AWS region where resources will be made"
  type        = string
  default     = "us-east-1"
}

variable "real_estate_api_project" {
  description = "A tag for the project name to organise resources"
  type        = string
  default     = "DataEngineeringProject"
}

variable "environment" {
  description = "The environment for resource tagging"
  type        = string
  default     = "dev"
}

variable "vpc_cidr_block" {
  description = "The CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16" # A large, private CIDR block for your VPC.
}

variable "public_subnet_cidr" {
  description = "The CIDR block for the public subnet."
  type        = string
  default     = "10.0.1.0/24" # A /24 subnet for public-facing resources.
}

variable "private_subnet_cidr" {
  description = "The CIDR block for the private subnet."
  type        = string
  default     = "10.0.2.0/24" # A /24 subnet for private, sensitive resources.
}

variable "availability_zone" {
  description = "The Availability Zone for your subnets."
  type        = string
  default     = "us-east-1a" # Select an AZ within your chosen region.
}