# Define the required providers
terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
    digitalocean = {
      source = "digitalocean/digitalocean"
    }
  }
}

# Use workspace to determine the environment
locals {
  environment = terraform.workspace == "default" ? "dev" : terraform.workspace
}

# Call the appropriate module based on the workspace
module "environment" {
  source = "./modules/${local.environment}"
}