# mocker-hub

## Getting started

1) Go to `/distribution/certs` and extract `certs.rar`.

2) Build and run: `docker compose up--build`.

3) Use debug data while developing. On the first run, while the database is empty, visit [localhost:8000/api/v1/dummy](localhost:8000/api/v1/dummy) (do this just once).

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
docker tag {image-name} localhost:5000/{image-name}
docker push localhost:5000/{image-name}
```

Pull an image from the registry:

```sh
docker pull localhost:5000/{image-name}
```

Log out:

```shs
docker logout localhost:5000
```