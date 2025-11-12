# CI/CD Testing Progress Checklist

Use this checklist to track your progress through the testing and report writing process.

## Pre-Testing Setup

- [ ] Read TESTING_SUMMARY.md for overview
- [ ] Read QUICK_START.md for detailed steps
- [ ] Install Python dependencies
  ```bash
  pip install requests matplotlib
  ```
- [ ] Make scripts executable
  ```bash
  chmod +x scripts/*.sh scripts/*.py
  ```
- [ ] Verify cluster access
  ```bash
  kubectl get pods -n giovanamachado
  ```
- [ ] Verify deployment is running
  ```bash
  kubectl get deployment playlist-recommender -n giovanamachado
  ```
- [ ] Set up port forwarding
  ```bash
  kubectl port-forward svc/playlist-recommender-svc 50013:50013 -n giovanamachado
  ```
- [ ] Test service is accessible
  ```bash
  curl -X POST http://localhost:50013/api/recommend \
    -H "Content-Type: application/json" \
    -d '{"songs":["test"]}'
  ```

## Test 1: Replica Scaling

- [ ] Start monitoring script (15 min)
  ```bash
  python3 scripts/test_cicd.py http://localhost:50013/api/recommend \
    -d 15 -o test1_replicas.json
  ```
- [ ] Note current replica count
  ```bash
  kubectl get deployment playlist-recommender -n giovanamachado
  ```
  Current replicas: ______

- [ ] Edit k8s/base/deployment.yaml
  - Changed replicas to: ______

- [ ] Commit and push changes
  ```bash
  git add k8s/base/deployment.yaml
  git commit -m "Test 1: Scale replicas"
  git push
  ```
  - Commit hash: ______________
  - Push time: ________________

- [ ] Monitor ArgoCD sync
  - Sync started at: ________________
  - Sync completed at: ________________

- [ ] Monitor new pods
  - New pod created at: ________________
  - New pod ready at: ________________

- [ ] Wait for monitoring to complete

- [ ] Analyze results
  ```bash
  python3 scripts/analyze_results.py test1_replicas.json
  ```

- [ ] Record metrics:
  - Total deployment time: ________ minutes
  - Downtime: ________ seconds
  - Success rate: ________ %
  - ArgoCD sync time: ________ minutes

- [ ] Generate visualization
  ```bash
  python3 scripts/visualize_results.py test1_replicas.json --all
  ```

- [ ] Take screenshots:
  - [ ] Monitoring output
  - [ ] kubectl get pods
  - [ ] ArgoCD UI sync status

## Test 2: Code Update

- [ ] Build new Docker image
  ```bash
  cd api
  docker build -t docker.io/giovana2ma/playlists-frontend:0.2 .
  docker push docker.io/giovana2ma/playlists-frontend:0.2
  ```
  - Build completed at: ________________
  - Push completed at: ________________

- [ ] Start monitoring script (20 min)
  ```bash
  python3 scripts/test_cicd.py http://localhost:50013/api/recommend \
    -d 20 -o test2_code.json
  ```

- [ ] Edit k8s/base/deployment.yaml
  - Changed image tag to: ______

- [ ] Edit k8s/base/configmap.yaml
  - Changed API_VERSION to: ______

- [ ] Commit and push changes
  ```bash
  git add k8s/base/deployment.yaml k8s/base/configmap.yaml
  git commit -m "Test 2: Update to v0.2"
  git push
  ```
  - Commit hash: ______________
  - Push time: ________________

- [ ] Monitor deployment
  - ArgoCD sync started: ________________
  - Old pods terminating: ________________
  - New pods creating: ________________
  - New pods ready: ________________

- [ ] Wait for monitoring to complete

- [ ] Analyze results
  ```bash
  python3 scripts/analyze_results.py test2_code.json
  ```

- [ ] Record metrics:
  - Total deployment time: ________ minutes
  - Downtime: ________ seconds
  - Success rate: ________ %
  - Version change detected at: ________________

- [ ] Generate visualization
  ```bash
  python3 scripts/visualize_results.py test2_code.json --all
  ```

- [ ] Take screenshots:
  - [ ] Monitoring output showing version change
  - [ ] kubectl rollout status
  - [ ] ArgoCD UI

## Test 3: Dataset Update

- [ ] Start monitoring script (30 min)
  ```bash
  python3 scripts/test_cicd.py http://localhost:50013/api/recommend \
    -d 30 -o test3_dataset.json
  ```

- [ ] Note current dataset
  ```bash
  kubectl get configmap playlist-config -n giovanamachado -o yaml | grep DATASET
  ```
  Current dataset: ______

- [ ] Edit k8s/base/configmap.yaml
  - Changed DATASET_URL to: ______________________________
  - Changed DATASET_NAME to: ______
  - Changed MODEL_FILENAME to: ______

- [ ] Commit and push changes
  ```bash
  git add k8s/base/configmap.yaml
  git commit -m "Test 3: Switch dataset"
  git push
  ```
  - Commit hash: ______________
  - Push time: ________________

- [ ] Monitor events:
  - ArgoCD sync started: ________________
  - ConfigMap updated: ________________
  - Watcher detected change: ________________
  - ML job created: ________________
  - ML job started: ________________
  - ML job completed: ________________
  - Deployment restart triggered: ________________
  - New pods ready: ________________

- [ ] Monitor ML job
  ```bash
  kubectl get jobs -n giovanamachado
  kubectl logs -f <ml-job-pod> -n giovanamachado
  ```
  - Job name: ______________
  - Job duration: ________ minutes

- [ ] Wait for monitoring to complete

- [ ] Analyze results
  ```bash
  python3 scripts/analyze_results.py test3_dataset.json
  ```

- [ ] Record metrics:
  - Total pipeline time: ________ minutes
  - ML job execution: ________ minutes
  - Downtime: ________ seconds
  - Success rate: ________ %
  - Model change detected at: ________________

- [ ] Generate visualization
  ```bash
  python3 scripts/visualize_results.py test3_dataset.json --all
  ```

- [ ] Take screenshots:
  - [ ] Monitoring output showing model change
  - [ ] kubectl get jobs
  - [ ] ML job logs
  - [ ] ArgoCD UI

## Analysis and Visualization

- [ ] Analyze all tests together
  ```bash
  python3 scripts/analyze_results.py test1_replicas.json \
    test2_code.json test3_dataset.json -o comparison_report.txt
  ```

- [ ] Generate comparison chart
  ```bash
  python3 scripts/visualize_results.py test1_replicas.json \
    test2_code.json test3_dataset.json --comparison comparison.png
  ```

- [ ] Review all generated files:
  - [ ] test1_replicas.json
  - [ ] test2_code.json
  - [ ] test3_dataset.json
  - [ ] comparison_report.txt
  - [ ] comparison.png
  - [ ] test1_replicas_timeline.png
  - [ ] test1_replicas_response.png
  - [ ] test2_code_timeline.png
  - [ ] test2_code_response.png
  - [ ] test3_dataset_timeline.png
  - [ ] test3_dataset_response.png

## Report Writing

- [ ] Copy report template
  ```bash
  cp scripts/report_template.tex scripts/my_report.tex
  ```

- [ ] Edit report with your information:
  - [ ] Add your name and student ID
  - [ ] Fill in test environment details
  - [ ] Add architecture diagram

- [ ] Add Test 1 results:
  - [ ] Fill in results table
  - [ ] Add timeline graph
  - [ ] Write analysis section
  - [ ] Include screenshots

- [ ] Add Test 2 results:
  - [ ] Fill in results table
  - [ ] Add timeline graph
  - [ ] Write analysis section
  - [ ] Include screenshots

- [ ] Add Test 3 results:
  - [ ] Fill in results table
  - [ ] Add timeline graph
  - [ ] Write analysis section
  - [ ] Include screenshots

- [ ] Complete comparative analysis:
  - [ ] Fill in comparison tables
  - [ ] Add comparison chart
  - [ ] Write comparative discussion

- [ ] Write discussion section:
  - [ ] Analyze downtime causes
  - [ ] Propose mitigation strategies
  - [ ] Discuss trade-offs
  - [ ] Add code examples for improvements

- [ ] Write recommendations:
  - [ ] Short-term improvements
  - [ ] Long-term improvements
  - [ ] ML pipeline optimizations

- [ ] Write conclusions:
  - [ ] Summarize findings
  - [ ] State key results
  - [ ] Lessons learned

- [ ] Compile PDF
  ```bash
  cd scripts
  pdflatex my_report.tex
  pdflatex my_report.tex  # Run twice for TOC
  ```

- [ ] Review PDF:
  - [ ] All sections complete
  - [ ] All graphs visible
  - [ ] All tables filled
  - [ ] No placeholder text
  - [ ] Spell check done
  - [ ] Page numbers correct
  - [ ] Table of contents accurate

## Final Checks

- [ ] PDF compiles without errors
- [ ] All required sections present
- [ ] All graphs and charts included
- [ ] All tables filled with real data
- [ ] References cited
- [ ] Professional appearance
- [ ] File size reasonable (<10MB)
- [ ] Filename follows submission guidelines

## Submission

- [ ] Upload PDF to Sakai
- [ ] Verify upload successful
- [ ] Keep backup copy
- [ ] Save all test data (JSON files)
- [ ] Save all visualizations
- [ ] Save LaTeX source

## Time Tracking

- Setup: ________ minutes
- Test 1: ________ minutes
- Test 2: ________ minutes
- Test 3: ________ minutes
- Analysis: ________ minutes
- Visualization: ________ minutes
- Report writing: ________ hours
- Total time: ________ hours

## Notes and Observations

Use this space for additional notes:

Test 1 observations:
________________________________________________________________________
________________________________________________________________________

Test 2 observations:
________________________________________________________________________
________________________________________________________________________

Test 3 observations:
________________________________________________________________________
________________________________________________________________________

Challenges encountered:
________________________________________________________________________
________________________________________________________________________

Interesting findings:
________________________________________________________________________
________________________________________________________________________

Questions for discussion:
________________________________________________________________________
________________________________________________________________________
