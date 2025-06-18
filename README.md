# mocker-hub

![Static Badge](https://img.shields.io/badge/license-BSD_2_Clause-blue)

[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=fff)](#)
[![Bash](https://img.shields.io/badge/Bash-4EAA25?logo=gnubash&logoColor=fff)](#)
[![CSS](https://img.shields.io/badge/CSS-1572B6?logo=css3&logoColor=fff)](#)
[![Sass](https://img.shields.io/badge/Sass-C69?logo=sass&logoColor=fff)](#)
[![HTML](https://img.shields.io/badge/HTML-%23E34F26.svg?logo=html5&logoColor=white)](#)
![YAML](https://img.shields.io/badge/yaml-%23ffffff.svg?logo=yaml&logoColor=151515)
[![JSON](https://img.shields.io/badge/JSON-000?logo=json&logoColor=fff)](#)
![JWT](https://img.shields.io/badge/JWT-black?logo=JSON%20web%20tokens)

[![FastAPI](https://img.shields.io/badge/FastAPI-009485.svg?logo=fastapi&logoColor=white)](#)
[![Postgres](https://img.shields.io/badge/Postgres-%23316192.svg?logo=postgresql&logoColor=white)](#)
![Nginx](https://img.shields.io/badge/nginx-%23009639?logo=nginx)
[![Redis](https://img.shields.io/badge/Redis-%23DD0031.svg?logo=redis&logoColor=white)](#)
[![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=fff)](#)
[![React](https://img.shields.io/badge/React-%2320232a.svg?logo=react&logoColor=%2361DAFB)](#)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?logo=bootstrap&logoColor=fff)](#)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=fff)](#)
![Docker](https://img.shields.io/badge/Docker_Compose-%230db7ed.svg?logo=docker&logoColor=white)
![ElasticSearch](https://img.shields.io/badge/-ElasticSearch-005571?logo=elasticsearch)
![Pytest](https://img.shields.io/badge/pytest-%23ffffff.svg?logo=pytest&logoColor=2f9fe3)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=github-actions&logoColor=white)](#)

![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/magley/mocker-hub?cacheSeconds=3600) ![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-pr/magley/mocker-hub?cacheSeconds=3600)

## Getting started

1) You can optionally regenerate the certificate in `/distribution/certs`.

2) Build and run: `docker compose up--build`.

3) Use debug data while developing. On the first run, while the database is empty, visit [localhost:8000/api/v1/dummy](localhost:8000/api/v1/dummy) (do this just once).

### Nginx and the web app

During development, run the `client/` app locally using `npm run dev`.

In production, you should use nginx as the web app server. To do this, comment in the test environment and comment out the production environment in the root Dockerfile.

## Access points

You can access the server at [localhost:8000](http://localhost:8000/docs).

While developing the API, use Swagger docs: [localhost:8000/docs](localhost:8000/docs).

Database UI is in [localhost:8002](http://localhost:8002). Check `compose.yaml` for the login credentials.

The initial superadmin password is stored in `volume-server-cfg/superadmin_password.txt`.

## Using the registry

To push and pull images through mocker-hub, use the registry:

Log in:

```sh
docker login localhost:5000
```

In case you still have issues, create a file `/etc/docker/daemon.json` and write the following:
```json 
{
 "insecure-registries": ["localhost:5000"]
}
```

Push an image into the registry:

```sh
docker tag {image-name}[:{tag}] localhost:5000/{image-name}[:{tag}]
docker push localhost:5000/{image-name}[:{tag}]
```
If no `:tag` is provided, latest is used by default.

Pull an image from the registry:

```sh
docker pull localhost:5000/{image-name}[:{tag}]
```

Log out:

```shs
docker logout localhost:5000
```