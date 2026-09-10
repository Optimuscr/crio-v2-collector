#!/usr/bin/env python3
import argparse,hashlib,json,os,tempfile
from pathlib import Path

def canonical(o): return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(o): return hashlib.sha256(canonical(o)).hexdigest()

def ids_in(path,id_field):
    p=Path(path)
    if not p.exists(): return set()
    out=set()
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                x=json.loads(line); 
                if x.get(id_field): out.add(x[id_field])
            except Exception: pass
    return out

def append_jsonl_durable(path,obj,id_field):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    oid=obj[id_field]
    if oid in ids_in(path,id_field):
        return False
    with path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,ensure_ascii=False,sort_keys=True)+"\n")
        f.flush(); os.fsync(f.fileno())
    return True

def atomic_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def ingest(envelope,state_dir):
    required=["asset","feature","value","source_id","source_timestamp_ms","collected_at_ms","raw_receipt_sha256"]
    miss=[k for k in required if k not in envelope]
    if miss: raise ValueError("MISSING_FIELDS:"+",".join(miss))
    if envelope["source_timestamp_ms"]>envelope["collected_at_ms"]: raise ValueError("SOURCE_AFTER_COLLECTION")
    base={k:envelope[k] for k in required}
    obs={"schema":"CRIO_V2_OBSERVATION_0.2.0",**base,"quality_status":envelope.get("quality_status","AVAILABLE"),"unit":envelope.get("unit"),
         "observation_id":sha(base)}
    inserted=append_jsonl_durable(Path(state_dir)/"observations.jsonl",obs,"observation_id")
    return {**obs,"inserted":inserted}

def bind_event(event,state_dir,contract):
    observations=[]
    p=Path(state_dir)/"observations.jsonl"
    if p.exists():
        observations=[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    row={"schema":"CRIO_V2_EVENT_0.2.0",**event,"features":{}}
    for feat in contract["features"]:
        cand=[o for o in observations if o["asset"]==event["asset"] and o["feature"]==feat and o["source_timestamp_ms"]<=event["event_timestamp_ms"]]
        if not cand: row["features"][feat]={"status":"MISSING","value":None}
        else:
            x=max(cand,key=lambda o:o["source_timestamp_ms"])
            row["features"][feat]={"status":x["quality_status"],"value":x["value"],"source_id":x["source_id"],"source_timestamp_ms":x["source_timestamp_ms"],"observation_id":x["observation_id"]}
    row["event_id"]=sha({"asset":event["asset"],"event_timestamp_ms":event["event_timestamp_ms"],"trigger":event["trigger"]})
    inserted=append_jsonl_durable(Path(state_dir)/"events.jsonl",row,"event_id")
    return {**row,"inserted":inserted}

if __name__=="__main__":
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("ingest");a.add_argument("envelope");a.add_argument("state")
    b=sub.add_parser("bind");b.add_argument("event");b.add_argument("state");b.add_argument("contract")
    x=ap.parse_args()
    if x.cmd=="ingest": print(json.dumps(ingest(json.load(open(x.envelope)),x.state),ensure_ascii=False,indent=2))
    else: print(json.dumps(bind_event(json.load(open(x.event)),x.state,json.load(open(x.contract))),ensure_ascii=False,indent=2))
