# 🧪 Lab 1: Minikube Setup & First Deployment
## Day 1 | Duration: ~45 minutes

---

## ✅ Prerequisites
- Docker Desktop running
- Terminal open
- You completed `brew install minikube` (already done!)

---

## Part 1: Start Your Kubernetes Cluster

### Step 1.1: Start Minikube

```bash
minikube start --driver=docker
```

**Expected output:**
```
✅ minikube v1.37.0 on Darwin 14.5 (arm64)
✅ Using the docker driver based on user configuration
✅ Starting "minikube" primary control-plane node...
✅ Done! kubectl is now configured to use "minikube" cluster
```

### Step 1.2: Verify It's Running

```bash
minikube status
```

**Expected output:**
```
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

### Step 1.3: Check kubectl Connection

```bash
kubectl cluster-info
```

**Expected output:**
```
Kubernetes control plane is running at https://127.0.0.1:XXXXX
CoreDNS is running at https://127.0.0.1:XXXXX/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

🎉 **Checkpoint:** Your Kubernetes cluster is running!

---

## Part 2: Explore the Cluster

### Step 2.1: See Your Nodes

```bash
kubectl get nodes
```

**Expected:** One node called "minikube" with STATUS "Ready"

### Step 2.2: See System Pods

```bash
kubectl get pods -A
```

**What you'll see:** System pods in `kube-system` namespace:
- `coredns-*` - DNS service
- `etcd-minikube` - Key-value store
- `kube-apiserver-minikube` - API server
- `kube-controller-manager-minikube` - Controller
- `kube-scheduler-minikube` - Scheduler
- `kube-proxy-*` - Network proxy

### Step 2.3: Open the Dashboard (Optional but cool!)

```bash
minikube dashboard
```

**What happens:** Opens a web browser with Kubernetes Dashboard UI

Press `Ctrl+C` to stop when done exploring.

---

## Part 3: Deploy Your First App (Imperative Way)

### Step 3.1: Create a Deployment

```bash
kubectl create deployment hello-nginx --image=nginx
```

**Expected:** `deployment.apps/hello-nginx created`

### Step 3.2: Watch It Come Up

```bash
kubectl get pods -w
```

**Watch the STATUS change:**
```
NAME                           READY   STATUS              RESTARTS   AGE
hello-nginx-xxxxx-xxxxx        0/1     ContainerCreating   0          2s
hello-nginx-xxxxx-xxxxx        1/1     Running             0          15s
```

Press `Ctrl+C` to stop watching.

### Step 3.3: Get Deployment Details

```bash
kubectl get deployments
```

```bash
kubectl describe deployment hello-nginx
```

**Look for:**
- Replicas: 1 desired, 1 available
- Pod Template with nginx image
- Events showing deployment progress

---

## Part 4: Expose Your App

### Step 4.1: Create a Service

```bash
kubectl expose deployment hello-nginx --type=NodePort --port=80
```

**Expected:** `service/hello-nginx exposed`

### Step 4.2: See the Service

```bash
kubectl get services
```

**Expected output:**
```
NAME          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
hello-nginx   NodePort    10.x.x.x        <none>        80:3XXXX/TCP   5s
kubernetes    ClusterIP   10.96.0.1       <none>        443/TCP        10m
```

### Step 4.3: Access Your App!

```bash
minikube service hello-nginx
```

**What happens:** Opens browser to nginx welcome page! 🎉

---

## Part 5: Explore Your Pod

### Step 5.1: Get Pod Name

```bash
kubectl get pods
```

Copy the pod name (e.g., `hello-nginx-xxxxx-xxxxx`)

### Step 5.2: View Logs

```bash
kubectl logs hello-nginx-xxxxx-xxxxx
```

(Replace with your actual pod name)

### Step 5.3: Execute Command Inside Pod

```bash
kubectl exec -it hello-nginx-xxxxx-xxxxx -- /bin/bash
```

**You're now INSIDE the container!** Try:

```bash
# Inside the pod:
ls
cat /etc/nginx/nginx.conf
curl localhost
exit
```

### Step 5.4: Describe the Pod

```bash
kubectl describe pod hello-nginx-xxxxx-xxxxx
```

**Look for:**
- Status: Running
- IP: The pod's internal IP
- Containers: nginx with port 80
- Events: Scheduled, Pulled, Created, Started

---

## Part 6: Scale Your App

### Step 6.1: Scale Up

```bash
kubectl scale deployment hello-nginx --replicas=3
```

### Step 6.2: Watch Pods Scale

```bash
kubectl get pods -w
```

**See 3 pods come up!** Press `Ctrl+C` when all are Running.

### Step 6.3: Verify

```bash
kubectl get deployment hello-nginx
```

**Expected:** `READY 3/3`

---

## Part 7: Clean Up

### Step 7.1: Delete Service

```bash
kubectl delete service hello-nginx
```

### Step 7.2: Delete Deployment

```bash
kubectl delete deployment hello-nginx
```

### Step 7.3: Verify Clean

```bash
kubectl get all
```

**Should only show:** `kubernetes` service

### Step 7.4: (Optional) Stop Minikube

```bash
minikube stop
```

**Note:** Use `minikube start` to restart later. Your data is preserved.

---

## 🎯 What You Learned

✅ How to start/stop minikube
✅ Basic kubectl commands: get, describe, logs, exec
✅ Creating deployments imperatively
✅ Exposing services with NodePort
✅ Scaling applications
✅ Cleaning up resources

---

## 🚀 Next Lab

**Lab 2:** Deploy using YAML files (the right way!)

---

## 🆘 Troubleshooting

**Pod stuck in "Pending"?**
```bash
kubectl describe pod <pod-name>
# Check Events section for errors
```

**Can't access service?**
```bash
minikube service hello-nginx --url
# Copy URL and open manually
```

**Minikube won't start?**
```bash
minikube delete
minikube start --driver=docker
```

