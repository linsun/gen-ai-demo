#!/bin/bash

echo "Create the kind cluster..."
kind create cluster --config cluster.yaml

kind -n llm load docker-image ghcr.io/cncf/keynote:latest

echo "Applying the Kubernets manifests..."
kubectl apply -f kubernetes/demo.yaml
kubectl apply -f kubernetes/ollama.yaml
kubectl apply -f kubernetes/client.yaml

