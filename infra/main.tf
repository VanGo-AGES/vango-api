terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "vango-tfstate-staging" # Cole o nome exato aqui
    key    = "staging/terraform.tfstate"
    region = "us-east-2" # Atualizado para Ohio
  }
}

provider "aws" {
  region = var.aws_region
}