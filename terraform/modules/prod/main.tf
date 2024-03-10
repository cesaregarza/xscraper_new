terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

resource "digitalocean_database_cluster" "postgres" {
  name       = "postgres-prod"
  engine     = "pg"
  version    = "13"
  size       = "db-s-1vcpu-1gb"
  region     = "nyc1"
  node_count = 1
}

resource "digitalocean_database_user" "prod_user" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.db_user
}

resource "digitalocean_database_db" "prod_db" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.db_name
}

output "db_host" {
  value = digitalocean_database_cluster.postgres.host
}

output "db_port" {
  value = digitalocean_database_cluster.postgres.port
}

output "db_name" {
  value = var.db_name
}

output "db_user" {
  value = var.db_user
}

output "db_password" {
  value     = var.db_password
  sensitive = true
}