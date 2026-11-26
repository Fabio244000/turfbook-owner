#!/usr/bin/env bash
# A throwaway public key for this CI run only: Settings requires identity's public key to
# verify the session token, and no real key ever reaches CI.
set -euo pipefail

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$RUNNER_TEMP/jwt.pem"
openssl pkey -in "$RUNNER_TEMP/jwt.pem" -pubout -out "$RUNNER_TEMP/jwt.pub.pem"
{
  echo 'JWT_PUBLIC_KEY<<EOF'
  cat "$RUNNER_TEMP/jwt.pub.pem"
  echo 'EOF'
} >> "$GITHUB_ENV"
