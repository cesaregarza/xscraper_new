variable "db_name" {
  description = "Name of the PostgreSQL database for development"
  type        = string
}

variable "db_user" {
  description = "Username for the PostgreSQL database in development"
  type        = string
}

variable "db_password" {
  description = "Password for the PostgreSQL database in development"
  type        = string
}

variable "db_port" {
  description = "External port for accessing the PostgreSQL database in development"
  type        = number
}
