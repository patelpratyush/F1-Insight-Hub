variable "environment" { type = string }
variable "cloudflare_account_id" { type = string }
variable "upstash_email" { type = string }
variable "upstash_api_key" {
  type      = string
  sensitive = true
}
variable "neon_api_key" {
  type      = string
  sensitive = true
}
variable "vercel_api_token" {
  type      = string
  sensitive = true
}
variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}
