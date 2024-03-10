variable "db_name" {
  description = "Name of the PostgreSQL database for production"
  type        = string
}

variable "db_user" {
  description = "Username for the PostgreSQL database in production"
  type        = string
}

variable "db_password" {
  description = "Password for the PostgreSQL database in production"
  type        = string
  sensitive   = true
}
