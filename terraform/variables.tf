variable "region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  description = "The Environment tag value the team rules match"
  type        = string
  default     = "prod"
}

variable "notification_email" {
  description = "Optional. Subscribes this address to all three topics so you can read the events"
  type        = string
  default     = ""
}
