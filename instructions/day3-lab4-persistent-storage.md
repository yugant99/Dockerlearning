# 🧪 Lab 4: Persistent Storage
## Day 3 | Duration: ~45 minutes

---

## The Problem

Containers are ephemeral. Pod dies = data dies.

**This lab:** Make data survive pod restarts!

---

## ✅ Prerequisites
```bash
minikube start
cd ~/dockerlearning/practical
mkdir -p day3-deep-dive && cd day3-deep-dive
```

---

## Part 1: The Problem (Demo)

### Step 1.1: Create Pod with No Persistence

```bash
nano no-persist-pod.yaml
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-persist
spec:
  containers:
  - name: busybox
    image: busybox
    command: ["sh", "-c", "sleep 3600"]
```

```bash
kubectl apply -f no-persist-pod.yaml
```

### Step 1.2: Write Data

```bash
kubectl exec -it no-persist -- sh
```

```bash
# Inside pod:
echo "Important data!" > /tmp/mydata.txt
cat /tmp/mydata.txt
exit
```

### Step 1.3: Delete and Recreate

```bash
kubectl delete pod no-persist
kubectl apply -f no-persist-pod.yaml
```

### Step 1.4: Check Data

```bash
kubectl exec -it no-persist -- cat /tmp/mydata.txt
```

**Result:** `cat: can't open '/tmp/mydata.txt': No such file or directory`

😢 **Data is GONE!**

---

## Part 2: emptyDir Volume (Survives Container Restart)

### Step 2.1: Create Pod with emptyDir

```bash
nano emptydir-pod.yaml
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: emptydir-demo
spec:
  containers:
  - name: writer
    image: busybox
    command: ["sh", "-c", "echo 'Data from writer' > /data/message.txt && sleep 3600"]
    volumeMounts:
    - name: shared-data
      mountPath: /data
  - name: reader
    image: busybox
    command: ["sh", "-c", "sleep 5 && cat /data/message.txt && sleep 3600"]
    volumeMounts:
    - name: shared-data
      mountPath: /data
  volumes:
  - name: shared-data
    emptyDir: {}
```

### Step 2.2: Apply & Check

```bash
kubectl apply -f emptydir-pod.yaml
```

```bash
kubectl logs emptydir-demo -c reader
```

**Output:** `Data from writer`

**Two containers sharing data!**

### Step 2.3: Understanding emptyDir

- Created when pod starts
- Deleted when pod is deleted
- Great for: temp files, cache, sharing between containers
- NOT for: data that must survive pod deletion

---

## Part 3: PersistentVolume (PV) and PersistentVolumeClaim (PVC)

### Step 3.1: See Storage Classes

```bash
kubectl get storageclass
```

**Minikube has:** `standard` (default)

### Step 3.2: Create a PVC

```bash
nano my-pvc.yaml
```

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard
```

```bash
kubectl apply -f my-pvc.yaml
```

### Step 3.3: Check PVC Status

```bash
kubectl get pvc
```

**Expected:** STATUS = `Bound` (minikube auto-provisions PV)

```bash
kubectl get pv
```

**See the auto-created PV!**

---

## Part 4: Use PVC in a Pod

### Step 4.1: Create Pod Using PVC

```bash
nano pvc-pod.yaml
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pvc-demo
spec:
  containers:
  - name: app
    image: busybox
    command: ["sh", "-c", "sleep 3600"]
    volumeMounts:
    - name: my-storage
      mountPath: /data
  volumes:
  - name: my-storage
    persistentVolumeClaim:
      claimName: my-pvc
```

```bash
kubectl apply -f pvc-pod.yaml
```

### Step 4.2: Write Data to Persistent Storage

```bash
kubectl exec -it pvc-demo -- sh
```

```bash
# Inside pod:
echo "This data will persist!" > /data/important.txt
echo "Even after pod deletion!" >> /data/important.txt
cat /data/important.txt
exit
```

### Step 4.3: Delete the Pod

```bash
kubectl delete pod pvc-demo
```

### Step 4.4: Recreate Pod

```bash
kubectl apply -f pvc-pod.yaml
```

### Step 4.5: Check Data Still Exists!

```bash
kubectl exec -it pvc-demo -- cat /data/important.txt
```

🎉 **Data survived pod deletion!**

---

## Part 5: Deployment with Persistent Storage

### Step 5.1: Create Deployment with PVC

```bash
nano mysql-deployment.yaml
```

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 2Gi
---
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
type: Opaque
data:
  password: cm9vdHBhc3N3b3Jk  # rootpassword in base64
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        ports:
        - containerPort: 3306
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: mysql-storage
        persistentVolumeClaim:
          claimName: mysql-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: mysql-service
spec:
  selector:
    app: mysql
  ports:
  - port: 3306
    targetPort: 3306
  type: ClusterIP
```

### Step 5.2: Apply

```bash
kubectl apply -f mysql-deployment.yaml
```

### Step 5.3: Wait for MySQL to Start

```bash
kubectl get pods -w
```

Wait until STATUS = `Running` (may take 1-2 minutes)

Press `Ctrl+C` when ready.

### Step 5.4: Connect to MySQL

```bash
kubectl exec -it $(kubectl get pod -l app=mysql -o jsonpath='{.items[0].metadata.name}') -- mysql -uroot -prootpassword
```

```sql
-- Inside MySQL:
CREATE DATABASE testdb;
USE testdb;
CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50));
INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob');
SELECT * FROM users;
EXIT;
```

### Step 5.5: Delete and Recreate Pod

```bash
# Delete just the pod (not deployment)
kubectl delete pod -l app=mysql
```

```bash
# Deployment recreates it
kubectl get pods -w
```

Wait for new pod to be Running.

### Step 5.6: Verify Data Persisted!

```bash
kubectl exec -it $(kubectl get pod -l app=mysql -o jsonpath='{.items[0].metadata.name}') -- mysql -uroot -prootpassword -e "SELECT * FROM testdb.users;"
```

**Output:**
```
+----+-------+
| id | name  |
+----+-------+
|  1 | Alice |
|  2 | Bob   |
+----+-------+
```

🎉 **Database data survived pod restart!**

---

## Part 6: Understanding Access Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `ReadWriteOnce` (RWO) | Single node read/write | Databases |
| `ReadOnlyMany` (ROX) | Multiple nodes read-only | Static content |
| `ReadWriteMany` (RWX) | Multiple nodes read/write | Shared storage |

**Note:** Minikube only supports RWO. GKE supports RWX via Filestore.

---

## Part 7: Clean Up

```bash
kubectl delete -f mysql-deployment.yaml
kubectl delete -f pvc-pod.yaml
kubectl delete -f emptydir-pod.yaml
kubectl delete -f no-persist-pod.yaml
kubectl delete pvc my-pvc
```

```bash
kubectl get pv,pvc
```

**Should be empty!**

---

## 🎯 What You Learned

✅ Why persistent storage matters
✅ emptyDir for temporary/shared storage
✅ PVC to request persistent storage
✅ Dynamic provisioning with StorageClass
✅ Real database deployment with persistence
✅ Data survives pod restarts!

---

## 🚀 Next Lab

**Lab 5:** Services & Networking Deep Dive

