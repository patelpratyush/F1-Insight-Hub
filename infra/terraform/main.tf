terraform {
  required_providers {
    neon       = { source = "kislerdm/neon" }
    upstash    = { source = "upstash/upstash" }
    cloudflare = { source = "cloudflare/cloudflare" }
    vercel     = { source = "vercel/vercel" }
  }
}

provider "neon" { api_key = var.neon_api_key }
provider "upstash" {
  email   = var.upstash_email
  api_key = var.upstash_api_key
}
provider "cloudflare" { api_token = var.cloudflare_api_token }
provider "vercel" { api_token = var.vercel_api_token }

resource "neon_project" "db" {
  name       = "f1-insight-${var.environment}"
  pg_version = 16
}

resource "upstash_redis_database" "cache" {
  database_name  = "f1-insight-${var.environment}"
  region         = "global"
  primary_region = "us-east-1"
  tls            = true
}

resource "cloudflare_r2_bucket" "telemetry" {
  account_id = var.cloudflare_account_id
  name       = "f1-telemetry-${var.environment}"
}

resource "vercel_project" "web" {
  name           = "f1-insight-web-${var.environment}"
  framework      = "nextjs"
  root_directory = "apps/web"
}
