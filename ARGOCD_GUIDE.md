# ArgoCD Setup and Deployment Guide

This guide explains how to set up continuous deployment for the Playlist Recommendation System using ArgoCD.

## Prerequisites

1. Access to the Kubernetes cluster with ArgoCD installed
2. Git repository with your Kubernetes manifests
3. Docker images pushed to a public registry (Docker Hub or Quay.io)
4. ArgoCD CLI installed (optional, can use Web UI)

## Architecture Overview

```
Git Repository (Source of Truth)
    ├── deployment.yaml       # Frontend API deployment
    ├── service.yaml          # Service configuration
    ├── pvc.yaml              # Persistent Volume Claim
    ├── configmap.yaml        # Dataset and configuration
    ├── ml-job.yaml           # ML model generation job
    └── argocd-app.yaml       # ArgoCD application definition

ArgoCD watches the repository and automatically:
1. Detects changes in Git
2. Applies changes to Kubernetes cluster
3. Manages application lifecycle
```

## Step 1: Prepare Your Git Repository

### 1.1 Required Files

Ensure your repository contains these Kubernetes manifests:

- `deployment.yaml` - Frontend deployment
- `service.yaml` - Service configuration  
- `pvc.yaml` - Persistent Volume Claim
- `configmap.yaml` - Configuration (dataset URL, parameters)
- `ml-job.yaml` - ML Job for rule generation

### 1.2 Push to Git

```bash
cd /home/giovanamachado/TP2

# Initialize git if not already done
git init
git add deployment.yaml service.yaml pvc.yaml configmap.yaml ml-job.yaml
git commit -m "Add Kubernetes manifests for ArgoCD"

# Add remote and push (update with your repository URL)
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

## Step 2: Login to ArgoCD

### 2.1 Change Default Password

```bash
# Login to ArgoCD CLI (if installed)
argocd login <ARGOCD-SERVER-URL>

# Change password
argocd account update-password
```

### 2.2 Or use Web UI

Visit the ArgoCD web interface and login with your credentials.

## Step 3: Create ArgoCD Application

### Option A: Using ArgoCD CLI

```bash
# Create the application
argocd app create giovanamachado-playlist-recommender \
  --repo https://github.com/YOUR-USERNAME/YOUR-REPO.git \
  --path . \
  --project giovanamachado-project \
  --dest-namespace giovanamachado \
  --dest-server https://kubernetes.default.svc \
  --sync-policy automated \
  --auto-prune \
  --self-heal

# Check application status
argocd app get giovanamachado-playlist-recommender

# Sync manually if needed
argocd app sync giovanamachado-playlist-recommender
```

### Option B: Using ArgoCD Web UI

1. Click **"+ New App"**
2. Fill in the form:
   - **Application Name**: `giovanamachado-playlist-recommender`
   - **Project**: `giovanamachado-project`
   - **Sync Policy**: `Automatic`
   - **Repository URL**: Your Git repository URL
   - **Revision**: `HEAD` (or specific branch)
   - **Path**: `.` (root directory, or path to manifests)
   - **Cluster URL**: `https://kubernetes.default.svc`
   - **Namespace**: `giovanamachado`
3. Enable:
   - ✅ Auto-create namespace (if needed)
   - ✅ Auto-prune resources
   - ✅ Self-heal
4. Click **"Create"**

### Option C: Using kubectl and argocd-app.yaml

```bash
# Update argocd-app.yaml with your repository URL
# Then apply it
kubectl apply -f argocd-app.yaml
```

## Step 4: Verify Deployment

```bash
# Check ArgoCD application status
argocd app get giovanamachado-playlist-recommender

# Check Kubernetes resources
kubectl -n giovanamachado get all
kubectl -n giovanamachado get configmap
kubectl -n giovanamachado get pvc

# Check pod logs
kubectl -n giovanamachado logs -l app=giovanamachado-playlist-recommender

# Test the API
CLUSTER_IP=$(kubectl -n giovanamachado get svc playlist-recommender-svc -o jsonpath='{.spec.clusterIP}')
curl -X POST http://${CLUSTER_IP}:50013/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"songs":["all me","antidote"]}'
```

## Step 5: Continuous Deployment Workflows

### 5.1 Update Application Code

When you update the Flask API or ML code:

1. **Build new Docker image** with a new tag:
   ```bash
   docker build -t docker.io/giovana2ma/playlists-frontend:0.2 api/
   docker push docker.io/giovana2ma/playlists-frontend:0.2
   ```

2. **Update deployment.yaml** with new image tag:
   ```yaml
   image: docker.io/giovana2ma/playlists-frontend:0.2
   ```

3. **Commit and push**:
   ```bash
   git add deployment.yaml
   git commit -m "Update frontend to v0.2"
   git push
   ```

4. ArgoCD will automatically detect the change and update the deployment.

### 5.2 Switch Dataset (ds1 → ds2)

Use the helper script:

```bash
# Switch to ds2
./switch-dataset.sh ds2

# Review changes
git diff

# Commit and push
git add configmap.yaml ml-job.yaml
git commit -m "Switch to dataset ds2"
git push
```

ArgoCD will:
1. Update the ConfigMap
2. Create a new ML Job with unique name (e.g., `ml-job-ds2-20251110-150000`)
3. The job will generate `rules_ds2.pkl` in the PVC
4. Restart the frontend deployment to load the new model

### 5.3 Manual Dataset Switch (Alternative)

```bash
# Edit configmap.yaml
# Change:
#   DATASET_URL: "/home/datasets/spotify/2023_spotify_ds2.csv"
#   DATASET_NAME: "ds2"
#   MODEL_FILENAME: "rules_ds2.pkl"

# Edit ml-job.yaml
# Change metadata.name to: ml-job-ds2-<timestamp>

# Commit and push
git add configmap.yaml ml-job.yaml
git commit -m "Switch to ds2"
git push
```

## Step 6: Monitor and Debug

### Check ArgoCD Sync Status

```bash
# CLI
argocd app get giovanamachado-playlist-recommender

# Web UI
# Navigate to your application and check:
# - Sync Status (Synced/OutOfSync)
# - Health Status (Healthy/Degraded)
# - Last Sync time
```

### Check ML Job Status

```bash
# List jobs
kubectl -n giovanamachado get jobs

# Check specific job
kubectl -n giovanamachado describe job ml-job-ds1-<timestamp>

# View logs
kubectl -n giovanamachado logs job/ml-job-ds1-<timestamp>

# Check if model was created
kubectl -n giovanamachado exec -it deployment/playlist-recommender -- ls -lh /model/
```

### Common Issues

**Issue: Application not syncing**
```bash
# Force sync
argocd app sync giovanamachado-playlist-recommender

# Check for errors
argocd app get giovanamachado-playlist-recommender
```

**Issue: ML Job fails**
```bash
# Check job status
kubectl -n giovanamachado describe job <job-name>

# Check pod logs
kubectl -n giovanamachado logs <pod-name>

# Common fixes:
# - Verify dataset path exists
# - Check PVC is bound
# - Verify image exists and is pullable
```

**Issue: Frontend can't load model**
```bash
# Check if model file exists in PVC
kubectl -n giovanamachado exec -it deployment/playlist-recommender -- ls -lh /model/

# Check frontend logs
kubectl -n giovanamachado logs -l app=giovanamachado-playlist-recommender

# Restart deployment
kubectl -n giovanamachado rollout restart deployment playlist-recommender
```

## Step 7: Cleanup (When Done Testing)

```bash
# Delete ArgoCD application
argocd app delete giovanamachado-playlist-recommender

# Or delete resources manually
kubectl -n giovanamachado delete deployment playlist-recommender
kubectl -n giovanamachado delete service playlist-recommender-svc
kubectl -n giovanamachado delete job --all
kubectl -n giovanamachado delete configmap playlist-config
kubectl -n giovanamachado delete pvc project2-pvc
```

## CI/CD Pipeline Summary

```
Developer → Git Push
    ↓
GitHub/GitLab Repository
    ↓
ArgoCD Detects Change
    ↓
    ├─→ ConfigMap Update → Restart Deployment
    ├─→ Deployment Update → Rolling Update
    ├─→ ML Job Creation → Generate New Model
    └─→ Service Update → Update Routes
    ↓
Kubernetes Cluster
    ↓
Running Application
```

## Best Practices

1. **Version Control Everything**: All Kubernetes manifests should be in Git
2. **Use Semantic Versioning**: Tag Docker images with meaningful versions (0.1, 0.2, etc.)
3. **Unique Job Names**: Always use unique names for Jobs (include timestamp or dataset name)
4. **Monitor Resources**: Check ArgoCD UI regularly for sync status
5. **Test Locally First**: Test manifest changes with `kubectl apply` before pushing to Git
6. **Use ConfigMaps**: Store configuration externally, not hardcoded in images
7. **Enable Auto-Prune**: Let ArgoCD clean up old jobs automatically

## Additional Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
