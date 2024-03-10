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

provider "docker" {
}

provider "digitalocean" {
  token = var.do_token
}

module "dev" {
  source = "./modules/dev"
  db_name     = var.db_name
  db_user     = var.db_user
  db_password = var.db_password
  db_port     = var.db_port
}

module "prod" {
  source = "./modules/prod"
  db_name     = var.db_name
  db_user     = var.db_user
  db_password = var.db_password
}
