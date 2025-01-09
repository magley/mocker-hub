FROM python:3.10.15-alpine3.20

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

RUN mkdir -p /code/logs

CMD ["fastapi", "run", "app/api/main.py", "--port", "8000", "--proxy-headers"]