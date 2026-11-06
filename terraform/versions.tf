terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
    # Alarm tag propagation isn't in the aws provider yet, so the alarms come from the Cloud Control provider.
    awscc = {
      source  = "hashicorp/awscc"
      version = ">= 1.109"
    }
  }
}

provider "aws" {
  region = var.region
}

provider "awscc" {
  region = var.region
}
