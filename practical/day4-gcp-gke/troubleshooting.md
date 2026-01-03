# 🐛 GKE Troubleshooting Guide

## Common GKE Issues & Solutions

### Issue: `gcloud container clusters create-auto` fails

**Error:** `PERMISSION_DENIED` or billing not enabled

**Solution:**
```bash
# Check billing
gcloud billing accounts list

# Enable Kubernetes Engine API
gcloud services enable container.googleapis.com

# Check project permissions
gcloud projects get-iam-policy $(gcloud config get-value project) --flatten="bindings[].members" --filter="bindings.role:roles/container.admin"
```

### Issue: `kubectl get nodes` shows no nodes

**Error:** Connection issues or cluster not ready

**Solution:**
```bash
# Check cluster status
gcloud container clusters describe ml-interview-cluster --region=us-central1 --format="value(status)"

# Reconnect if needed
gcloud container clusters get-credentials ml-interview-cluster --region=us-central1

# Check cluster events
kubectl get events --sort-by=.metadata.creationTimestamp | tail -10
```

### Issue: Image pull fails on GKE

**Error:** `ImagePullBackOff` with GCR images

**Solution:**
```bash
# Authenticate Docker with GCR
gcloud auth configure-docker

# Check if image exists
gcloud container images list --repository=gcr.io/$(gcloud config get-value project)

# Verify image name in deployment
kubectl describe pod <pod-name> -n ml-platform | grep "Image:"

# Check image pull secrets (usually not needed with GCR)
kubectl get secrets -n ml-platform
```

### Issue: PVC stuck in Pending

**Error:** `kubectl get pvc` shows STATUS: Pending

**Solution:**
```bash
# Check PVC details
kubectl describe pvc model-pvc -n ml-platform

# Check storage class availability
kubectl get storageclass

# Check GKE storage availability
gcloud compute regions describe us-central1 --format="value(quotas[0].metric)"

# Try different storage class
kubectl patch pvc model-pvc -n ml-platform -p '{"spec":{"storageClassName":"standard"}}'
```

### Issue: LoadBalancer service stuck without external IP

**Error:** `EXTERNAL-IP` shows `<pending>`

**Solution:**
```bash
# Check service events
kubectl describe service ml-api-service -n ml-platform

# GKE LoadBalancer creation can take 2-5 minutes
kubectl get service ml-api-service -n ml-platform -w

# Check GCP load balancer status
gcloud compute forwarding-rules list --filter="region:us-central1"

# If stuck too long, check quotas
gcloud compute regions describe us-central1 --format="value(quotas[2].metric,quotas[2].limit,quotas[2].usage)"
```

### Issue: HPA not working

**Error:** HPA shows `<unknown>` for metrics

**Solution:**
```bash
# Check if metrics server is running (GKE has it built-in)
kubectl get deployment metrics-server -n kube-system

# Check HPA status
kubectl describe hpa ml-api-hpa -n ml-platform

# Verify resource metrics are available
kubectl top pods -n ml-platform

# Check cluster autoscaling settings
gcloud container clusters describe ml-interview-cluster --region=us-central1 --format="value(autoscaling.enableNodeAutoprovisioning)"
```

### Issue: Pod OOM Killed on GKE

**Error:** Pod status shows `OOMKilled`

**Solution:**
```bash
# Check pod resource usage
kubectl describe pod <pod-name> -n ml-platform | grep -A 10 "Containers:"

# Check GKE node capacity
kubectl describe node | grep -A 10 "Capacity:"

# Increase memory limits
kubectl patch deployment ml-api -n ml-platform --type='json' \
  -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "2Gi"}]'

# Check for memory leaks in application
kubectl logs <pod-name> -n ml-platform --previous | grep -i memory
```

### Issue: Workload Identity not working

**Error:** GCS access denied despite Workload Identity setup

**Solution:**
```bash
# Verify service account annotation
kubectl describe serviceaccount ml-k8s-sa -n ml-platform

# Check IAM policy binding
gcloud iam service-accounts get-iam-policy \
  ml-production-sa@$(gcloud config get-value project).iam.gserviceaccount.com

# Test with manual key (temporary)
kubectl create secret generic gcp-key --from-file=key.json=/path/to/key.json -n ml-platform
kubectl patch deployment ml-api -n ml-platform --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/env", "value": [{"name": "GOOGLE_APPLICATION_CREDENTIALS", "value": "/key/key.json"}]}]'
kubectl patch deployment ml-api -n ml-platform --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/volumes", "value": [{"name": "gcp-key", "secret": {"secretName": "gcp-key"}}]}]'
kubectl patch deployment ml-api -n ml-platform --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/volumeMounts", "value": [{"name": "gcp-key", "mountPath": "/key"}]}]'
```

---

## Quick Diagnostic Commands

```bash
# Full cluster health check
kubectl get all -n ml-platform
kubectl get pvc -n ml-platform
kubectl get hpa -n ml-platform
kubectl top pods -n ml-platform
kubectl top nodes

# Recent events
kubectl get events -n ml-platform --sort-by=.metadata.creationTimestamp | tail -20

# GCP resource check
gcloud compute instances list
gcloud compute disks list
gcloud container clusters list

# Cost monitoring
gcloud billing export projects describe $(gcloud config get-value project)
```

---

## Emergency Cost Controls

If costs spiral out of control:

```bash
# Delete everything immediately
kubectl delete namespace ml-platform
gcloud container clusters delete ml-interview-cluster --region=us-central1 --quiet
gcloud compute instances delete $(gcloud compute instances list --format="value(name)") --quiet
gcloud compute disks delete $(gcloud compute disks list --format="value(name)") --quiet

# Check final bill
gcloud billing export projects describe $(gcloud config get-value project)
```

---

## GKE vs Minikube Differences

| Feature | Minikube | GKE Autopilot |
|---------|----------|----------------|
| Node management | Manual | Automatic |
| Storage | HostPath | GCP Persistent Disk |
| Networking | Local | GCP VPC |
| LoadBalancer | NodePort | GCP Load Balancer |
| Monitoring | Basic | Cloud Monitoring |
| Cost | Free | Free cluster, pay per pod |
| Scaling | Manual | Automatic |

---

## Getting Help

1. **GKE Documentation:** https://cloud.google.com/kubernetes-engine/docs
2. **Stack Overflow:** Search for `[google-kubernetes-engine]` tag
3. **GCP Console Logs:** Check under "Logging" → "Logs Explorer"
4. **kubectl debug:** `kubectl debug pod/<pod-name> -n ml-platform --image=busybox`
