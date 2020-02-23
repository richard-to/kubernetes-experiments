# Hello World API

The goal of this exercise is deploy a FastAPI app using Kubernetes.

# 1. Hello World app

This is the example app from the FastAPI documentation. It basically returns `{"Hello": "World"}`.

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}
```

# 2. Dockerfile

The Dockerfile is based off a prebuilt docker image that integrates Uvicorn, Gunicorn, and FastAPI.

- [Uvicorn](https://www.uvicorn.org/)
  - ASGI server (different from WSGI)
- [Gunicorn](https://gunicorn.org/)
  - Used to manage Uvicorn processes
- [FastAPI](https://fastapi.tiangolo.com/)
  - ASGI web framework

```docker
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY ./app /app
```

# 3. Creating the Docker image

```shell
docker build -t helloworld .;
docker tag helloworld localhost:5000/helloworld;
```

In order for minikube to use this image, we need to push it to the minkube registry. To do this,
we'll need to redirect the `docker push` command to push to the minikube registry.

This can be done with this command. So long as this image is running, all `docker push` commands will
push images to the minikube registry.

```shell
docker run --rm -it --network=host alpine ash -c "apk add socat && socat TCP-LISTEN:5000,reuseaddr,fork TCP:$(minikube ip):5000";
```

In another terminal, you now can push the image:

```
docker push localhost:5000/helloworld;
```

# 4. Deploying the Helloworld API

```shell
# Register a service will provide internal network access to the Helloworld API
kubectl create -f ./kubernetes/helloworld/service.yaml;

# Deploy the Helloworld API to a pod
kubectl create -f ./kubernetes/helloworld/deployment.yaml;

# Provide external access to the Helloworld API using the ingress method
# With minikube, requests will be routed by Nginx to the appropriate service.
kubectl apply -f ./kubernetes/minikube-ingress.yml;
```

In order to view the Helloworld API, we'll need to update our `/etc/hosts` file.

You can get the IP of your minikube VM installation using `minikube ip`. My IP is `192.168.99.101`.

```
192.168.99.101    helloworld.test
```

Now you should be able to view the api at http://helloworld.test

## 4.1 Service file

This file configures a `helloworld` service that provides access to
the `helloworld` app via port `80`.

The `targetPort` is the port exposed by the `helloworld` app container, which
is also `80`. Since this is the same `port`, we don't have to specify a `targetPort` since
it will default to the value specified by `port`.

```yml
apiVersion: v1
kind: Service
metadata:
  name: helloworld
  labels:
    service: helloworld
spec:
  selector:
    app: helloworld
  ports:
  - port: 80
```

## 4.2 Deployment file

This file deploys a stateless pod to the cluster. Here we specify our
helloworld image to be run with only 1 instance (replica).

```yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: helloworld
spec:
  replicas: 1
  selector:
    matchLabels:
      app: helloworld
  template:
    metadata:
      labels:
        app: helloworld
    spec:
      containers:
      - name: helloworld
        image: localhost:5000/helloworld:latest
        ports:
        - containerPort: 80
```

## 4.3 Ingress file

This file configures access to our helloworld app at http://helloworld.test.

Here we use the `.test` domain since it is a reserved domain. I didn't use `.local` since Bonjour uses that domain.

Basically we specify a host and link it to the helloworld service and port. Note that servicePort is set to 80.
This is the port to access the helloworld app internally. Externally access to the app is also configured for port 80. In
this case they just happen to be the same.

```yml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: minikube-ingress
  annotations:
spec:
  rules:
  - host: helloworld.test
    http:
      paths:
      - path: /
        backend:
          serviceName: helloworld
          servicePort: 80
```
