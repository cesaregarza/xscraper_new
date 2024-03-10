terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
    }
  }
}

resource "digitalocean_database_cluster" "postgres" {
  name       = "postgres-prod"
  engine     = "pg"
  version    = "15"
  size       = "db-s-1vcpu-2gb"
  region     = "nyc3"
  node_count = 1
}

resource "digitalocean_database_db" "prod_db" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.db_name
}

resource "digitalocean_database_user" "prod_user" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.db_user
}
