# Day 1: Setup & First Deployment

## 🎯 Goal
Get minikube running and deploy your first application to Kubernetes.

---

## Step 1: Start Minikube

For M3 MacBook Air, we use the Docker driver (most compatible):

```bash
# Start minikube with Docker driver
minikube start --driver=docker

# Verify it's running
minikube status
```

**Expected Output:**
```
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

---

## Step 2: Explore kubectl Basics

```bash
# See cluster info
kubectl cluster-info

# See all nodes (just minikube for local)
kubectl get nodes

# See all pods across all namespaces
kubectl get pods -A
```

---

## Step 3: Deploy Your First App

### Option A: Imperative (Quick)

```bash
# Create a deployment
kubectl create deployment hello-world --image=nginx

# See the deployment
kubectl get deployments

# See the pod created by deployment
kubectl get pods

# Get detailed info about the pod
kubectl describe pod <pod-name>
```

### Option B: Declarative (Best Practice)

Create `my-first-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-first-pod
  labels:
    app: hello
spec:
  containers:
  - name: hello-container
    image: nginx:latest
    ports:
    - containerPort: 80
```

Apply it:

```bash
kubectl apply -f my-first-pod.yaml
kubectl get pods
kubectl describe pod my-first-pod
```

---

## Step 4: Access Your App

```bash
# Expose the deployment as a service
kubectl expose deployment hello-world --type=NodePort --port=80

# See the service
kubectl get services

# Access via minikube
minikube service hello-world
```

This opens your browser to the nginx welcome page!

---

## Step 5: Explore the Pod

```bash
# View logs
kubectl logs <pod-name>

# Execute command inside pod
kubectl exec -it <pod-name> -- /bin/sh

# Inside the pod:
ls
cat /etc/nginx/nginx.conf
exit
```

---

## Step 6: Minikube Dashboard

```bash
# Open the Kubernetes dashboard
minikube dashboard
```

This gives you a visual interface to explore your cluster!

---

## 🧹 Cleanup

```bash
# Delete the deployment and service
kubectl delete deployment hello-world
kubectl delete service hello-world
kubectl delete pod my-first-pod

# Stop minikube (preserves data)
minikube stop

# Delete minikube completely (start fresh)
minikube delete
```

---

## ✅ Day 1 Checkpoint

You should be able to:
- [ ] Start/stop minikube
- [ ] Use `kubectl get` to see resources
- [ ] Use `kubectl describe` for details
- [ ] Use `kubectl logs` to see container output
- [ ] Use `kubectl exec` to run commands in a container
- [ ] Create a pod both imperatively and declaratively

---

## 📝 Practice Exercises

1. Deploy a different image (try `httpd:latest` - Apache)
2. Create a pod with resource limits (CPU: 100m, Memory: 128Mi)
3. Create two pods and try to ping between them

---

## 🔗 Files in This Directory

- `my-first-pod.yaml` - Simple pod definition
- `hello-deployment.yaml` - Deployment example
- `hello-service.yaml` - Service example

---

**Next: Day 2 - Core Concepts (Pods, Deployments, Services in depth) →**

---

## 📅 Recent Update
This README was updated on January 8, 2025 as part of a git commit demonstration.

