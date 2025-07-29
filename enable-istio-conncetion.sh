#!/bin/bash

DEST_RULE_NS="istio-config"

kubectl get svc --all-namespaces -o json | jq -r '
  .items[] |
  select(.metadata.name | startswith("hif")) |
  "\(.metadata.name) \(.metadata.namespace)"
' | while read -r svc_name svc_ns; do
  host="${svc_name}.${svc_ns}.svc.cluster.local"

  cat <<EOF > dr-${svc_name}-${svc_ns}.yaml
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: ${svc_name}-dr
  namespace: ${DEST_RULE_NS}
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
    outlierDetection:
      consecutiveGatewayErrors: 5
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
    retries:
      attempts: 3
      perTryTimeout: 2s
EOF

  echo "Generated DestinationRule with targeted circuit breaker for $host"
done
