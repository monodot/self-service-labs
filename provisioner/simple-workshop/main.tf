// https://cloud.google.com/docs/terraform/get-started-with-terraform
// https://github.com/terraform-google-modules/terraform-docs-samples/blob/main/storage_new_bucket/main.tf

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "random_id" "bucket_prefix" {
  byte_length = 2
}

resource "google_storage_bucket" "lab_bucket" {
  name          = "lab-${var.lab_id}-${random_id.bucket_prefix.hex}"
  location      = "US"
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  labels = {
    environment = "dev"
    lab_id = "${var.lab_id}"
  }
}

resource "google_service_account" "demo_sa" {
  account_id   = "lab-${var.lab_id}-${random_id.bucket_prefix.hex}-sa"
  display_name = "Lab ${var.lab_id} Service Account"
}

resource "google_service_account_key" "demo_sa_key" {
  service_account_id = google_service_account.demo_sa.name
}

resource "google_storage_bucket_object" "demo_object" {
  name   = "user-key"
  bucket = google_storage_bucket.lab_bucket.name
  content = google_service_account_key.demo_sa_key.private_key
  # source = "user-key.json"
}

