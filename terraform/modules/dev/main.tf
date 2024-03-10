terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

resource "docker_container" "postgres" {
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

output "db_host" {
  value = "localhost"
}

output "db_port" {
  value = var.db_port
}