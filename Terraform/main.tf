# 1. Terraform block – tells Terraform which provider to use and version
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# 2. Provider block – tells AWS CLI which region to work in
provider "aws" {
  region = "us-east-1"
}

# 3. Resource block – creates an S3 bucket
resource "aws_s3_bucket" "demo_bucket" {
  bucket = "lewis-demo-bucket-7205"
}
