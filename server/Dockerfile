FROM python:3.10.15-alpine3.20

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN apk add 7zip --no-cache

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

RUN mkdir -p /code/logs

RUN mkdir -p /code/certs

COPY ./entrypoint.sh /code/entrypoint.sh
RUN ls -l /code
RUN chmod +x /code/entrypoint.sh

ENTRYPOINT ["/code/entrypoint.sh"]

CMD ["fastapi", "run", "app/api/main.py", "--port", "8000", "--proxy-headers"]