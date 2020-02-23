# Kubernetes Experiments

This repository contains code that I'm using to learn and experiment with Kubernetes.

# 1. Environment setup

- minikube
- kubectl
- docker (for macOS)
- python 3.7 (via Anaconda)

## 1.1 Install `minikube` and `kubectl` CLI tools via gcloud:

I use GCP for production deployments, so I'm installing kubectl and minikube from gcloud to avoid version discrepancies.

Homebrew can also be used to install kubectl and minikube.

```shell
# Install kubectl and minikube via gcloud
gcloud components install kubectl;
gcloud components install minikube;

# Make sure we have the latest versions of kubectl and minikube
gcloud components update;
```

## 1.2 Install Docker for macOS:

Follow the instructions here: https://docs.docker.com/docker-for-mac/install/

## 1.3 Start minikube

```shell
# Starts a node Kubernete cluster using Virtualbox/VMWareFusion
minikube start;

# Enables a plugin that allows minikube to use a local docker repository,
# so we don't have to use DockerHub or GCR.
minikube addons enable registry;

# Enables an nginx frontend that will route incoming requests to different services
minikube addons enable ingress;
```

## 1.4 Create a new Anaconda environment

```shell
conda create --name kubernetes-experiment python=3.7;
conda activate kubernetes-experiment;
```

# 2. Set up Kubernetes Dashboard Web UI

Kubernetes comes with an admin dashboard that shows information about the cluster, such as what
pods are running and what jobs have run.

## 2.1 Install web UI

```shell
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0-rc5/aio/deploy/recommended.yaml;
```

## 2.2 Create admin user with cluster admin role

In order to access the dashboard, we need to create an admin account and give the account the cluster-admin role.

```shell
kubectl apply -f kubernetes/kube-dash/admin-user.yaml;
kubectl apply -f kubernetes/kube-dash/cluster-role.yaml;
```

## 2.3 Viewing the web UI

To view the dashboard, we need to run this command in a separate terminal:

```shell
kubectl proxy
```

Now we can view the dashboard at: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/

## 2.4 Logging in to the web UI

To log in to the web UI we need to get an access token, which can be done with this command:

```shell
kubectl -n kubernetes-dashboard describe secret $(kubectl -n kubernetes-dashboard get secret | grep admin-user | awk '{print $1}')
```

Copy and paste this token into the web UI.

## 2.5 Resources:

- https://github.com/kubernetes/dashboard
- https://github.com/kubernetes/dashboard/blob/master/docs/user/access-control/creating-sample-user.md
