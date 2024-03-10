output "db_host" {
  value = module.environment.db_host
}

output "db_port" {
  value = module.environment.db_port
}

output "db_name" {
  value = module.environment.db_name
}

output "db_user" {
  value = module.environment.db_user
}

output "db_password" {
  value     = module.environment.db_password
  sensitive = true
}