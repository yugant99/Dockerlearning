# 🚀 JupyterHub on GKE - Quick Start

## Prerequisites ✅

- [ ] GKE cluster running (`kubectl get nodes` works)
- [ ] Helm installed (`helm version`)
- [ ] GCP project set (`gcloud config get-value project`)
- [ ] Google OAuth credentials created

## Step 1: Setup (5 minutes)

```bash
cd practical/day5-jupyter-gke

# Run setup script
./setup-jupyterhub.sh
```

## Step 2: Configure OAuth (5 minutes)

**Option A: ngrok (Recommended for Testing)**
```bash
# Install ngrok
brew install ngrok
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Start tunnel
ngrok http 80
# Copy the https://abc123.ngrok.io URL
```

**Option B: Localhost (For local testing only)**
- Use `http://localhost:8000/hub/oauth_callback`

**Google Console Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID (Web application)
3. Add authorized redirect URI:
   - For ngrok: `https://abc123.ngrok.io/hub/oauth_callback`
   - For localhost: `http://localhost:8000/hub/oauth_callback`
4. Update `jupyterhub-values.yaml`:
   ```yaml
   hub:
     config:
       JupyterHub:
         GoogleOAuthenticator:
           client_id: "your-client-id.apps.googleusercontent.com"
           client_secret: "your-client-secret"
           oauth_callback_url: "https://abc123.ngrok.io/hub/oauth_callback"  # Use your ngrok URL
   ```

## Step 3: Deploy (10 minutes)

```bash
# Deploy JupyterHub
helm upgrade --install jupyterhub jupyterhub/jupyterhub \
  --namespace jupyterhub \
  --values jupyterhub-values.yaml \
  --values singleuser-profileList.yaml \
  --wait \
  --timeout 600s
```

## Step 4: Access (2 minutes)

```bash
# Get external IP (wait for it to appear)
kubectl get service proxy-public -n jupyterhub -w

# Open in browser
EXTERNAL_IP=$(kubectl get service proxy-public -n jupyterhub -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
open http://$EXTERNAL_IP
```

## Expected Result 🎉

- JupyterHub login page with Google OAuth
- Select "Data Science Environment"
- Personal Jupyter server with ML libraries
- Persistent storage for your work

## Cost Estimate 💰

- **LoadBalancer**: ~$0.025/hour
- **Storage**: ~$0.04/GB/month per user
- **Compute**: Based on user pod usage

## Cleanup 🧹

```bash
helm uninstall jupyterhub -n jupyterhub
kubectl delete namespace jupyterhub
```

---

## 🎯 What You'll Learn

- Multi-user Jupyter platform architecture
- OAuth authentication integration
- Kubernetes resource management
- Custom Docker images for data science
- GKE LoadBalancer and storage classes
- User isolation and persistence

---

**Time: ~20 minutes active | Skills: JupyterHub, OAuth, multi-user platforms**
