#!/usr/bin/env python3
import json,sys,hashlib,importlib.util,os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
state=Path(sys.argv[1]).resolve()
state.mkdir(parents=True,exist_ok=True)

# Reject obviously ephemeral inspection locations
bad_roots=["/tmp","/var/tmp"]
if any(str(state).startswith(x+"/") or str(state)==x for x in bad_roots):
    raise SystemExit("FAIL: state path is ephemeral")

sp=importlib.util.spec_from_file_location("ledger",ROOT/"src/append_only_ledger.py")
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)

probe={
 "asset":"BTCUSDT","feature":"funding_rate","value":0.00012345,
 "source_id":"PERSISTENCE_PROBE","source_timestamp_ms":1000,"collected_at_ms":1010,
 "raw_receipt_sha256":"b"*64
}
r=m.ingest(probe,state)
p=state/"observations.jsonl"
before=p.read_bytes()
before_sha=hashlib.sha256(before).hexdigest()
count_before=len(before.splitlines())

# emulate restart by reloading code, then idempotently ingest same probe
sp2=importlib.util.spec_from_file_location("ledger_restart",ROOT/"src/append_only_ledger.py")
m2=importlib.util.module_from_spec(sp2);sp2.loader.exec_module(m2)
r2=m2.ingest(probe,state)
after=p.read_bytes()
after_sha=hashlib.sha256(after).hexdigest()
count_after=len(after.splitlines())

ok=(count_before==count_after and before_sha==after_sha and r2["inserted"] is False)
receipt={
 "state_path":str(state),
 "write_read_pass":p.exists(),
 "count_before_restart":count_before,
 "count_after_restart":count_after,
 "sha256_before_restart":before_sha,
 "sha256_after_restart":after_sha,
 "duplicate_reingest_inserted":r2["inserted"],
 "restart_recovery_pass":ok
}
(state/"RESTART_RECOVERY_TEST.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
print(json.dumps(receipt,indent=2))
raise SystemExit(0 if ok else 2)
