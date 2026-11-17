output "database_uri" {
  value     = neon_project.db.connection_uri
  sensitive = true
}
output "redis_endpoint" { value = upstash_redis_database.cache.endpoint }
output "telemetry_bucket" { value = cloudflare_r2_bucket.telemetry.name }
