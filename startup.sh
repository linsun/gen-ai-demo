#!/bin/bash

echo "Create the kind cluster..."
kind create cluster --config cluster.yaml

docker pull docker.io/linsun/demo:latest
docker pull docker.io/curlimages/curl
docker pull docker.io/ollama/ollama:latest

docker pull docker.io/istio/proxyv2:1.24.0-distroless
docker pull docker.io/istio/pilot:1.24.0-distroless
docker pull docker.io/istio/install-cni:1.24.0-distroless
docker pull docker.io/istio/ztunnel:1.24.0-distroless
docker pull docker.io/istio/pilot:1.24.0-distroless
docker pull ghcr.io/prometheus-operator/prometheus-config-reloader:v0.76.0
docker pull docker.io/prom/prometheus:v2.54.1
docker pull quay.io/kiali/kiali:v2.0


kind load docker-image docker.io/linsun/demo:latest
kind load docker-image docker.io/curlimages/curl
kind load docker-image docker.io/ollama/ollama:latest

kind load docker-image docker.io/istio/proxyv2:1.24.0-distroless
kind load docker-image docker.io/istio/pilot:1.24.0-distroless
kind load docker-image docker.io/istio/install-cni:1.24.0-distroless
kind load docker-image docker.io/istio/ztunnel:1.24.0-distroless
kind load docker-image docker.io/istio/pilot:1.24.0-distroless
kind load docker-image ghcr.io/prometheus-operator/prometheus-config-reloader:v0.76.0
kind load docker-image docker.io/prom/prometheus:v2.54.1
kind load docker-image quay.io/kiali/kiali:v2.0

echo "Applying the Kubernets manifests..."
kubectl apply -f kubernetes/demo.yaml
kubectl apply -f kubernetes/ollama.yaml
kubectl apply -f kubernetes/client.yaml
# Replace below with your own secret file
kubectl apply -f ../openai-secret.yaml

sleep 10
# pull the 2 models
kubectl exec -it deploy/client -- curl http://ollama.ollama:11434/api/pull -d '{"name": "llama3.2"}'
kubectl exec -it deploy/client -- curl http://ollama.ollama:11434/api/pull -d '{"name": "llava"}'