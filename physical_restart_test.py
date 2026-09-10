#!/usr/bin/env python3
import json,sys,subprocess,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];state=Path(sys.argv[1]);probe=state.parent/(state.name+"_restart_probe")
if probe.exists():shutil.rmtree(probe)
probe.mkdir(parents=True)
code="import importlib.util;from pathlib import Path;sp=importlib.util.spec_from_file_location('m',r'%s');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);x={'asset':'BTCUSDT','feature':'funding_rate','value':.1,'source_id':'RESTART_PROBE','source_timestamp_ms':1000,'collected_at_ms':1010,'raw_receipt_sha256':'c'*64};print(m.ingest(x,Path(r'%s'))['inserted'])"%(ROOT/"src/append_only_ledger.py",probe)
a=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True);p=probe/"observations.jsonl";before=p.read_bytes();bh=hashlib.sha256(before).hexdigest()
b=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True);after=p.read_bytes();ah=hashlib.sha256(after).hexdigest()
ok=a.returncode==0 and b.returncode==0 and bh==ah and len(after.splitlines())==1 and b.stdout.strip()=="False"
r={"process1_rc":a.returncode,"process2_rc":b.returncode,"sha_before":bh,"sha_after":ah,"records":len(after.splitlines()),"second_inserted":b.stdout.strip(),"production_state_untouched":True,"pass":ok}
(state/"RESTART_RECOVERY_TEST.json").write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));raise SystemExit(0 if ok else 2)
