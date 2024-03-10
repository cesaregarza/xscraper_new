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

# Use a local provider for the dev environment
provider "docker" {}

# Use the DigitalOcean provider for the prod environment
provider "digitalocean" {
  token = var.do_token
}

# Call the dev module
module "dev" {
  source = "./modules/dev"
}

# Call the prod module
module "prod" {
  source = "./modules/prod"
}