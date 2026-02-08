#!/bin/bash
set -euo pipefail

# Phase 1 (Reddit) — EC2 runner script
#
# Goals:
# - Activate the correct conda environment
# - Run the Phase 1 collector CLI (posts by default; comments optional)
# - Stop the EC2 instance automatically:
#     - Default: stop on success only
#     - Optional: stop always (even on failure) for cost control
# - Safeguards:
#     - Only stop if instance tag AutoStop=true (configurable)
#     - Uses IMDSv2 for instance-id / region / tags
#
# Usage examples:
#   chmod +x collect_reddit.sh
#
#   # Posts only (default), stop on success:
#   nohup ./collect_reddit.sh -s loneliness --listing new --per-subreddit-limit 1000 > process_output.log 2>&1 &
#
#   # Include comments, stop always:
#   STOP_ALWAYS=1 nohup ./collect_reddit.sh -s loneliness --include-comments --comments-limit-per-post 200 > process_output.log 2>&1 &
#
#   # Explicit output directory (no auto naming):
#   nohup ./collect_reddit.sh -s loneliness --out-dir data/ph1/my_run_001 > process_output.log 2>&1 &
#
# Notes:
# - This script assumes your outputs are on an attached EBS volume.
# - Do NOT commit secrets. Credentials should be in your environment or local env/.env as per project config.
# - This script forwards all arguments to: python -u -m cl_st1.ph1.cli.ph1_cli

# -----------------------------
# Config (override via env vars)
# -----------------------------
: "${CONDA_ENV_NAME:=cl_st1_andressa}"
: "${CONDA_SH:=$HOME/miniconda3/etc/profile.d/conda.sh}"

# Stopping behavior:
: "${STOP_ALWAYS:=0}"                 # 1 => stop even if job fails; 0 => stop only on success (default)
: "${REQUIRE_AUTOSTOP_TAG:=1}"        # 1 => require instance tag AutoStop=true to stop; 0 => skip tag check
: "${AUTOSTOP_TAG_KEY:=AutoStop}"
: "${AUTOSTOP_TAG_VALUE:=true}"

# Optional: set extra args to collector via env var (appended after CLI args)
: "${EXTRA_COLLECT_ARGS:=}"

# -----------------------------
# Helpers
# -----------------------------
log() { printf '%s %s\n' "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')]" "$*" >&2; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { log "Error: required command not found: $1"; exit 1; }
}

get_imds_token() {
  curl -fsS -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"
}

imds_get_with_token() {
  local token path
  token="$1"
  path="$2"
  curl -fsS -H "X-aws-ec2-metadata-token: $token" \
    "http://169.254.169.254/latest/${path}"
}

get_region_from_imds() {
  local token region
  token="$1"
  region="$(imds_get_with_token "$token" "meta-data/placement/region" 2>/dev/null || true)"
  if [[ -z "${region:-}" ]]; then
    region="${AWS_REGION:-${AWS_DEFAULT_REGION:-}}"
  fi
  echo "${region:-}"
}

get_instance_id_from_imds() {
  local token instance_id
  token="$1"
  instance_id="$(imds_get_with_token "$token" "meta-data/instance-id" 2>/dev/null || true)"
  echo "${instance_id:-}"
}

get_instance_tag_from_imds() {
  # Requires IMDS instance tags enabled (recommended).
  # Returns empty string if tags are unavailable.
  local token key
  token="$1"
  key="$2"
  imds_get_with_token "$token" "meta-data/tags/instance/${key}" 2>/dev/null || true
}

activate_conda_env() {
  if [[ ! -f "$CONDA_SH" ]]; then
    log "Error: conda.sh not found at: $CONDA_SH"
    log "Set CONDA_SH to your Miniconda location."
    exit 1
  fi

  # shellcheck disable=SC1090
  source "$CONDA_SH"

  conda activate "$CONDA_ENV_NAME"

  if [[ "${CONDA_DEFAULT_ENV:-}" != "$CONDA_ENV_NAME" ]]; then
    log "Error: conda environment '$CONDA_ENV_NAME' not activated!"
    exit 1
  fi

  log "Conda environment active: $CONDA_ENV_NAME"
}

run_collector() {
  # Run from repo root (assumes this script is in repo root).
  local repo_root
  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$repo_root"

  # Ensure package is importable in this env.
  # Editable install is preferred; if not installed, this will fail fast.
  python -c "import cl_st1" >/dev/null 2>&1 || {
    log "Error: Python cannot import 'cl_st1'. Did you run 'pip install -e .' in this environment?"
    exit 1
  }

  # -u streams logs immediately (good for nohup)
  log "Starting collector: python -u -m cl_st1.ph1.cli.ph1_cli $* ${EXTRA_COLLECT_ARGS}"
  # shellcheck disable=SC2086
  python -u -m cl_st1.ph1.cli.ph1_cli "$@" ${EXTRA_COLLECT_ARGS}
}

stop_instance_if_allowed() {
  local token instance_id region tag_value
  require_cmd aws
  require_cmd curl

  token="$(get_imds_token)" || { log "Error: failed to get IMDS token; not stopping instance."; return 0; }
  instance_id="$(get_instance_id_from_imds "$token")"
  region="$(get_region_from_imds "$token")"

  if [[ -z "${instance_id:-}" ]]; then
    log "Error: could not determine instance-id; not stopping instance."
    return 0
  fi
  if [[ -z "${region:-}" ]]; then
    log "Error: could not determine AWS region; not stopping instance."
    return 0
  fi

  if [[ "$REQUIRE_AUTOSTOP_TAG" == "1" ]]; then
    tag_value="$(get_instance_tag_from_imds "$token" "$AUTOSTOP_TAG_KEY")"
    if [[ -z "${tag_value:-}" ]]; then
      log "Auto-stop safeguard: instance tags unavailable via IMDS; not stopping instance."
      log "Tip: enable IMDS instance tags or set REQUIRE_AUTOSTOP_TAG=0 (not recommended)."
      return 0
    fi
    if [[ "${tag_value}" != "$AUTOSTOP_TAG_VALUE" ]]; then
      log "Auto-stop safeguard: tag ${AUTOSTOP_TAG_KEY}=${tag_value} (expected ${AUTOSTOP_TAG_VALUE}); not stopping instance."
      return 0
    fi
  fi

  aws ec2 stop-instances --region "$region" --instance-ids "$instance_id" >/dev/null || true
  log "Stop requested for instance ${instance_id} in region ${region}."
}

# -----------------------------
# Main
# -----------------------------
JOB_EXIT_CODE=0

on_exit() {
  # Decide whether to stop the instance based on job outcome and policy.
  if [[ "$STOP_ALWAYS" == "1" ]]; then
    log "STOP_ALWAYS=1: attempting to stop instance (regardless of job exit code ${JOB_EXIT_CODE})."
    stop_instance_if_allowed || true
    return 0
  fi

  if [[ "$JOB_EXIT_CODE" -eq 0 ]]; then
    log "Job succeeded: attempting to stop instance."
    stop_instance_if_allowed || true
  else
    log "Job failed (exit code ${JOB_EXIT_CODE}): leaving instance running for debugging."
    log "If you intended cost-control mode, re-run with STOP_ALWAYS=1."
  fi
}

main() {
  trap on_exit EXIT

  activate_conda_env

  # Forward all script args to the collector CLI.
  # Examples:
  #   ./collect_reddit.sh -s loneliness --listing new --per-subreddit-limit 1000 --no-include-comments
  #   ./collect_reddit.sh -s loneliness --listing top --per-subreddit-limit 200 --include-comments
  set +e
  run_collector "$@"
  JOB_EXIT_CODE=$?
  set -e

  conda deactivate || true
  exit "$JOB_EXIT_CODE"
}

main "$@"