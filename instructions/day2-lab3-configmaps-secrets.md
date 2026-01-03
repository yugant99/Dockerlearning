# 🧪 Lab 3: ConfigMaps & Secrets
## Day 2 | Duration: ~40 minutes

---

## Why ConfigMaps & Secrets?

**Problem:** Hardcoding config in containers is bad
- Can't change without rebuilding
- Sensitive data in images = security risk

**Solution:** Externalize configuration!
- ConfigMaps = non-sensitive config
- Secrets = sensitive data (passwords, keys)

---

## ✅ Prerequisites
- Minikube running
- Navigate to workspace:
```bash
cd ~/dockerlearning/practical
mkdir -p day2-core-concepts && cd day2-core-concepts
```

---

## Part 1: ConfigMaps - From Literal Values

### Step 1.1: Create ConfigMap (Imperative)

```bash
kubectl create configmap app-config \
    --from-literal=DATABASE_HOST=postgres \
    --from-literal=DATABASE_PORT=5432 \
    --from-literal=LOG_LEVEL=info
```

### Step 1.2: View ConfigMap

```bash
kubectl get configmaps
```

```bash
kubectl describe configmap app-config
```

**See your key-value pairs!**

### Step 1.3: View as YAML

```bash
kubectl get configmap app-config -o yaml
```

**Notice the `data` section with your values**

---

## Part 2: Use ConfigMap in a Pod

### Step 2.1: Create Pod YAML

```bash
nano pod-with-configmap.yaml
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: configmap-demo
spec:
  containers:
  - name: demo
    image: busybox
    command: ["sh", "-c", "env && sleep 3600"]
    env:
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: DATABASE_HOST
    - name: DB_PORT
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: DATABASE_PORT
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: LOG_LEVEL
```

**Save the file**

### Step 2.2: Apply

```bash
kubectl apply -f pod-with-configmap.yaml
```

### Step 2.3: Verify Environment Variables

```bash
kubectl logs configmap-demo | grep -E "DB_|LOG_"
```

**Expected output:**
```
DB_HOST=postgres
DB_PORT=5432
LOG_LEVEL=info
```

🎉 **Config injected without hardcoding!**

---

## Part 3: ConfigMap from File

### Step 3.1: Create a Config File

```bash
cat > app.properties << EOF
database.host=mysql.default.svc.cluster.local
database.port=3306
database.name=myapp
cache.enabled=true
cache.ttl=3600
EOF
```

### Step 3.2: Create ConfigMap from File

```bash
kubectl create configmap file-config --from-file=app.properties # app.properties is right up man 
```

### Step 3.3: View It

```bash
kubectl describe configmap file-config
```

**The entire file is stored as one key!**

---

## Part 4: Mount ConfigMap as Volume

### Step 4.1: Create Pod with Volume Mount

```bash
nano pod-with-config-volume.yaml
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: config-volume-demo
spec:
  containers:
  - name: demo
    image: busybox
    command: ["sh", "-c", "cat /etc/config/app.properties && sleep 3600"]
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: file-config
```

### Step 4.2: Apply

```bash
kubectl apply -f pod-with-config-volume.yaml
```

### Step 4.3: Check the File

```bash
kubectl logs config-volume-demo
```

**See your config file contents!**

### Step 4.4: Exec into Pod to Explore

```bash
kubectl exec -it config-volume-demo -- sh
```

```bash
# Inside pod:
ls /etc/config/
cat /etc/config/app.properties
exit
```

---

## Part 5: Secrets - Create and Use

### Step 5.1: Create Secret (Imperative)

```bash
kubectl create secret generic db-credentials \
    --from-literal=username=admin \
    --from-literal=password=supersecret123
```

### Step 5.2: View Secret

```bash
kubectl get secrets
```

```bash
kubectl describe secret db-credentials
```

**Notice:** Data shows byte size, not actual values!

### Step 5.3: See Base64 Encoded Values

```bash
kubectl get secret db-credentials -o yaml
```

**Values are base64 encoded (NOT encrypted!)**

### Step 5.4: Decode a Value

```bash
kubectl get secret db-credentials -o jsonpath='{.data.password}' | base64 --decode
```

**Shows:** `supersecret123`

---

## Part 6: Use Secret in Pod

### Step 6.1: Create Pod with Secret

```bash
nano pod-with-secret.yaml
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-demo
spec:
  containers:
  - name: demo
    image: busybox
    command: ["sh", "-c", "echo Username: $DB_USER && echo Password: $DB_PASS && sleep 3600"]
    env:
    - name: DB_USER
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: username
    - name: DB_PASS
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: password
```

### Step 6.2: Apply

```bash
kubectl apply -f pod-with-secret.yaml
```

### Step 6.3: Check Logs

```bash
kubectl logs secret-demo
```

**Output:**
```
Username: admin
Password: supersecret123
```

---

## Part 7: Secret from YAML (Declarative)

### Step 7.1: Encode Values

```bash
echo -n 'myuser' | base64
# Output: bXl1c2Vy

echo -n 'mypassword' | base64
# Output: bXlwYXNzd29yZA==
```

### Step 7.2: Create Secret YAML

```bash
nano my-secret.yaml
```

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-app-secret
type: Opaque
data:
  username: bXl1c2Vy           # base64 of 'myuser'
  password: bXlwYXNzd29yZA==   # base64 of 'mypassword'
```

### Step 7.3: Apply

```bash
kubectl apply -f my-secret.yaml
```

### Step 7.4: Verify

```bash
kubectl get secret my-app-secret -o jsonpath='{.data.username}' | base64 --decode
```

---

## Part 8: Real-World Example - Nginx with Config

### Step 8.1: Create Nginx Config

```bash
cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html;
    }
    
    location /health {
        return 200 'healthy\n';
        add_header Content-Type text/plain;
    }
}
EOF
```

### Step 8.2: Create ConfigMap

```bash
kubectl create configmap nginx-config --from-file=nginx.conf
```

### Step 8.3: Create Deployment Using ConfigMap

```bash
nano nginx-with-config.yaml
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-custom
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx-custom
  template:
    metadata:
      labels:
        app: nginx-custom
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/conf.d
      volumes:
      - name: nginx-config
        configMap:
          name: nginx-config
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-custom-svc
spec:
  selector:
    app: nginx-custom
  type: NodePort
  ports:
  - port: 80
    nodePort: 30081
```

### Step 8.4: Apply & Test

```bash
kubectl apply -f nginx-with-config.yaml
```

```bash
minikube service nginx-custom-svc --url
```

**Test health endpoint:**
```bash
curl $(minikube service nginx-custom-svc --url)/health
```

**Output:** `healthy`

---

## Part 9: Clean Up

```bash
kubectl delete -f nginx-with-config.yaml
kubectl delete -f pod-with-secret.yaml
kubectl delete -f pod-with-config-volume.yaml
kubectl delete -f pod-with-configmap.yaml
kubectl delete -f my-secret.yaml
kubectl delete configmap app-config file-config nginx-config
kubectl delete secret db-credentials my-app-secret
```

---

## 🎯 What You Learned

✅ Creating ConfigMaps from literals and files
✅ Injecting ConfigMaps as environment variables
✅ Mounting ConfigMaps as volumes
✅ Creating and using Secrets
✅ Base64 encoding for Secrets
✅ Real-world example with nginx config

---

## ⚠️ Important Security Note

**Secrets are NOT encrypted by default!**
- Base64 is encoding, NOT encryption
- Anyone with cluster access can decode them
- In production, use:
  - Sealed Secrets
  - External Secrets Operator
  - HashiCorp Vault
  - GCP Secret Manager

---

## 🚀 Next Lab

**Lab 4:** Persistent Volumes and StatefulSets

