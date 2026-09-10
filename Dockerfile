FROM python:3.12-slim
WORKDIR /app
COPY . /app
ENV PYTHONUNBUFFERED=1
ENV CRIO_STATE_PATH=/data/crio/state
CMD ["python3","src/collector_daemon.py"]
