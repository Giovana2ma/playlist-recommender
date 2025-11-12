# ArgoCD Deployment Guide

This guide explains how to set up continuous deployment for the Spotify Playlist Recommender using ArgoCD.

## Prerequisites

1. **Docker images pushed to registry**
   - `docker.io/giovana2ma/playlists-ml:0.1`
   - `docker.io/giovana2ma/playlists-frontend:0.1`

2. **Git repository** with Kubernetes manifests
   - Create a public Git repository (GitHub, GitLab, etc.)
   - Push all the `.yaml` files to the repository

3. **ArgoCD access**
   - Login to ArgoCD server
   - Change default password

## Repository Structure

Your Git repository should contain these files:

```
.
├── deployment.yaml          # Frontend deployment
├── service.yaml            # Service definition
├── pvc.yaml                # Persistent Volume Claim
├── k8s-configmap.yaml      # Configuration for dataset and parameters
├── k8s-ml-job.yaml         # ML model generation job
├── argocd-application.yaml # ArgoCD app definition (optional)
└── README.md               # This file
```

## Setup Steps

### 1. Push Code to Git Repository

```bash
# Initialize git repository (if not already done)
cd /home/giovanamachado/TP2
git init

# Add the Kubernetes manifests
git add deployment.yaml service.yaml pvc.yaml k8s-configmap.yaml k8s-ml-job.yaml

# Commit
git commit -m "Add Kubernetes manifests for ArgoCD deployment"

# Add remote and push (replace with your repository URL)
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git branch -M main
git push -u origin main
```

### 2. Login to ArgoCD

```bash
# Get ArgoCD server address (ask your instructor)
ARGOCD_SERVER="argocd.example.com"

# Login via CLI
argocd login $ARGOCD_SERVER

# Change password (first time only)
argocd account update-password
```

### 3. Create ArgoCD Application

**Option A: Using CLI**

```bash
argocd app create giovanamachado-playlist-recommender \
  --repo https://github.com/YOUR-USERNAME/YOUR-REPO.git \
  --path . \
  --project giovanamachado-project \
  --dest-namespace giovanamachado \
  --dest-server https://kubernetes.default.svc \
  --sync-policy automated \
  --auto-prune \
  --self-heal
```

**Option B: Using Web UI**

1. Navigate to ArgoCD web interface
2. Click "New App"
3. Fill in the form:
   - **Application Name**: `giovanamachado-playlist-recommender`
   - **Project**: `giovanamachado-project`
   - **Sync Policy**: Automatic
   - **Repository URL**: Your Git repo URL
   - **Path**: `.` (or subdirectory with manifests)
   - **Cluster URL**: `https://kubernetes.default.svc`
   - **Namespace**: `giovanamachado`
4. Enable:
   - ☑ Auto-create namespace
   - ☑ Auto-prune resources
   - ☑ Self-heal
5. Click "Create"

**Option C: Apply the Application Manifest**

```bash
# Update argocd-application.yaml with your Git repo URL
kubectl apply -f argocd-application.yaml
```

### 4. Verify Deployment

```bash
# Check ArgoCD application status
argocd app get giovanamachado-playlist-recommender

# Check Kubernetes resources
kubectl -n giovanamachado get all
kubectl -n giovanamachado get pvc
kubectl -n giovanamachado get configmap

# View application in ArgoCD UI
# Navigate to: https://<argocd-server>/applications/giovanamachado-playlist-recommender
```

## Continuous Deployment Workflow

### Updating the Code (Frontend/ML)

1. **Make code changes** in `api/` or `model/`
2. **Build new Docker images** with a new tag:
   ```bash
   ./build-images.sh
   # Update VERSION in build-images.sh to 0.2, 0.3, etc.
   ```

3. **Push images** to registry:
   ```bash
   ./push-images.sh
   ```

4. **Update deployment.yaml** with new image tag:
   ```yaml
   image: docker.io/giovana2ma/playlists-frontend:0.2  # Changed from 0.1
   ```

5. **Commit and push**:
   ```bash
   git add deployment.yaml
   git commit -m "Update frontend to version 0.2"
   git push
   ```

6. **ArgoCD automatically syncs** and deploys the new version

### Switching Datasets (ds1 → ds2)

1. **Update k8s-configmap.yaml**:
   ```yaml
   data:
     DATASET_URL: "/home/datasets/spotify/2023_spotify_ds2.csv"
     DATASET_NAME: "ds2"
     MODEL_FILENAME: "rules_ds2.pkl"
   ```

2. **Update k8s-ml-job.yaml** - change the job name:
   ```yaml
   metadata:
     name: ml-job-ds2-v1  # Changed from ml-job-ds1-v1
     labels:
       dataset: ds2       # Changed from ds1
   ```

3. **Commit and push**:
   ```bash
   git add k8s-configmap.yaml k8s-ml-job.yaml
   git commit -m "Switch to dataset ds2"
   git push
   ```

4. **ArgoCD will**:
   - Update the ConfigMap
   - Create a new ML Job (with new name)
   - The Job generates `rules_ds2.pkl` in the PVC
   - Frontend pods restart and load the new model

### Manual Sync (if needed)

```bash
# Trigger manual sync
argocd app sync giovanamachado-playlist-recommender

# Or via UI: Click "Sync" button
```

## Testing the Deployment

### Test the API

```bash
# Get the service cluster IP
CLUSTER_IP=$(kubectl -n giovanamachado get svc playlist-recommender-svc -o jsonpath='{.spec.clusterIP}')

# Send a test request
curl -X POST http://$CLUSTER_IP:50013/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"songs":["all me","antidote"]}'
```

### Check ML Job Status

```bash
# List all jobs
kubectl -n giovanamachado get jobs

# Check job logs
kubectl -n giovanamachado logs job/ml-job-ds1-v1

# Jobs are automatically cleaned up after 1 hour (ttlSecondsAfterFinished: 3600)
```

### Monitor Resources

```bash
# Watch pods
kubectl -n giovanamachado get pods -w

# Check deployment status
kubectl -n giovanamachado describe deployment playlist-recommender

# View ConfigMap
kubectl -n giovanamachado get configmap playlist-config -o yaml
```

## Troubleshooting

### Application not syncing

```bash
# Check sync status
argocd app get giovanamachado-playlist-recommender

# Force refresh
argocd app sync giovanamachado-playlist-recommender --force

# Check ArgoCD logs
kubectl -n argocd logs -f deployment/argocd-application-controller
```

### ML Job failing

```bash
# Check job status
kubectl -n giovanamachado describe job ml-job-ds1-v1

# View logs
kubectl -n giovanamachado logs job/ml-job-ds1-v1

# Delete failed job
kubectl -n giovanamachado delete job ml-job-ds1-v1
```

### Model not loading in frontend

```bash
# Check if model file exists in PVC
kubectl -n giovanamachado exec -it deployment/playlist-recommender -- ls -lh /model/

# Check frontend logs
kubectl -n giovanamachado logs -f deployment/playlist-recommender

# Restart deployment
kubectl -n giovanamachado rollout restart deployment playlist-recommender
```

## Clean Up

```bash
# Delete the ArgoCD application (this removes all resources)
argocd app delete giovanamachado-playlist-recommender

# Or delete manually
kubectl -n giovanamachado delete deployment playlist-recommender
kubectl -n giovanamachado delete service playlist-recommender-svc
kubectl -n giovanamachado delete job --all
kubectl -n giovanamachado delete pvc project2-pvc
kubectl -n giovanamachado delete configmap playlist-config
```

## Advanced Configuration

### Image Pull Secrets (for private registries)

If using a private Docker registry:

```yaml
# Add to deployment.yaml
spec:
  template:
    spec:
      imagePullSecrets:
      - name: dockerhub-secret
```

Create the secret:
```bash
kubectl -n giovanamachado create secret docker-registry dockerhub-secret \
  --docker-server=docker.io \
  --docker-username=giovana2ma \
  --docker-password=<your-password>
```

### Auto-reload Model in Frontend

The current frontend loads the model once at startup. To auto-reload when the file changes, you could:

1. Add a file watcher in `api/server.py`
2. Use a sidecar container to monitor file changes
3. Restart pods when ConfigMap changes (using annotations)

### Using Kustomize

For managing multiple environments (dev/staging/prod):

```bash
# Directory structure
k8s/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── dev/
    │   └── kustomization.yaml
    └── prod/
        └── kustomization.yaml
```

## References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
