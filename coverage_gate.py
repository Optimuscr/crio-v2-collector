#!/usr/bin/env python3
import json,sys
from pathlib import Path
contract=json.load(open(sys.argv[1],encoding="utf-8")); events=Path(sys.argv[2])
rows=[json.loads(x) for x in events.read_text(encoding="utf-8").splitlines() if x.strip()] if events.exists() else []
out={"events":len(rows),"features":{}}
for feat,c in contract["features"].items():
    n=sum(r["features"].get(feat,{}).get("status")=="AVAILABLE" for r in rows)
    ratio=n/len(rows) if rows else 0
    out["features"][feat]={"available":n,"coverage":ratio,"required":c["min_coverage"],"pass":ratio>=c["min_coverage"]}
out["all_pass"]=bool(rows) and all(x["pass"] for x in out["features"].values())
print(json.dumps(out,ensure_ascii=False,indent=2))
