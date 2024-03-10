output "db_host" {
  value     = digitalocean_database_cluster.postgres.host
  description = "The host address of the PostgreSQL database cluster."
}

output "db_port" {
  value     = digitalocean_database_cluster.postgres.port
  description = "The port on which the PostgreSQL database cluster is accessible."
}

output "db_name" {
  value     = var.db_name
  description = "The name of the PostgreSQL database."
}

output "db_user" {
  value     = var.db_user
  description = "The username for accessing the PostgreSQL database."
}
