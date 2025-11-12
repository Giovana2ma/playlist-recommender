# CI/CD Testing Procedures

This document outlines the procedures for testing the ArgoCD CI/CD pipeline for the Playlist Recommender System.

## Setup

### Prerequisites
1. ArgoCD is installed and configured
2. Application is deployed to Kubernetes cluster
3. kubectl is configured to access your cluster
4. Python 3.x with requests library installed

### Initial Setup

```bash
# Install Python dependencies
pip install requests

# Make scripts executable
chmod +x scripts/test_cicd.py

# Set up port forwarding to access the service
kubectl port-forward svc/playlist-recommender-svc 50013:50013 -n giovanamachado
```

## Test 1: Kubernetes Deployment Changes (Replica Count)

### Objective
Test that ArgoCD automatically redeploys when the number of replicas is changed.

### Procedure

1. **Start monitoring** (in terminal 1):
   ```bash
   python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 15 -o test1_replicas.json
   ```

2. **Check initial state** (in terminal 2):
   ```bash
   kubectl get pods -n giovanamachado -l app=giovanamachado-playlist-recommender
   ```

3. **Update replica count**:
   ```bash
   # Edit the deployment file
   # Change replicas from 2 to 3 (or vice versa)
   # Commit and push to trigger ArgoCD
   git add k8s/base/deployment.yaml
   git commit -m "Test: Increase replicas to 3"
   git push
   ```

4. **Monitor ArgoCD**:
   ```bash
   # Watch ArgoCD sync status
   kubectl get applications -n argocd
   ```

5. **Verify changes**:
   ```bash
   kubectl get pods -n giovanamachado -l app=giovanamachado-playlist-recommender
   ```

### Expected Results
- ArgoCD should detect the change within 3 minutes (default sync interval)
- New pod(s) should be created
- Service should remain available during scaling
- No downtime expected (rolling update)

---

## Test 2: Code Updates (Container Image Version)

### Objective
Test that ArgoCD redeploys when the container image version is updated.

### Procedure

1. **Start monitoring** (in terminal 1):
   ```bash
   python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 20 -o test2_code.json
   ```

2. **Update code version** (in terminal 2):
   ```bash
   # Update API_VERSION in k8s/base/configmap.yaml
   # Change from "1.0.0" to "1.0.1" or "2.0.0"
   ```

3. **Modify server code** (optional):
   ```bash
   # Make a small change to api/server.py
   # For example, add a comment or update a string
   cd api
   # Edit server.py
   ```

4. **Build and push new image**:
   ```bash
   # Build new Docker image with incremented version
   cd api
   docker build -t docker.io/giovana2ma/playlists-frontend:0.2 .
   docker push docker.io/giovana2ma/playlists-frontend:0.2
   ```

5. **Update deployment manifest**:
   ```bash
   # Edit k8s/base/deployment.yaml
   # Change image tag from :0.1 to :0.2
   # Also update API_VERSION in configmap.yaml
   ```

6. **Commit and push**:
   ```bash
   git add k8s/base/deployment.yaml k8s/base/configmap.yaml
   git commit -m "Test: Update frontend to v0.2"
   git push
   ```

7. **Monitor deployment**:
   ```bash
   kubectl rollout status deployment/playlist-recommender -n giovanamachado
   ```

### Expected Results
- ArgoCD should sync within 3 minutes
- Pods should be recreated with new image
- Version in API responses should change from old to new
- Brief downtime possible during pod termination/creation (measure with monitoring script)

---

## Test 3: Training Dataset Update

### Objective
Test that ArgoCD triggers ML model regeneration when the dataset is changed.

### Procedure

1. **Start monitoring** (in terminal 1):
   ```bash
   python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 30 -o test3_dataset.json
   ```

2. **Check current dataset** (in terminal 2):
   ```bash
   kubectl get configmap playlist-config -n giovanamachado -o yaml | grep DATASET
   ```

3. **Update ConfigMap to use different dataset**:
   ```bash
   # Edit k8s/base/configmap.yaml
   # Change:
   #   DATASET_URL: "/home/datasets/spotify/2023_spotify_ds1.csv"
   #   DATASET_NAME: "ds1"
   #   MODEL_FILENAME: "rules_ds1.pkl"
   # To:
   #   DATASET_URL: "/home/datasets/spotify/2023_spotify_ds2.csv"
   #   DATASET_NAME: "ds2"
   #   MODEL_FILENAME: "rules_ds2.pkl"
   ```

4. **Commit and push**:
   ```bash
   git add k8s/base/configmap.yaml
   git commit -m "Test: Switch to ds2 dataset"
   git push
   ```

5. **Monitor ML job creation**:
   ```bash
   # Watch for new ML job to be created
   kubectl get jobs -n giovanamachado -w
   ```

6. **Check ML job logs**:
   ```bash
   # Find the job name
   kubectl get jobs -n giovanamachado | grep ml-job
   
   # Get pod name
   kubectl get pods -n giovanamachado -l app=giovanamachado-playlist-ml
   
   # View logs
   kubectl logs <ml-job-pod-name> -n giovanamachado
   ```

7. **Monitor deployment restart**:
   ```bash
   kubectl get pods -n giovanamachado -l app=giovanamachado-playlist-recommender -w
   ```

### Expected Results
- ArgoCD syncs ConfigMap change within 3 minutes
- ML config watcher detects ConfigMap change within 30 seconds
- New ML job is created automatically
- ML job generates new model file (may take 5-15 minutes depending on dataset)
- Deployment is automatically restarted after ML job completes
- Model date in API responses changes to reflect new model
- Downtime during pod restart (measure with monitoring script)

---

## Analyzing Results

### Metrics to Collect

1. **Deployment Time**:
   - Time from git push to ArgoCD sync
   - Time from sync to pod ready
   - Total time from change to service update

2. **Downtime**:
   - Number of failed requests
   - Duration of connection errors
   - Gap between old and new pod availability

3. **Change Detection**:
   - Time to detect version change
   - Time to detect model_date change
   - Continuity of service during update

### Analyzing JSON Output

```python
import json

# Load test results
with open('test1_replicas.json', 'r') as f:
    data = json.load(f)

# Check downtime
downtime = data['summary']['downtime_seconds']
print(f"Total downtime: {downtime} seconds")

# Check changes
version_changes = data['changes']['version_changes']
model_changes = data['changes']['model_changes']

print(f"Version changes: {len(version_changes)}")
print(f"Model changes: {len(model_changes)}")

# Analyze detailed results
for result in data['detailed_results']:
    if result['status'] == 'connection_error':
        print(f"Downtime at: {result['timestamp']}")
```

---

## Troubleshooting

### Service not responding
```bash
# Check pod status
kubectl get pods -n giovanamachado

# Check pod logs
kubectl logs -l app=giovanamachado-playlist-recommender -n giovanamachado

# Check service
kubectl get svc -n giovanamachado
```

### ArgoCD not syncing
```bash
# Check ArgoCD application
kubectl get application -n argocd

# Force sync
argocd app sync <app-name>

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

### ML job not created
```bash
# Check ml-config-watcher logs
kubectl logs -l app=ml-config-watcher -n giovanamachado

# Check RBAC permissions
kubectl get serviceaccount ml-updater-sa -n giovanamachado
kubectl get role ml-updater-role -n giovanamachado
```

---

## Documentation Requirements

For your PDF submission, include:

1. **Test Setup**:
   - Architecture diagram
   - ArgoCD configuration
   - CI/CD pipeline flow

2. **Test Results** (for each test):
   - Screenshots of monitoring output
   - Timestamps of key events
   - Graphs showing request success/failure over time
   - Measured deployment times
   - Measured downtime periods

3. **Analysis**:
   - Comparison of three test scenarios
   - Discussion of downtime causes
   - Recommendations for minimizing downtime
   - Trade-offs in deployment strategies

4. **Conclusions**:
   - Summary of CI/CD pipeline performance
   - Lessons learned
   - Future improvements
