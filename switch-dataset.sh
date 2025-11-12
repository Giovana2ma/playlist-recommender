#!/bin/bash
# Script to switch between datasets (ds1 and ds2)
# This updates the ConfigMap and ML Job to use a different dataset

set -e

# Check arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <dataset-name>"
    echo "Example: $0 ds1"
    echo "         $0 ds2"
    exit 1
fi

DATASET=$1
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
JOB_NAME="ml-job-${DATASET}-${TIMESTAMP}"

echo "======================================================================"
echo "Switching to Dataset: $DATASET"
echo "======================================================================"

# Update ConfigMap
echo "Updating ConfigMap..."
cat > k8s-configmap.yaml <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: playlist-config
  namespace: giovanamachado
data:
  # Dataset configuration - update this to switch between ds1 and ds2
  DATASET_URL: "/home/datasets/spotify/2023_spotify_${DATASET}.csv"
  DATASET_NAME: "${DATASET}"
  MODEL_FILENAME: "rules_${DATASET}.pkl"
  
  # Model generation parameters
  MIN_SUPPORT: "0.01"
  MIN_CONFIDENCE: "0.3"
  MIN_LIFT: "1.0"
  
  # API configuration
  API_PORT: "50013"
  API_VERSION: "1.0.0"
EOF

# Update ML Job with unique name
echo "Creating ML Job manifest with name: $JOB_NAME..."
cat > k8s-ml-job.yaml <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  # IMPORTANT: Unique name for each dataset change
  name: ${JOB_NAME}
  namespace: giovanamachado
  labels:
    app: giovanamachado-playlist-ml
    dataset: ${DATASET}
spec:
  # Automatically clean up finished jobs after 1 hour
  ttlSecondsAfterFinished: 3600
  template:
    metadata:
      labels:
        app: giovanamachado-playlist-ml
    spec:
      restartPolicy: Never
      containers:
      - name: ml-generator
        image: docker.io/giovana2ma/playlists-ml:0.1
        imagePullPolicy: IfNotPresent
        
        # Command to run the rule generator
        command: ["python3", "ruleGenerator.py"]
        args:
          - "\$(DATASET_PATH)"
          - "-o"
          - "/output/\$(MODEL_FILENAME)"
          - "-s"
          - "\$(MIN_SUPPORT)"
          - "-c"
          - "\$(MIN_CONFIDENCE)"
          - "-l"
          - "\$(MIN_LIFT)"
        
        # Environment variables from ConfigMap
        env:
        - name: DATASET_PATH
          valueFrom:
            configMapKeyRef:
              name: playlist-config
              key: DATASET_URL
        - name: MODEL_FILENAME
          valueFrom:
            configMapKeyRef:
              name: playlist-config
              key: MODEL_FILENAME
        - name: MIN_SUPPORT
          valueFrom:
            configMapKeyRef:
              name: playlist-config
              key: MIN_SUPPORT
        - name: MIN_CONFIDENCE
          valueFrom:
            configMapKeyRef:
              name: playlist-config
              key: MIN_CONFIDENCE
        - name: MIN_LIFT
          valueFrom:
            configMapKeyRef:
              name: playlist-config
              key: MIN_LIFT
        
        volumeMounts:
        # Mount the dataset directory (read-only)
        - name: dataset-volume
          mountPath: /home/datasets/spotify
          readOnly: true
        # Mount the PVC for output (read-write)
        - name: model-volume
          mountPath: /output
      
      volumes:
      # Host path to dataset directory
      - name: dataset-volume
        hostPath:
          path: /home/datasets/spotify
          type: Directory
      # Persistent volume claim for model storage
      - name: model-volume
        persistentVolumeClaim:
          claimName: project2-pvc
EOF

echo ""
echo "✓ Files updated successfully!"
echo ""
echo "Next steps:"
echo "1. Review the changes:"
echo "   git diff k8s-configmap.yaml k8s-ml-job.yaml"
echo ""
echo "2. Commit and push to trigger ArgoCD sync:"
echo "   git add k8s-configmap.yaml k8s-ml-job.yaml"
echo "   git commit -m 'Switch to dataset ${DATASET}'"
echo "   git push"
echo ""
echo "3. Or apply manually:"
echo "   kubectl apply -f k8s-configmap.yaml"
echo "   kubectl apply -f k8s-ml-job.yaml"
echo "   kubectl -n giovanamachado rollout restart deployment playlist-recommender"
echo ""
echo "======================================================================"
