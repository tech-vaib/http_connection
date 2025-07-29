#!/bin/bash

for svc in $(kubectl get svc --all-namespaces -o json | jq -r '.items[] | "\(.metadata.name) \(.metadata.namespace)"'); do
  svc_name=$(echo $svc | awk '{print $1}')
  svc_ns=$(echo $svc | awk '{print $2}')
  host="${svc_name}.${svc_ns}.svc.cluster.local"

  cat <<EOF > dr-${svc_name}-${svc_ns}.yaml
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: ${svc_name}-dr
  namespace: istio-config  # or $svc_ns if you prefer per-namespace
spec:
  host: ${host}
  exportTo:
    - "*"
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http2MaxRequests: 500
        http1MaxPendingRequests: 100
        maxRequestsPerConnection: 50
EOF

done
