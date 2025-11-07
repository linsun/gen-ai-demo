#!/bin/bash

# TAG=$(curl https://storage.googleapis.com/istio-build/dev/latest)
# TAG=1.24-alpha.6a458274241dd51fbd6e015e7f439a29e8beb07f
# istioctl install --set tag=$TAG --set hub=gcr.io/istio-testing --set profile=ambient --skip-confirmation  --set meshConfig.accessLogFile=/dev/stdout --set values.pilot.env.PILOT_ENABLE_IP_AUTOALLOCATE=true --set  values.cni.ambient.dnsCapture=true

istioctl install --set profile=ambient --skip-confirmation  --set meshConfig.accessLogFile=/dev/stdout

kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null || \
  kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.0/experimental-install.yaml

# change this to your istio dir
ISTIO_DOWNLOAD_DIR=~/Downloads/istio-1.28.0

kubectl apply -f $ISTIO_DOWNLOAD_DIR/samples/addons/prometheus.yaml
kubectl apply -f $ISTIO_DOWNLOAD_DIR/samples/addons/kiali.yaml
# kubectl apply -f $ISTIO_DOWNLOAD_DIR/samples/addons/grafana.yaml

kubectl label ns default istio.io/dataplane-mode=ambient
istioctl waypoint apply --enroll-namespace --namespace default --overwrite

kubectl apply -f kubernetes/client.yaml
kubectl apply -f kubernetes/demo-route.yaml
kubectl apply -f kubernetes/demo.yaml
kubectl apply -f kubernetes/ingress-gateway.yaml
kubectl apply -f kubernetes/demo-http-route.yaml
kubectl apply -f kubernetes/rag-v1.yaml
kubectl apply -f kubernetes/rag-v2.yaml
kubectl apply -f kubernetes/rag-httproute.yaml
# istioctl waypoint apply --enroll-namespace --namespace default --overwrite

kubectl create ns istio-egress
kubectl label ns istio-egress istio.io/dataplane-mode=ambient
istioctl waypoint apply --enroll-namespace --namespace istio-egress --overwrite
kubectl apply -f policy/se-ollama.yaml

# kubectl label ns default istio.io/dataplane-mode=ambient
