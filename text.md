Register required AKS feature flags (only once per subscription)

az feature register --namespace "Microsoft.ContainerService" --name "EnableIstioAddonsPreview"
az provider register --namespace Microsoft.ContainerService

⚠️ Wait for the feature to be in the "Registered" state:
az feature show --namespace "Microsoft.ContainerService" --name "EnableIstioAddonsPreview" --query "state"


Enable Istio CNI on an existing AKS cluster
az aks enable-addons \
  --addons istiocni,istio-base,istio-ingress \
  --name <CLUSTER_NAME> \
  --resource-group <RESOURCE_GROUP>

Verify Istio CNI DaemonSet is running

kubectl get daemonset istio-cni-node -n kube-system
------------
Confirm It’s Working (No init container)

Deploy a test app with automatic sidecar injection:
kubectl label namespace default istio-injection=enabled
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.21/samples/helloworld/helloworld.yaml
kubectl get pod -l app=helloworld -o jsonpath='{.spec.initContainers}'

Create an AKS cluster with the Istio CNI add-on enabled
az aks create \
  --resource-group <RESOURCE_GROUP> \
  --name <CLUSTER_NAME> \
  --enable-istio-base-addon \
  --enable-istio-cni-addon \
  --enable-istio-ingress-addon \
  --network-plugin azure \
  --node-count 3 \
  --generate-ssh-keys


  kubectl get svc --all-namespaces -o json | jq -r '.items[] | select(.metadata.name | test("backend")) | "\(.metadata.name).\(.metadata.namespace).svc.cluster.local"'

kubectl get svc --all-namespaces -o custom-columns=HOST:.metadata.name,NAMESPACE:.metadata.namespace | tail -n +2 | awk '{print $1"."$2".svc.cluster.local"}'

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


