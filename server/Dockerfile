# syntax=docker/dockerfile:1.4
FROM python:3.10.15-alpine3.20
WORKDIR /code

# --no-cache removed
RUN --mount=type=cache,target=/var/cache/apk \
    apk add 7zip

COPY ./requirements.txt /code/requirements.txt

#  --no-cache-dir removed
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade -r /code/requirements.txt

COPY ./app /code/app

RUN mkdir -p /code/logs
RUN mkdir -p /code/certs

COPY ./entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

ENTRYPOINT ["/code/entrypoint.sh"]

CMD ["fastapi", "run", "app/api/main.py", "--port", "8000", "--proxy-headers"]