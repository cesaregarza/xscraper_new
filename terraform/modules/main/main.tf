terraform{
    required_providers {
        digitalocean = {
            source = "digitalocean/digitalocean"
        }
    }
}
resource "docker_container" "postgres" {
  count = var.environment == "dev" ? 1 : 0

  image = "postgres:latest"
  name  = "postgres-dev"

  env = [
    "POSTGRES_DB=${var.db_name}",
    "POSTGRES_USER=${var.db_user}",
    "POSTGRES_PASSWORD=${var.db_password}",
  ]

  ports {
    internal = 5432
    external = var.db_port
  }
}

resource "digitalocean_database_cluster" "postgres" {
  count = var.environment == "prod" ? 1 : 0

  name       = "postgres-prod"
  engine     = "pg"
  version    = "15"
  size       = "db-s-1vcpu-1gb"
  region     = "nyc1"
  node_count = 1
}

resource "digitalocean_database_user" "prod_user" {
  count = var.environment == "prod" ? 1 : 0

  cluster_id = digitalocean_database_cluster.postgres[0].id
  name       = var.db_user
}

resource "digitalocean_database_db" "prod_db" {
  count = var.environment == "prod" ? 1 : 0

  cluster_id = digitalocean_database_cluster.postgres[0].id
  name       = var.db_name
}

output "db_host" {
  value = var.db_host
}

output "db_port" {
  value = var.db_port
}