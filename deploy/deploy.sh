#!/usr/bin/env bash
# Deploy the CS663 Part 3 expense assistant to Cloud Run.
# Run this from Cloud Shell, or any shell with gcloud installed and
# signed in as khagendrakhatri365@gmail.com.
#
# Usage:
#   ./deploy/deploy.sh            # full deploy
#   ./deploy/deploy.sh --dry-run  # print the commands without running them
#
# What it does:
#   1. Checks the backend entrypoint exists (backend/main.py).
#   2. Enables the Cloud Run, Cloud Build, and Vertex AI APIs.
#   3. Builds the image with Cloud Build.
#   4. Deploys (or updates) the Cloud Run service.
#   5. Prints the live service URL.
#
# It never writes a key or a credential to any file. It uses the
# gcloud login already in the shell.

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-cs663-dog-training}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-cs663-expense-assistant}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE}"
APP_MODULE="${APP_MODULE:-backend.main:app}"

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=1
fi

# Print a command in dry-run mode, run it otherwise.
run() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "+ $*"
    else
        "$@"
    fi
}

# The backend is built by a parallel task. Stop early with a clear
# message if it is not finished yet, or if it used a different file.
if [[ ! -f "backend/main.py" ]]; then
    echo "ERROR: backend/main.py was not found in the project root." >&2
    echo "The website build is not finished yet, or the backend entrypoint" >&2
    echo "is in a different file. Set APP_MODULE to the real app path" >&2
    echo "and point this script at it before you deploy." >&2
    exit 1
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
    if ! command -v gcloud >/dev/null 2>&1; then
        echo "ERROR: gcloud was not found. Run this from Cloud Shell." >&2
        exit 1
    fi
    if ! command -v docker >/dev/null 2>&1; then
        echo "NOTE: docker was not found locally. That is fine, the build" >&2
        echo "runs in Cloud Build, not on this machine." >&2
    fi
fi

echo "Deploying service ${SERVICE} to project ${PROJECT_ID} in ${REGION}."

run gcloud config set project "$PROJECT_ID"

run gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    aiplatform.googleapis.com

run gcloud builds submit --tag "$IMAGE" .

run gcloud run deploy "$SERVICE" \
    --image "$IMAGE" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8081 \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 5 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=TRUE,APP_MODULE=${APP_MODULE}"

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "+ gcloud run services describe ${SERVICE} --region ${REGION} --format 'value(status.url)'"
    echo "Dry run done. No commands were run and nothing was deployed."
    exit 0
fi

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format 'value(status.url)')"
echo ""
echo "Live URL: ${URL}"
echo "Test it with: curl -s ${URL}/health"
