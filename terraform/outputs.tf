output "db_host" {
  value = module.prod.db_host
}

output "db_port" {
  value = module.prod.db_port
}

output "db_name" {
  value = module.prod.db_name
}

output "db_user" {
  value = module.prod.db_user
}

output "db_password" {
  value     = module.prod.db_password
  sensitive = true
}