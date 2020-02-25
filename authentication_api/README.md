# Authentication API

This exercise sets up an API for authenticating users. We will use the following software:

1. Fast API
    - Web app for authenticating users
2. Postgres
    - Store user accounts
3. Redis
    - Store access tokens
4. Kubernetes
    - Configures an authentication api that uses Fast API, Postgres, and Redis

- The Kubernetes configuration is based off this tutorial: [https://testdriven.io/blog/running-flask-on-kubernetes](https://testdriven.io/blog/running-flask-on-kubernetes).
- The Authentication API is based off the Fast API tutorials, which are very detailed and helpful:
    - [SQL (Relational) Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
    - [Security](https://fastapi.tiangolo.com/tutorial/security/)
    - [CORS](https://fastapi.tiangolo.com/tutorial/cors/)

## 1. The authentication API

- The authentication API will be used a centralized authentication service for other APIs.
- It will return an access token when the user logs in, which will allow them to make authorized
  requests to the API
- The access token will be stored in Redis so that the other APIs can verify that the
  access token is valid

This is the barebones version of the authentication API. There are a lot of logistics that I'm trying
to figure out in terms of account and app authorization. So there will likely be large changes here.

Since the focus is on Kubernetes, I'm not going to go indepth on the API implementation, but there
are some things worth highlighting.

### 1.1 Local and Minikube development

This app is simple enough that I can test and develop the API locally using:

```shell
uvicorn app.main:app --reload --port 8000;
```

We can easily install the dependencies using our Anaconda environment, which will allow
us to run this app without having to push to the Minikube Docker repository every time.

We also need to access to Postgres and Redis. We could install local versions, but that will get messy,
We could also create a Docker compose configuration, but that that is one more thing to manage.

A better option is to expose the Postgres and Redis Pods through the NodePort service. This is easy to do,
and all we need to do is update our config.py to use the right host and port.

With NodePort the service, we can connect to Postgres and Redis using the Minikube IP and the node port,
which is between 30000-32767.

I haven't tried [Skaffold](https://github.com/GoogleContainerTools/skaffold), but that seems like another option for
developing apps with Kubernetes.

### 1.2 Alembic

For database migrations, I'm using Alembic. I had a few problems getting it set up.

I needed to edit the `env.py` and make the following adjustments:

The right path needs to be added so that imports will work.

```python
parent_dir = os.path.abspath(os.path.join(os.getcwd()))
sys.path.append(parent_dir)

from app.config import AUTH_DB_URL  # noqa
from app.db import Base  # noqa
import app.models  # noqa
```

Set the database url to use:

```python
config.set_main_option("sqlalchemy.url", AUTH_DB_URL)
```

Add our SQL Alchemy metadata to enable auto generation. You will also need to import the models
otherwise auto generation will not work. I'm not sure why importing `Base.metadata` is not
enough.

```python
target_metadata = Base.metadata
```

### 1.3 authenticator.py

The authenticator.py file is where the authentication occurs. This differs slightly from the
FastAPI security tutorial since I decided not to use JWTs here. I keep reading a lot of reasons
not to use JWTs.

Instead I am generating access tokens and then storing the hashed token in Redis with an expiration
time.

The will be generated when the user logs in with their credentials. Then we they make a request to
an private endpoint, we will check the token in Redis.

This is only a basic implementation for now. I plan to implement something similar to what's described in
this article:

- <http://cryto.net/~joepie91/blog/2016/06/19/stop-using-jwt-for-sessions-part-2-why-your-solution-doesnt-work/>

We will generate our token using the secrets module. Then hash the token. I considered using passlib here,
but I couldn't figure out how to retrieve passlib hashed token from Redis since we won't have an id or email
to use as a key.

So I settled on using SHA-256 hash with a salt. This way we will at least stored the hashed tokens in Redis.

The metadata will be stored using the hash data type, which would allow us to store other information aside
from email, such as APIs that the user has access to or their roles. Granted that information is undecided.

```python
def create_access_token(*, account: Account, expires_delta: timedelta = None):
    if not expires_delta:
        expires_delta = timedelta(minutes=15)

    token = secrets.token_hex()

    hashed_token = hash_token(token, SESSION_DB_TOKEN_KEY)
    session_db = get_session_db()
    session_db.hmset(hashed_token, {"email": account.email})
    session_db.expire(hashed_token, expires_delta)

    return token


def get_account(token: str = Depends(oauth2_scheme), db: DbSession = Depends(get_db)):
    session_db = get_session_db()
    hashed_token = hash_token(token, SESSION_DB_TOKEN_KEY)
    data = session_db.hgetall(hashed_token)

    if data is None:
        raise CREDENTIALS_EXCEPTION

    account = crud.get_account_by_email(db, data["email"])
    if account is None:
        raise CREDENTIALS_EXCEPTION
    return account
```

### 1.4 CORS

Since the we're using a centralized authentication API, we will need to enable CORS
to include the domains of other APIs that depend on this API. Here there are no
other domains, since I haven't created any other APIs yet.

CORS can be added using the middleware pattern. FastAPI provides a CORSMiddleware class.

```python
origins = []


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 2. Running the API on Kubernetes

Make sure push up the auth-api image as `localhost:5000/auth-api` to the Minikube Docker registry.

Then run the following commands:

```shell
# Store Postgres DB user and password
kubectl apply -f kubernetes/authentication_api/db-secrets.yaml;

# Configure Redis and Postgres (persistent volumes and claims, services, and deployments)
kubectl apply -f kubernetes/authentication_api/db-config.yaml;

# Connect to the postres database (auth db) container
kubectl get pods;
kubectl exec <insert-auth-db-pod-name> -it -- psql -U postgresl

# For this experiment, we'll just manually create the auth database inside psql;
psql> create database auth;

# Configure authentication API (service and deployment)
kubectl apply -f kubernetes/authentication_api/app-config.yaml;

# Update ingress to allow the API to be accessed at auth.
kubectl kubernetes/minikube-ingress.yaml

# Update hosts file with Minikube IP and auth.books.test
sudo vi /etc/hosts
```

Now the Swaggers Docs for the authentication API should be accessible at http://auth.books.test/docs.

## 3. Kubernetes configuration details

To run the authentication API we will need the following objects:

- PersistentVolume
    - Needed for Postgres data persistence
- PersistentVolumeClaim
    - I don't fully understand claims, but they seem similar to services in that they allow access
      to a persistent volume. In addition they seem to provide settings for the volume such as access
      modes (ReadWriteOnce, ReadOnlyMany, ReadWriteMany) and disk size.
- NodePort Services
    - We will need NodePorts for both Redis and Postgres
    - Normally we'd use the ClusterIP service, but for development it's nice to be able to access these
      data stores directly.
- Deployments
    - We will also need the Pods to run the Postgres and Redis containers
- Secrets
    - We use this to store the postgres user and password
    - I have a lot of questions still about how to use this securely

### 3.1 Persistent volume and claim

The configuration is pretty straightforward for Minikube. I imagine it's a bit more complicated
for a production deployment where we would want to to configure GCE persistent disk.

The `ReadWriteOnce` mode allows the disk to be connected to only one container. This makes sense
since having multiple writers for one disk seems problematic in terms of concurrency. Also GCE
persistent disks not allow `ReadWriteMany`.

As previously mentioned I don't fully understand volume claims yet aside from we need them
similar to how Services connect Pods, which make sense to have that extra layer.

I'm a bit confused why we need to add the specs to the claim? Is it so additional volumes
with the same spec/metadata could be used?

Which leads me to the question of how persistent volumes are connected to claims. At
first I assumed `volumeName`, but now I think that is not correct.

```yml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: auth-db-pv
  labels:
    type: local
spec:
  capacity:
    storage: 128M
  storageClassName: standard
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/data/auth-db-pv"

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: auth-db-pvc
  labels:
    type: local
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 128M
  volumeName: auth-db-pv
  storageClassName: standard
```

### 3.2 Postgres configuration

As mentioned earlier, we use the NodePort service for development purposes since that
allows us to access the postgres database directly.

For the postgres Deployment Pod, we add a PersistentVolume using the PersistentVolumeClaim.
Then we also use the Secrets object to get postgres user credentials to use as environment
variables in the postgres container.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: auth-db
spec:
  selector:
    service: auth-db
  type: NodePort
  ports:
  - port: 5432
    nodePort: 30001

---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-db
  labels:
    name: database
spec:
  replicas: 1
  selector:
    matchLabels:
      service: auth-db
  template:
    metadata:
      labels:
        service: auth-db
    spec:
      containers:
      - name: auth-db
        image: postgres:12-alpine
        env:
          - name: POSTGRES_USER
            valueFrom:
              secretKeyRef:
                name: auth-db-credentials
                key: user
          - name: POSTGRES_PASSWORD
            valueFrom:
              secretKeyRef:
                name: auth-db-credentials
                key: password
        volumeMounts:
          - name: auth-db-volume-mount
            mountPath: /var/lib/postgresql/data
      volumes:
      - name: auth-db-volume-mount
        persistentVolumeClaim:
          claimName: auth-db-pvc
      restartPolicy: Always
```

### 3.3 Redis configuration

There's not much to add about the Redis configuration since it's
pretty basic, which is great.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: session-db
spec:
  selector:
    service: session-db
  type: NodePort
  ports:
  - port: 6379
    nodePort: 30002

---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: session-db
spec:
  replicas: 1
  selector:
    matchLabels:
      service: session-db
  template:
    metadata:
      labels:
        service: session-db
    spec:
      containers:
      - name: session-db
        image: redis:5.0-alpine
        ports:
        - containerPort: 6379
```

### 3.4 Secrets configuration

The secrets are base64 encoded, which isn't secure, so I'm confused on how to add the
secrets configuration to git.

I have read that secrets can be paired with HashiCorp's Vault, which sounds
interesting but I haven't looked into it yet.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: auth-db-credentials
type: Opaque
data:
  user: cG9zdGdyZXM=
  password: cGFzc3dvcmQ=
```

### 3.5 Auth API configuration

Setting up the auth API is straightforward. Similar to the postgres Pod,
we add our postgres credentials as environment variables.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: auth-api
  labels:
    service: auth-api
spec:
  selector:
    app: auth-api
  ports:
  - port: 80

---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: auth-api
  template:
    metadata:
      labels:
        app: auth-api
    spec:
      containers:
      - name: auth-api
        image: localhost:5000/auth-api:latest
        env:
          - name: AUTH_DB_USER
            valueFrom:
              secretKeyRef:
                name: auth-db-credentials
                key: user
          - name: AUTH_DB_PASSWORD
            valueFrom:
              secretKeyRef:
                name: auth-db-credentials
                key: password
        ports:
        - containerPort: 80
```

### 3.6 Ingress configuration

The ingress configuration is also straightforward.

```yaml
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
  - host: auth.books.test
    http:
      paths:
      - path: /
        backend:
          serviceName: auth-api
          servicePort: 80
```

## 4. Questions

Overall, setting up this simple authentication API was straightforward. Kubernetes is a lot more
powerful than Docker Compose. But it's nice that we can create a similar set up in Kubernetes
and Minikube with relatively low complexity.

There are some things I will need to look into more:

1. PersistentVolumeClaims
2. Securely using secrets
3. How to replace or use Ansible for certain use cases:
    - Setting up configuration files for different environments
    - Setting up persistent disks (folders and files)
4. GKE deployment differences
5. Scaling

There's a lot more stuff that I have questions about, but those are the ones that come to mind.
