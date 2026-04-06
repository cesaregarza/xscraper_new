#!/bin/bash

set -euo pipefail

TOKENS_INPUT="${1:-}"
DEFAULT_FTOKEN_URL="https://nxapi-znca-api.fancy.org.uk/api/znca/f"

if [ -z "$TOKENS_INPUT" ]; then
    echo "Expected a pipe-delimited TOKENS argument" >&2
    exit 1
fi

decode_shared_config() {
    if [ -z "${SCRAPER_SHARED_CONFIG_B64:-}" ]; then
        return 0
    fi

    printf '%s' "$SCRAPER_SHARED_CONFIG_B64" | base64 --decode
}

write_optional_line() {
    local file_path="$1"
    local key="$2"
    local value="${3:-}"

    if [ -n "$value" ]; then
        printf '%s = %s\n' "$key" "$value" >> "$file_path"
    fi
}

write_config_from_env() {
    local file_path="$1"

    write_optional_line \
        "$file_path" \
        "ftoken_url" \
        "${SCRAPER_FTOKEN_URL:-$DEFAULT_FTOKEN_URL}"
    write_optional_line "$file_path" "gtoken" "${SCRAPER_GTOKEN:-}"
    write_optional_line "$file_path" "bullet_token" "${SCRAPER_BULLET_TOKEN:-}"
    printf '\n[options]\n' >> "$file_path"
    write_optional_line "$file_path" "user_agent" "${SCRAPER_USER_AGENT:-}"
    write_optional_line \
        "$file_path" \
        "app_version_override" \
        "${SCRAPER_APP_VERSION_OVERRIDE:-}"

    if [ -n "${SCRAPER_NXAPI_CLIENT_ID:-}" ] || \
        [ -n "${SCRAPER_NXAPI_CLIENT_ASSERTION_PRIVATE_KEY_PATH:-}" ]; then
        printf '\n[nxapi]\n' >> "$file_path"
        write_optional_line \
            "$file_path" \
            "nxapi_client_id" \
            "${SCRAPER_NXAPI_CLIENT_ID:-}"
        write_optional_line \
            "$file_path" \
            "nxapi_scope" \
            "${SCRAPER_NXAPI_SCOPE:-}"
        write_optional_line \
            "$file_path" \
            "nxapi_user_agent" \
            "${SCRAPER_NXAPI_USER_AGENT:-}"
        write_optional_line \
            "$file_path" \
            "nxapi_client_version" \
            "${SCRAPER_NXAPI_CLIENT_VERSION:-}"
        write_optional_line \
            "$file_path" \
            "nxapi_token_url" \
            "${SCRAPER_NXAPI_TOKEN_URL:-}"
        write_optional_line \
            "$file_path" \
            "nxapi_client_secret" \
            "${SCRAPER_NXAPI_CLIENT_SECRET:-}"
        write_optional_line \
            "$file_path" \
            "nxapi_client_assertion_private_key_path" \
            "${SCRAPER_NXAPI_CLIENT_ASSERTION_PRIVATE_KEY_PATH:-}"
        write_optional_line \
            "$file_path" \
            "nxapi_client_assertion_jku" \
            "${SCRAPER_NXAPI_CLIENT_ASSERTION_JKU:-}"
        write_optional_line \
            "$file_path" \
            "nxapi_client_assertion_kid" \
            "${SCRAPER_NXAPI_CLIENT_ASSERTION_KID:-}"
        write_optional_line \
            "$file_path" \
            "nxapi_client_assertion_type" \
            "${SCRAPER_NXAPI_CLIENT_ASSERTION_TYPE:-}"
    fi
}

IFS='|' read -r -a TOKENS <<< "$TOKENS_INPUT"

for index in "${!TOKENS[@]}"; do
    filename="SCRAPER_${index}.ini"
    session_token="${TOKENS[$index]}"

    printf '[tokens]\n' > "$filename"
    printf 'session_token = %s\n' "$session_token" >> "$filename"

    if [ -n "${SCRAPER_SHARED_CONFIG_B64:-}" ]; then
        printf '\n' >> "$filename"
        decode_shared_config >> "$filename"
    else
        write_config_from_env "$filename"
    fi
done
