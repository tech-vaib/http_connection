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
=====================
kubectl get pods -n istio-system
kubectl get namespace -L istio-injection
##Check if any pod has the Envoy sidecar (istio-proxy) injected:

kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].name}{"\n"}{end}' | grep istio-proxy
#List Custom Resource Definitions (CRDs) related to Istio:
kubectl get crds | grep istio
#If Istio was installed via Helm:
helm list -n istio-system

#If installed via Istio Operator:
kubectl get IstioOperator -A

## disabe istio
Check which namespaces have injection enabled:
kubectl get ns --show-labels | grep istio-injection

Then disable it:
kubectl label namespace <your-namespace> istio-injection-
## If you have a MutatingWebhookConfiguration for Istio auto-injection:(global)
kubectl delete mutatingwebhookconfiguration istio-sidecar-injector
##Remove Istio sidecars from existing pods
kubectl rollout restart deployment -n <your-namespace>

##Delete Istio-related Custom Resources
kubectl delete virtualservices.networking.istio.io --all-namespaces --all
kubectl delete gateways.networking.istio.io --all-namespaces --all
kubectl delete destinationrules.networking.istio.io --all-namespaces --all

##Uninstall Istio components
istioctl uninstall --purge
##If installed via Helm:
helm uninstall istio-base -n istio-system
helm uninstall istiod -n istio-system
helm uninstall istio-ingress -n istio-system

## Step-by-Step: Enable Istio in AKS
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH

istioctl version
## Install Istio base and control plane
istioctl install --set profile=demo -y
You should see output confirming that the installation was successful.
You can also use other profiles like minimal, default, remote, etc.
## Enable automatic sidecar injection
kubectl label namespace <your-namespace> istio-injection=enabled

## verify
kubectl get namespace -L istio-injection

Istiod:
components:
  pilot:
    k8s:
      resources:
        requests:
          cpu: 500m
          memory: 512Mi
        limits:
          cpu: 2
          memory: 1Gi

Ingress Gateway:
components:
  ingressGateways:
  - name: istio-ingressgateway
    enabled: true
    k8s:
      resources:
        requests:
          cpu: 500m
          memory: 256Mi
        limits:
          cpu: 2
          memory: 512Mi

Enable autoscaling for the ingress gateway and control plane if needed:
kubectl autoscale deployment istio-ingressgateway -n istio-system --cpu-percent=70 --min=2 --max=10

=================
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: httpbin-dr
  namespace: demo
spec:
  host: httpbin.demo.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 1000
      http:
        http1MaxPendingRequests: 1000
        maxRequestsPerConnection: 100
        maxRetries: 3
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 5s
      baseEjectionTime: 30s
      maxEjectionPercent: 50

istio-config.yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: istio-highload
  namespace: istio-system
spec:
  profile: default

  meshConfig:
    accessLogFile: /dev/stdout
    enablePrometheusMerge: true
    defaultConfig:
      proxyMetadata:
        ISTIO_META_DNS_CAPTURE: "true"
        ISTIO_META_DNS_AUTO_ALLOCATE: "true"
      holdApplicationUntilProxyStarts: true

  values:
    global:
      proxy:
        resources:
          requests:
            cpu: 200m
            memory: 128Mi
          limits:
            cpu: 1000m
            memory: 256Mi
      proxy_init:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 300m
            memory: 256Mi

  components:
    pilot:
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 1000m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 2Gi
        hpaSpec:
          minReplicas: 2
          maxReplicas: 10
          metrics:
          - type: Resource
            resource:
              name: cpu
              targetAverageUtilization: 70

    ingressGateways:
    - name: istio-ingressgateway
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 1Gi
        hpaSpec:
          minReplicas: 2
          maxReplicas: 10
          metrics:
          - type: Resource
            resource:
              name: cpu
              targetAverageUtilization: 70


