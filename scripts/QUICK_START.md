# CI/CD Testing Quick Start Guide

## Complete Testing Workflow

This guide will walk you through the entire testing process step-by-step.

### Prerequisites

1. **Check your environment:**
   ```bash
   # Verify kubectl access
   kubectl get pods -n giovanamachado
   
   # Verify Python
   python3 --version
   
   # Install dependencies
   pip install requests matplotlib
   ```

2. **Verify your deployment is running:**
   ```bash
   kubectl get deployment playlist-recommender -n giovanamachado
   kubectl get svc playlist-recommender-svc -n giovanamachado
   ```

### Step-by-Step Testing

#### STEP 1: Setup

Open **THREE terminal windows** - you'll need them throughout testing.

**Terminal 1: Port Forwarding**
```bash
cd ~/TP2
kubectl port-forward svc/playlist-recommender-svc 50013:50013 -n giovanamachado
```
Keep this running during all tests!

**Terminal 2: Will be used for monitoring**

**Terminal 3: Will be used for making changes**

#### STEP 2: Test 1 - Replica Scaling (No Downtime Expected)

**Terminal 2: Start monitoring**
```bash
cd ~/TP2
python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 15 -o test1_replicas.json
```

**Terminal 3: Make changes**
```bash
cd ~/TP2

# Check current replicas
kubectl get deployment playlist-recommender -n giovanamachado

# Edit deployment
nano k8s/base/deployment.yaml
# Change: replicas: 2 -> replicas: 3

# Commit and push
git add k8s/base/deployment.yaml
git commit -m "Test 1: Scale to 3 replicas"
git push

# Monitor the rollout
kubectl rollout status deployment/playlist-recommender -n giovanamachado

# Verify new pod
kubectl get pods -n giovanamachado -l app=giovanamachado-playlist-recommender
```

Wait for the monitoring script to complete (15 minutes).

**Analyze results:**
```bash
python3 scripts/analyze_results.py test1_replicas.json
```

**Expected outcome:** Zero downtime, deployment completes in 3-5 minutes.

#### STEP 3: Test 2 - Code Update (Brief Downtime Expected)

**Terminal 2: Start monitoring**
```bash
python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 20 -o test2_code.json
```

**Terminal 3: Build and deploy new version**
```bash
cd ~/TP2

# Build new image (increment version)
cd api
docker build -t docker.io/giovana2ma/playlists-frontend:0.2 .
docker push docker.io/giovana2ma/playlists-frontend:0.2
cd ..

# Update deployment
nano k8s/base/deployment.yaml
# Change: image: .../playlists-frontend:0.1
# To:     image: .../playlists-frontend:0.2

# Update ConfigMap version
nano k8s/base/configmap.yaml
# Change: API_VERSION: "1.0.0"
# To:     API_VERSION: "2.0.0"

# Commit and push
git add k8s/base/deployment.yaml k8s/base/configmap.yaml
git commit -m "Test 2: Update to version 0.2"
git push

# Monitor
kubectl rollout status deployment/playlist-recommender -n giovanamachado
```

Wait for monitoring to complete (20 minutes).

**Analyze results:**
```bash
python3 scripts/analyze_results.py test2_code.json
```

**Expected outcome:** Brief downtime (10-30s), version change detected, deployment in 3-5 minutes.

#### STEP 4: Test 3 - Dataset Update (Longer Process, Brief Downtime)

**Terminal 2: Start monitoring**
```bash
python3 scripts/test_cicd.py http://localhost:50013/api/recommend -d 30 -o test3_dataset.json
```

**Terminal 3: Update dataset**
```bash
cd ~/TP2

# Check current dataset
kubectl get configmap playlist-config -n giovanamachado -o yaml | grep DATASET

# Update ConfigMap
nano k8s/base/configmap.yaml
# Change all ds1 references to ds2:
#   DATASET_URL: "/home/datasets/spotify/2023_spotify_ds2.csv"
#   DATASET_NAME: "ds2"
#   MODEL_FILENAME: "rules_ds2.pkl"

# Commit and push
git add k8s/base/configmap.yaml
git commit -m "Test 3: Switch to ds2 dataset"
git push

# Monitor ML job creation (in a new terminal or split screen)
kubectl get jobs -n giovanamachado -w

# Once job appears, check its progress
kubectl get jobs -n giovanamachado
POD_NAME=$(kubectl get pods -n giovanamachado -l app=giovanamachado-playlist-ml --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
kubectl logs -f $POD_NAME -n giovanamachado

# Monitor deployment restart
kubectl get pods -n giovanamachado -l app=giovanamachado-playlist-recommender -w
```

Wait for monitoring to complete (30 minutes).

**Analyze results:**
```bash
python3 scripts/analyze_results.py test3_dataset.json
```

**Expected outcome:** ML job runs (8-15 min), brief downtime during pod restart, model_date changes.

### Step 5: Generate Report

**Create visualizations:**
```bash
cd ~/TP2

# Individual test visualizations
python3 scripts/visualize_results.py test1_replicas.json --all
python3 scripts/visualize_results.py test2_code.json --all
python3 scripts/visualize_results.py test3_dataset.json --all

# Comparison chart
python3 scripts/visualize_results.py test1_replicas.json test2_code.json test3_dataset.json --comparison comparison.png
```

**Generate text report:**
```bash
python3 scripts/analyze_results.py test1_replicas.json test2_code.json test3_dataset.json -o comparison_report.txt
```

**Compile LaTeX PDF:**
```bash
cd scripts

# Edit the template with your actual results
nano report_template.tex

# Fill in:
# - Your name and student ID
# - Actual test results in the tables
# - Your analysis and observations
# - Include generated graphs

# Compile to PDF
pdflatex report_template.tex
pdflatex report_template.tex  # Run twice for TOC

# View the PDF
xdg-open report_template.pdf
```

### Data to Include in Your Report

From your test results, extract and include:

1. **For each test:**
   - Total deployment time
   - Downtime duration
   - Success rate
   - Number of failed requests
   - Screenshots of monitoring output
   - ArgoCD sync time
   - Pod creation/restart time

2. **Visualizations:**
   - Timeline graphs showing when changes were detected
   - Response time charts
   - Comparison bar charts

3. **Kubernetes screenshots:**
   ```bash
   # Take screenshots of these commands:
   kubectl get pods -n giovanamachado
   kubectl get deployments -n giovanamachado
   kubectl get jobs -n giovanamachado
   kubectl describe deployment playlist-recommender -n giovanamachado
   ```

4. **ArgoCD screenshots:**
   - Application sync status
   - Deployment history
   - Sync operations

### Tips for Success

1. **Document everything:** Take screenshots at key moments
2. **Be patient:** ML jobs can take 10-15 minutes
3. **Watch for changes:** Monitor both kubectl and the test script output
4. **Multiple runs:** Consider running tests 2-3 times for consistency
5. **Clean environment:** Ensure no pending changes before starting
6. **Save your work:** Commit and push all changes properly

### Common Issues and Solutions

**Problem:** Port forward disconnects
```bash
# Restart port forwarding
pkill -f "port-forward.*playlist"
kubectl port-forward svc/playlist-recommender-svc 50013:50013 -n giovanamachado
```

**Problem:** ArgoCD not syncing
```bash
# Check application status
kubectl get applications -n argocd

# Force sync (if using argocd CLI)
argocd app sync playlist-recommender

# Or sync from UI
```

**Problem:** ML job not created
```bash
# Check watcher logs
kubectl logs -l app=ml-config-watcher -n giovanamachado --tail=50

# Restart watcher if needed
kubectl rollout restart deployment/ml-config-watcher -n giovanamachado
```

**Problem:** Tests show 100% failure
```bash
# Check service is accessible
curl -X POST http://localhost:50013/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"songs":["test"]}'

# Check pod status
kubectl get pods -n giovanamachado
kubectl logs -l app=giovanamachado-playlist-recommender -n giovanamachado
```

### Timeline for Testing

- **Setup:** 15 minutes
- **Test 1:** 20 minutes (15 monitoring + 5 analysis)
- **Test 2:** 25 minutes (20 monitoring + 5 analysis)
- **Test 3:** 35 minutes (30 monitoring + 5 analysis)
- **Report generation:** 30 minutes
- **Writing report:** 2-3 hours

**Total estimated time:** 4-5 hours

### Final Checklist

Before submitting your PDF report:

- [ ] All three tests completed successfully
- [ ] JSON result files saved (test1, test2, test3)
- [ ] Visualizations generated
- [ ] Screenshots collected
- [ ] LaTeX report filled with actual data
- [ ] PDF compiled successfully
- [ ] Report includes all required sections:
  - [ ] Introduction and methodology
  - [ ] Architecture description
  - [ ] Results for all three tests
  - [ ] Comparative analysis
  - [ ] Discussion of downtime causes
  - [ ] Recommendations
  - [ ] Conclusions
- [ ] Graphs and charts included
- [ ] All tables filled with actual data
- [ ] References cited
- [ ] Spell-checked and proofread

Good luck with your testing!
