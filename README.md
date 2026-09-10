# CRIO v2 Prospective Collector

Railway üzerinde sürekli çalışan CRIO v2 prospective veri toplayıcısı.

## Durum
- Üretim AL/skor motoru içermez.
- AVAXUSDT ve NEARUSDT holdout olarak mühürlüdür.
- Kalıcı state yolu: `/data/crio/state`
- Railway volume mount: `/data`

## Yerel test
```bash
python3 tests/run_tests.py
```

## Tek döngü
```bash
CRIO_STATE_PATH=/data/crio/state python3 src/collector_daemon.py --once
```

## Sürekli çalışma
```bash
CRIO_STATE_PATH=/data/crio/state python3 src/collector_daemon.py
```

İlk prospective dönem, kalıcı volume ve fiziksel restart doğrulandıktan sonra başlayan ilk tamamlanmış 4 saatlik döngüden itibaren kabul edilir.
