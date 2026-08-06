terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "databricks" {
  host  = var.databricks_host
  token = var.databricks_token
}

variable "aws_region" {
  description = "AWS region for the lakehouse storage tier."
  type        = string
  default     = "us-east-1"
}

variable "databricks_host" {
  description = "Databricks workspace URL."
  type        = string
}

variable "databricks_token" {
  description = "Databricks personal access token."
  type        = string
  sensitive   = true
}

# Provision the primary object-store layer for lakehouse data and metadata.
resource "aws_s3_bucket" "lakehouse_storage" {
  bucket = var.bucket_name

  tags = {
    Name        = "datakernel-lakehouse"
    Environment = "platform"
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "lakehouse_storage" {
  bucket = aws_s3_bucket.lakehouse_storage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lakehouse_storage" {
  bucket = aws_s3_bucket.lakehouse_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "databricks_cluster" "base_cluster" {
  cluster_name            = "datakernel-base"
  spark_version           = "13.3.x-scala2.12"
  node_type_id           = "m5d.large"
  autotermination_minutes = 20
  num_workers            = 1

  spark_conf = {
    "spark.databricks.delta.preview.enabled" = "true"
  }
}

variable "bucket_name" {
  description = "Globally unique S3 bucket name for the lakehouse storage tier."
  type        = string
}
