# 🐛 JupyterHub on GKE Troubleshooting

## Common Issues & Solutions

### Issue: Helm installation fails

**Error:** `Error: release jupyterhub failed: ...`

**Solutions:**
```bash
# Check namespace exists
kubectl get namespace jupyterhub

# Check Helm status
helm list -n jupyterhub

# Force reinstall if needed
helm uninstall jupyterhub -n jupyterhub
helm install jupyterhub jupyterhub/jupyterhub --namespace jupyterhub --values jupyterhub-values.yaml
```

### Issue: OAuth login fails

**Error:** Redirect URI mismatch or invalid client

**Solutions:**
```bash
# Check OAuth callback URL in Google Cloud Console
# Should match: https://your-domain/hub/oauth_callback

# Verify client ID and secret in values.yaml
kubectl get secret -n jupyterhub | grep oauth

# Check hub logs for OAuth errors
kubectl logs -f deployment/hub -n jupyterhub | grep oauth
```

### Issue: User server won't start

**Error:** Pod stuck in Pending or user server fails

**Solutions:**
```bash
# Check user server logs
kubectl logs -f deployment/user-scheduler -n jupyterhub

# Check resource availability
kubectl describe pod -n jupyterhub -l component=singleuser

# Verify image exists
gcloud container images describe gcr.io/your-project/jupyter-datascience:v1

# Check PVC creation
kubectl get pvc -n jupyterhub
```

### Issue: LoadBalancer stuck on <pending>

**Error:** EXTERNAL-IP shows `<pending>` for long time

**Solutions:**
```bash
# Check LoadBalancer events
kubectl describe service proxy-public -n jupyterhub

# Check GCP LoadBalancer status
gcloud compute forwarding-rules list --filter="region:us-central1"

# Verify quota limits
gcloud compute regions describe us-central1 --format="value(quotas[2].metric,quotas[2].limit,quotas[2].usage)"
```

### Issue: Custom image not found

**Error:** `ErrImagePull` or `ImagePullBackOff`

**Solutions:**
```bash
# Verify image was built and pushed
gcloud container images list --repository=gcr.io/your-project

# Check image tags
gcloud container images list-tags gcr.io/your-project/jupyter-datascience

# Rebuild if needed
docker buildx build --platform linux/amd64 -f Dockerfile.datascience -t gcr.io/your-project/jupyter-datascience:v2 --push .
```

### Issue: GPU workloads fail

**Error:** GPU pod stuck in Pending

**Solutions:**
```bash
# Check if GPU node pool exists
gcloud container node-pools list --cluster your-cluster --region us-central1

# Verify GPU quota
gcloud compute regions describe us-central1 --format="value(quotas[10].metric,quotas[10].limit,quotas[10].usage)"

# Check pod tolerations and requests
kubectl describe pod -n jupyterhub user-pod-name
```

### Issue: Storage/PVC issues

**Error:** User data not persisting

**Solutions:**
```bash
# Check PVC creation
kubectl get pvc -n jupyterhub

# Verify storage class
kubectl get storageclass

# Check PVC events
kubectl describe pvc claim-username -n jupyterhub
```

### Issue: JupyterHub admin access

**Problem:** Need admin access for user management

**Solutions:**
```bash
# Add admin users in values.yaml
hub:
  config:
    JupyterHub:
      admin_users:
        - your-email@domain.com

# Restart hub
kubectl rollout restart deployment/hub -n jupyterhub
```

## Useful Commands

```bash
# Full JupyterHub status
kubectl get all -n jupyterhub

# Check user pods
kubectl get pods -n jupyterhub -l component=singleuser

# Hub logs
kubectl logs -f deployment/hub -n jupyterhub

# User scheduler logs
kubectl logs -f deployment/user-scheduler -n jupyterhub

# Proxy logs
kubectl logs -f deployment/proxy -n jupyterhub

# Clean restart
helm upgrade jupyterhub jupyterhub/jupyterhub --namespace jupyterhub --values jupyterhub-values.yaml --values singleuser-profileList.yaml
```

## GCP-Specific Monitoring

```bash
# Cloud Logging for JupyterHub
# GCP Console → Logging → Logs Explorer
# Filter: resource.labels.namespace_name="jupyterhub"

# Monitor LoadBalancer
gcloud compute forwarding-rules describe jupyterhub-rule --region=us-central1

# Check cluster autoscaling
gcloud container clusters describe your-cluster --region=us-central1 --format="value(autoscaling.enableNodeAutoprovisioning)"
```

## Performance Tuning

```bash
# Check resource usage
kubectl top pods -n jupyterhub
kubectl top nodes

# Adjust user pod limits in profileList
# Increase hub resources if needed
hub:
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1000m
      memory: 2Gi
```

## Emergency Cleanup

```bash
# Stop all user servers
kubectl delete pods -n jupyterhub -l component=singleuser

# Reset JupyterHub
helm uninstall jupyterhub -n jupyterhub
kubectl delete namespace jupyterhub

# Clean up orphaned resources
gcloud compute disks list --filter="name~jupyterhub"
gcloud compute forwarding-rules list --filter="region:us-central1"
```
