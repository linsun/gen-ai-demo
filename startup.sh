#!/bin/bash

echo "Create the kind cluster..."
kind create cluster --config cluster.yaml

docker pull docker.io/linsun/demo:v2
docker pull docker.io/curlimages/curl
docker pull docker.io/linsun/rag:v1
docker pull docker.io/linsun/rag:v2

docker pull docker.io/istio/proxyv2:1.25.0-distroless
docker pull docker.io/istio/pilot:1.25.0-distroless
docker pull docker.io/istio/install-cni:1.25.0-distroless
docker pull docker.io/istio/ztunnel:1.25.0-distroless
docker pull docker.io/istio/pilot:1.25.0-distroless

kind load docker-image docker.io/linsun/demo:v2
kind load docker-image docker.io/curlimages/curl
kind load docker-image docker.io/linsun/rag:v1
kind load docker-image docker.io/linsun/rag:v2

kind load docker-image docker.io/istio/proxyv2:1.25.0-distroless
kind load docker-image docker.io/istio/pilot:1.25.0-distroless
kind load docker-image docker.io/istio/install-cni:1.25.0-distroless
kind load docker-image docker.io/istio/ztunnel:1.25.0-distroless
kind load docker-image docker.io/istio/pilot:1.25.0-distroless


echo "Applying the Kubernets manifests..."

# kubectl apply -f kubernetes/ollama.yaml
kubectl apply -f kubernetes/client.yaml
# Replace below with your own secret file
# kubectl apply -f ../openai-secret.yaml

sleep 10
# pull the 2 models
# kubectl exec -it deploy/client -- curl http://ollama.ollama:11434/api/pull -d '{"name": "llama3.2"}'
# kubectl exec -it deploy/client -- curl http://ollama.ollama:11434/api/pull -d '{"name": "llava"}'