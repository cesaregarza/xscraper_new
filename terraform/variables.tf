variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
}

variable "db_user" {
  description = "Username for the PostgreSQL database"
  type        = string
}

variable "db_password" {
  description = "Password for the PostgreSQL database"
  type        = string
}

variable "db_port" {
  description = "Database port"
  type        = number
  default     = 5432
}
