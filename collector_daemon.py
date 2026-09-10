#!/usr/bin/env python3
import subprocess,time,datetime,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];STATE=Path(os.environ.get("CRIO_STATE_PATH","/data/crio/state"))
def run():
 subprocess.run([sys.executable,str(ROOT/"src/binance_collector.py"),str(STATE)])
 subprocess.run([sys.executable,str(ROOT/"src/health_monitor.py"),str(STATE),str(ROOT/"contracts/UNIFIED_DATA_CONTRACT.json")])
if "--once" in sys.argv:run();raise SystemExit
while True:
 n=datetime.datetime.now(datetime.timezone.utc);h=((n.hour//4)+1)*4
 t=(n.replace(hour=h,minute=2,second=0,microsecond=0) if h<24 else datetime.datetime.combine(n.date()+datetime.timedelta(days=1),datetime.time(0,2),tzinfo=datetime.timezone.utc))
 time.sleep(max(1,(t-datetime.datetime.now(datetime.timezone.utc)).total_seconds()));run()
