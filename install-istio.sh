#!/bin/bash
# change this to your istio dir
ISTIO_DOWNLOAD_DIR=~/src/github.com/istio/istio/

# TAG=$(curl https://storage.googleapis.com/istio-build/dev/latest)
TAG=1.24-alpha.6a458274241dd51fbd6e015e7f439a29e8beb07f

istioctl install --set tag=$TAG --set hub=gcr.io/istio-testing --set profile=ambient --skip-confirmation  --set meshConfig.accessLogFile=/dev/stdout --set values.pilot.env.PILOT_ENABLE_IP_AUTOALLOCATE=true --set  values.cni.ambient.dnsCapture=true

kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null || \
  { kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml }

kubectl apply -f $ISTIO_DOWNLOAD_DIR/samples/addons/prometheus.yaml
kubectl apply -f $ISTIO_DOWNLOAD_DIR/samples/addons/kiali.yaml
kubectl apply -f $ISTIO_DOWNLOAD_DIR/samples/addons/grafana.yaml


kubectl label ns default istio.io/dataplane-mode=ambient
kubectl label ns ollama istio.io/dataplane-mode=ambient
