variable "db_name" {
  type        = string
  description = "Name of the PostgreSQL database"
}

variable "db_user" {
  type        = string
  description = "Username for the PostgreSQL database"
}

variable "db_password" {
  type        = string
  description = "Password for the PostgreSQL database"
}

variable "db_host" {
  type        = string
  description = "Database host"
}

variable "db_port" {
  type        = number
  description = "Database port"
}