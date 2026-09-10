#!/usr/bin/env python3
import json,sys,time,hashlib,os
from pathlib import Path
def readj(path):
    p=Path(path)
    if not p.exists(): return []
    out=[]
    for l in p.read_text(encoding="utf-8").splitlines():
        try:
            if l.strip():out.append(json.loads(l))
        except: pass
    return out
state=Path(sys.argv[1]); contract=json.load(open(sys.argv[2],encoding="utf-8"))
obs=readj(state/"observations.jsonl"); ev=readj(state/"events.jsonl"); receipts=readj(state/"receipts.jsonl")
now=int(time.time()*1000)
features={}
for f,c in contract["features"].items():
    vals=[o for o in obs if o.get("feature")==f and o.get("quality_status")=="AVAILABLE"]
    event_avail=sum(e.get("features",{}).get(f,{}).get("status")=="AVAILABLE" for e in ev)
    cov=event_avail/len(ev) if ev else 0
    last=max([o["source_timestamp_ms"] for o in vals],default=None)
    features[f]={"observations":len(vals),"event_coverage":cov,"required":c["min_coverage"],"coverage_pass":bool(ev) and cov>=c["min_coverage"],
                 "last_source_timestamp_ms":last,"freshness_hours":None if last is None else (now-last)/3600000}
dups=len(obs)-len({o.get("observation_id") for o in obs})
future=sum(o.get("source_timestamp_ms",0)>o.get("collected_at_ms",0) for o in obs)
report={"schema":"CRIO_V2_HEALTH_0.2.0","generated_at_ms":now,"observations":len(obs),"events":len(ev),"receipts":len(receipts),
        "duplicate_observations":dups,"future_timestamp_violations":future,"features":features}
report["status"]="PASS" if dups==0 and future==0 and (not ev or all(x["coverage_pass"] for x in features.values())) else "WARN"
(state/"health_latest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
with (state/"health_daily.jsonl").open("a",encoding="utf-8") as f:f.write(json.dumps(report,ensure_ascii=False,sort_keys=True)+"\n")
print(json.dumps(report,ensure_ascii=False,indent=2))
