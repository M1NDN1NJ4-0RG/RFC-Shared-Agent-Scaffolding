#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source "./lib.sh"

ROOT="$(cd .. && pwd)"
PREF="${ROOT}/scripts/preflight-automerge-ruleset.sh"

make_mock_gh() {
  local dir="$1"
  cat > "${dir}/gh" <<'GH'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" != "api" ]]; then
  echo "unsupported gh subcommand" >&2
  exit 99
fi
endpoint="${@: -1}"
scenario="${GH_SCENARIO:-ok}"

if [[ "$endpoint" =~ /rulesets$ ]]; then
  case "$scenario" in
    auth_error) printf '{"message":"Bad credentials","status":"401"}\n' ;;
    *) printf '[{"id":123,"name":"Main - PR Only + Green CI"}]\n' ;;
  esac
  exit 0
fi

if [[ "$endpoint" =~ /rulesets/123$ ]]; then
  case "$scenario" in
    auth_error) printf '{"message":"Forbidden","status":"403"}\n' ;;
    inactive) printf '{"id":123,"name":"Main - PR Only + Green CI","enforcement":"disabled","conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"]}},"rules":[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"lint"},{"context":"test"}]}}]}\n' ;;
    no_default) printf '{"id":123,"name":"Main - PR Only + Green CI","enforcement":"active","conditions":{"ref_name":{"include":["refs/heads/main"]}},"rules":[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"lint"},{"context":"test"}]}}]}\n' ;;
    missing_ctx) printf '{"id":123,"name":"Main - PR Only + Green CI","enforcement":"active","conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"]}},"rules":[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"lint"}]}}]}\n' ;;
    *) printf '{"id":123,"name":"Main - PR Only + Green CI","enforcement":"active","conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"]}},"rules":[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"lint"},{"context":"test"}]}}]}\n' ;;
  esac
  exit 0
fi

printf '{"message":"Not Found","status":"404"}\n'
exit 0
GH
  chmod +x "${dir}/gh"
}

test_preflight_ok() {
  local tmp mockbin
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mockbin="$tmp/mockbin"; mkdir -p "$mockbin"
    make_mock_gh "$mockbin"
    PATH="$mockbin:$PATH" GH_SCENARIO=ok bash "$PREF" --repo o/r --ruleset-name "Main - PR Only + Green CI" --want '["lint","test"]' >/dev/null
  )
}

test_preflight_missing_ctx() {
  local tmp mockbin rc
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mockbin="$tmp/mockbin"; mkdir -p "$mockbin"
    make_mock_gh "$mockbin"
    set +e
    PATH="$mockbin:$PATH" GH_SCENARIO=missing_ctx bash "$PREF" --repo o/r --ruleset-name "Main - PR Only + Green CI" --want '["lint","test"]' >/dev/null 2>&1
    rc=$?
    set -e
    [[ "$rc" -eq 1 ]]
  )
}

test_preflight_inactive() {
  local tmp mockbin rc
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mockbin="$tmp/mockbin"; mkdir -p "$mockbin"
    make_mock_gh "$mockbin"
    set +e
    PATH="$mockbin:$PATH" GH_SCENARIO=inactive bash "$PREF" --repo o/r --ruleset-name "Main - PR Only + Green CI" --want '["lint","test"]' >/dev/null 2>&1
    rc=$?
    set -e
    [[ "$rc" -eq 1 ]]
  )
}

test_preflight_no_default() {
  local tmp mockbin rc
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mockbin="$tmp/mockbin"; mkdir -p "$mockbin"
    make_mock_gh "$mockbin"
    set +e
    PATH="$mockbin:$PATH" GH_SCENARIO=no_default bash "$PREF" --repo o/r --ruleset-name "Main - PR Only + Green CI" --want '["lint","test"]' >/dev/null 2>&1
    rc=$?
    set -e
    [[ "$rc" -eq 1 ]]
  )
}

test_preflight_auth_error() {
  local tmp mockbin rc
  tmp="$(mktemp_dir)"
  (
    cd "$tmp"
    mockbin="$tmp/mockbin"; mkdir -p "$mockbin"
    make_mock_gh "$mockbin"
    set +e
    PATH="$mockbin:$PATH" GH_SCENARIO=auth_error bash "$PREF" --repo o/r --ruleset-name "Main - PR Only + Green CI" --want '["lint","test"]' >/dev/null 2>&1
    rc=$?
    set -e
    [[ "$rc" -eq 2 ]]
  )
}

t "preflight: ok returns 0" test_preflight_ok
t "preflight: missing contexts returns 1" test_preflight_missing_ctx
t "preflight: enforcement inactive returns 1" test_preflight_inactive
t "preflight: does not target default branch returns 1" test_preflight_no_default
t "preflight: auth error returns 2" test_preflight_auth_error

summary
