variable "project_id" {
    description = "The Google Cloud Project in which resources will be provisioned."
    type        = string
}

variable "region" {
    description = "The region in which resources will be provisioned."
    type        = string
    default     = "us-central1"
}

variable "lab_id" {
    description = "Lab ID"
    type        = string
}


