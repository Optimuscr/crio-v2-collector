#!/usr/bin/env python3
import urllib.request,urllib.parse,json,time,hashlib,sys,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("ledger",ROOT/"src/append_only_ledger.py");ledger=importlib.util.module_from_spec(sp);sp.loader.exec_module(ledger)
SPOT="https://api.binance.com"; FUT="https://fapi.binance.com"
def req(base,path,params):
 url=base+path+"?"+urllib.parse.urlencode(params);r=urllib.request.Request(url,headers={"User-Agent":"CRIO-v0.3"});ct=int(time.time()*1000)
 with urllib.request.urlopen(r,timeout=20) as x:raw=x.read()
 return json.loads(raw),raw,ct,url
def hh(b):return hashlib.sha256(b).hexdigest()
def receipt(state,source,url,asset,raw,ct,st):
 o={"source":source,"asset":asset,"url":url,"collected_at_ms":ct,"source_timestamp_ms":st,"sha256":hh(raw),"bytes":len(raw)}
 o["receipt_id"]=ledger.sha(o);ledger.append_jsonl_durable(Path(state)/"receipts.jsonl",o,"receipt_id")
def ingest(state,a,f,v,src,st,ct,raw,unit):
 ledger.ingest({"asset":a,"feature":f,"value":v,"source_id":src,"source_timestamp_ms":int(st),"collected_at_ms":int(ct),"raw_receipt_sha256":hh(raw),"unit":unit},state)
def spot(s,state):
 rows,raw,ct,url=req(SPOT,"/api/v3/klines",{"symbol":s,"interval":"4h","limit":21});st=int(rows[-1][6]);receipt(state,"SPOT_KLINES",url,s,raw,ct,st)
 vs=[float(x[5]) for x in rows];avg=sum(vs[-21:-1])/20
 if avg>0:ingest(state,s,"spot_relative_volume_20",vs[-1]/avg,"SPOT_KLINES",st,ct,raw,"ratio")
 return rows
def perp(s,state):
 rows,raw,ct,url=req(FUT,"/fapi/v1/klines",{"symbol":s,"interval":"4h","limit":21});st=int(rows[-1][6]);receipt(state,"PERP_KLINES",url,s,raw,ct,st)
 vs=[float(x[5]) for x in rows];avg=sum(vs[-21:-1])/20
 if avg>0:ingest(state,s,"perp_relative_volume_20",vs[-1]/avg,"PERP_KLINES",st,ct,raw,"ratio")
def oi(s,state):
 o,raw,ct,url=req(FUT,"/fapi/v1/openInterest",{"symbol":s});st=int(o.get("time",ct));receipt(state,"OPEN_INTEREST",url,s,raw,ct,st);ingest(state,s,"open_interest_value",float(o["openInterest"]),"OPEN_INTEREST",st,ct,raw,"base")
def funding(s,state):
 o,raw,ct,url=req(FUT,"/fapi/v1/premiumIndex",{"symbol":s});st=int(o.get("time",ct));receipt(state,"PREMIUM_INDEX",url,s,raw,ct,st);ingest(state,s,"funding_rate",float(o["lastFundingRate"]),"PREMIUM_INDEX",st,ct,raw,"rate")
def depth(s,state):
 o,raw,ct,url=req(FUT,"/fapi/v1/depth",{"symbol":s,"limit":1000});st=int(o.get("E",o.get("T",ct)));receipt(state,"FUTURES_DEPTH",url,s,raw,ct,st)
 bids=[(float(p),float(q)) for p,q in o["bids"]];asks=[(float(p),float(q)) for p,q in o["asks"]]
 if bids and asks:
  bb,ba=bids[0][0],asks[0][0];mid=(bb+ba)/2
  ingest(state,s,"spread_bps",(ba-bb)/mid*10000,"FUTURES_DEPTH",st,ct,raw,"bps")
  d=sum(p*q for p,q in bids if p>=mid*.99)+sum(p*q for p,q in asks if p<=mid*1.01)
  ingest(state,s,"order_book_depth_1pct_usdt",d,"FUTURES_DEPTH",st,ct,raw,"USDT")
def relative(s,state,a,b):
 if len(a)>=7 and len(b)>=7:
  ar=float(a[-1][4])/float(a[-7][4])-1;br=float(b[-1][4])/float(b[-7][4])-1;st=int(a[-1][6]);ct=int(time.time()*1000);raw=json.dumps({"a":ar,"b":br}).encode()
  ingest(state,s,"btc_relative_return_24h",ar-br,"DERIVED_SPOT",st,ct,raw,"return")
def cycle(state):
 U=json.load(open(ROOT/"config/FROZEN_UNIVERSE.json"))["symbols"];btc=spot("BTCUSDT",state);res={}
 for s in U:
  try:
   a=btc if s=="BTCUSDT" else spot(s,state);perp(s,state);oi(s,state);funding(s,state);depth(s,state);relative(s,state,a,btc);res[s]="PASS"
  except Exception as e:res[s]="FAIL:"+repr(e)
 return res
if __name__=="__main__":print(json.dumps(cycle(Path(sys.argv[1])),indent=2))
