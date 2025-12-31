# 🧪 Lab 2: Deploying with YAML Files
## Day 1 | Duration: ~45 minutes

---

## Why YAML?

Imperative (commands) = quick and dirty
Declarative (YAML) = **repeatable, version-controlled, production-ready**

---

## ✅ Prerequisites
- Minikube running (`minikube start`)
- Completed Lab 1

---

## Part 1: Your First Pod YAML

### Step 1.1: Navigate to Practical Folder

```bash
cd ~/dockerlearning/practical/day1-setup
```

### Step 1.2: Look at the Pod YAML

```bash
cat my-first-pod.yaml
```

**Understand each part:**
```yaml
apiVersion: v1        # Which API version
kind: Pod             # What resource type
metadata:
  name: my-first-pod  # Name of the pod
  labels:
    app: hello        # Labels for organization
spec:
  containers:
  - name: hello-container
    image: nginx:latest
    ports:
    - containerPort: 80
    resources:         # Resource management
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
```

### Step 1.3: Apply the YAML

```bash
kubectl apply -f my-first-pod.yaml
```

**Expected:** `pod/my-first-pod created`

### Step 1.4: Verify

```bash
kubectl get pods
```

```bash
kubectl describe pod my-first-pod
```

**Look for:** Resource requests/limits in the output

---

## Part 2: Create a Deployment YAML from Scratch

### Step 2.1: Create a New File

```bash
nano web-deployment.yaml
```

### Step 2.2: Type This YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

### Step 2.3: Apply the Deployment

```bash
kubectl apply -f web-deployment.yaml
```

### Step 2.4: Watch Pods Come Up

```bash
kubectl get pods -l app=web -w
```

**Notice:** 2 pods created (because replicas: 2)

Press `Ctrl+C` when both are Running.

---

## Part 3: Create a Service YAML

### Step 3.1: Create Service File

```bash
nano web-service.yaml
```

### Step 3.2: Type This YAML

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web        # Matches pods with label app=web
  type: NodePort
  ports:
  - port: 80        # Service port
    targetPort: 80  # Container port
    nodePort: 30080 # External port (30000-32767)
```

**Save:** `Ctrl+X`, `Y`, `Enter`

### Step 3.3: Apply the Service

```bash
kubectl apply -f web-service.yaml
```

### Step 3.4: Access Your App

```bash
minikube service web-service
```

**Browser opens with nginx!**

---

## Part 4: Update Your Deployment

### Step 4.1: Edit the Deployment

```bash
nano web-deployment.yaml
```

**Change replicas from 2 to 4:**
```yaml
spec:
  replicas: 4    # Changed from 2
```

**Save the file**

### Step 4.2: Apply Changes

```bash
kubectl apply -f web-deployment.yaml
```

**Expected:** `deployment.apps/web-app configured`

### Step 4.3: Watch Scaling

```bash
kubectl get pods -l app=web
```

**Now 4 pods!**

### Step 4.4: Change the Image Version

```bash
nano web-deployment.yaml
```

**Change image from nginx:1.21 to nginx:1.23:**
```yaml
      containers:
      - name: nginx
        image: nginx:1.23    # Changed version
```

**Save**

### Step 4.5: Apply Rolling Update

```bash
kubectl apply -f web-deployment.yaml
```

### Step 4.6: Watch the Rolling Update

```bash
kubectl rollout status deployment/web-app
```

**See:** Old pods terminated, new pods created (zero downtime!)

```bash
kubectl get pods -l app=web
```

**All pods now running nginx:1.23**

---

## Part 5: Multi-Resource YAML

You can put multiple resources in one file!

### Step 5.1: Look at Combined File

```bash
cat hello-deployment.yaml
```

**Notice:** Two resources separated by `---`
- Deployment
- Service

### Step 5.2: Apply Combined File

```bash
kubectl apply -f hello-deployment.yaml
```

**Creates both resources at once!**

---

## Part 6: Useful YAML Commands

### Dry Run (Test without applying)

```bash
kubectl apply -f web-deployment.yaml --dry-run=client
```

### See What Would Change

```bash
kubectl diff -f web-deployment.yaml
```

### Generate YAML from Running Resource

```bash
kubectl get deployment web-app -o yaml > exported-deployment.yaml
```

### Validate YAML Syntax

```bash
kubectl apply -f web-deployment.yaml --validate=true --dry-run=client
```

---

## Part 7: Clean Up

### Step 7.1: Delete Using YAML Files

```bash
kubectl delete -f web-service.yaml
kubectl delete -f web-deployment.yaml
kubectl delete -f my-first-pod.yaml
kubectl delete -f hello-deployment.yaml
```

### Step 7.2: Verify

```bash
kubectl get all
```

**Should only show kubernetes service**

---

## 🎯 What You Learned

✅ YAML structure for Pods, Deployments, Services
✅ `kubectl apply -f` for declarative management
✅ Rolling updates by changing YAML
✅ Multi-resource YAML files
✅ Dry-run and validation

---

## 📝 Practice Exercise

Create a YAML file for:
1. A deployment called `httpd-app` with 3 replicas of `httpd:latest`
2. A NodePort service on port 30090

Try it yourself, then check solution:

<details>
<summary>Click for Solution</summary>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: httpd-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: httpd
  template:
    metadata:
      labels:
        app: httpd
    spec:
      containers:
      - name: httpd
        image: httpd:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: httpd-service
spec:
  selector:
    app: httpd
  type: NodePort
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30090
```

</details>

---

## 🚀 Next Lab

**Lab 3:** ConfigMaps, Secrets, and Environment Variables

