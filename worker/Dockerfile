FROM python:3.10.15-alpine3.20

COPY worker.py /

RUN pip install --no-cache-dir rq redis

CMD ["python", "worker.py"]