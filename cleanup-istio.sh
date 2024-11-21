#!/bin/bash

ISTIO_DOWNLOAD_DIR=~/Downloads/istio-1.24.0

kubectl delete -f $ISTIO_DOWNLOAD_DIR/samples/addons/prometheus.yaml
kubectl delete -f $ISTIO_DOWNLOAD_DIR/samples/addons/kiali.yaml
kubectl delete -f $ISTIO_DOWNLOAD_DIR/samples/addons/grafana.yaml
kubectl delete -f policy/authz.yaml
kubectl delete -f policy/se-openai.yaml
istioctl waypoint delete --all
istioctl waypoint delete --all -n istio-egress
istioctl waypoint delete --all -n ollama

kubectl label namespace default istio.io/dataplane-mode-
kubectl label namespace istio-egress istio.io/dataplane-mode-
kubectl label namespace istio-egress istio.io/use-waypoint-

istioctl uninstall --purge

