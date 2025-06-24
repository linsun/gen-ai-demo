kubectl delete -f policy/
kubectl label namespace default istio.io/dataplane-mode-
istioctl waypoint delete waypoint 
kubectl delete pod --all -n istio-egress
kubectl label namespace default istio.io/use-waypoint-
