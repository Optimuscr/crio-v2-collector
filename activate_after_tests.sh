#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
STATE_PATH="${1:-}"
if [ -z "$STATE_PATH" ]; then
  echo "KULLANIM: bash ./activate_after_tests.sh /kalici/state/yolu"
  exit 2
fi

echo "[1/4] Dependency-free tests"
python3 "$ROOT/tests/run_tests.py"

echo "[2/4] Persistent state + restart gate"
python3 "$ROOT/src/persistent_state_gate.py" "$STATE_PATH"

echo "[3/4] Health precheck"
python3 "$ROOT/src/health_monitor.py" "$STATE_PATH" "$ROOT/contracts/UNIFIED_DATA_CONTRACT.json" > "$STATE_PATH/health_pre_activation.json"

echo "[4/4] READY"
echo "Gerçek ilk 4S kaynak döngüsü Work tarafından burada çalıştırılmalıdır."
echo "Başarılı gerçek kaynak döngüsü olmadan ACTIVATION_RECEIPT.json üretme."
