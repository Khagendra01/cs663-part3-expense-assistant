Khagendra Khatri
Nov 17, 2026
CS663 Computer Vision

# Deploy: Part 3 Option 3 Personal Expense Assistant to Cloud Run

AI use citation: this deploy guide was written with Muse assistance.
I checked the commands, and I am responsible for the result.

## What this deploys

The FastAPI backend that hosts the ADK expense manager agent, plus
the Gradio frontend, as one Cloud Run service:

- Service name: cs663-expense-assistant
- Project: cs663-dog-training
- Region: us-central1
- Model: gemini-2.5-flash on Vertex AI
- Container port: 8081

Files: Dockerfile and .dockerignore in the project root, and
deploy/deploy.sh, which is the single source of truth for the deploy
commands. There is no separate cloudrun.yaml, so the script and the
docs cannot drift apart.

This one service is the backend only. It serves the FastAPI API
on port 8081, not the Gradio web page. The Gradio frontend is a
separate app (frontend/app.py, port 7860) that calls the backend.
For the demo you run the frontend on your own machine and point
it at the live backend URL. See "Demo the website" below. That
matches the codelab, which also had a frontend service and a
backend service.

## Before you start

- Sign in to Cloud Shell as khagendrakhatri365@gmail.com. That login
  was verified on Nov 17, 2026, with project cs663-dog-training
  selected and the Vertex AI API (aiplatform.googleapis.com) enabled.
- The website build must be finished first. The script stops with a
  clear error if backend/main.py does not exist yet.
- The backend entrypoint is assumed to be backend/main.py exposing
  `app`, which is the codelab layout. If the website build used a
  different file, set APP_MODULE before you run the script, for
  example APP_MODULE=backend.app:app ./deploy/deploy.sh
- No key or credential goes in any file. The deploy uses the gcloud
  login in the shell, and Vertex AI auth comes from the Cloud Run
  service account.

## Deploy steps (Cloud Shell)

1. Get this project folder into Cloud Shell, then enter it:

```
cd part3-expense-assistant
```

2. Check the backend entrypoint is there:

```
ls backend/main.py Dockerfile deploy/deploy.sh
```

If backend/main.py is missing, stop. The website build is not done.

3. Do a dry run first. It prints every command and runs nothing:

```
bash deploy/deploy.sh --dry-run
```

4. Deploy. This enables the APIs, builds the image in Cloud Build,
and deploys the service. It takes a few minutes:

```
bash deploy/deploy.sh
```

What the script runs, in order:

```
gcloud config set project cs663-dog-training
gcloud services enable run.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com
gcloud builds submit --tag gcr.io/cs663-dog-training/cs663-expense-assistant .
gcloud run deploy cs663-expense-assistant \
  --image gcr.io/cs663-dog-training/cs663-expense-assistant \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8081 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 5 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=cs663-dog-training,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=TRUE,APP_MODULE=backend.main:app
```

5. Copy the live URL printed at the end. Get it again any time with:

```
gcloud run services describe cs663-expense-assistant --region us-central1 --format 'value(status.url)'
```

## Test the live URL

The live URL is the backend API. Check it is up first. This call
needs no Gemini key:

```
URL=$(gcloud run services describe cs663-expense-assistant --region us-central1 --format 'value(status.url)')
curl -s "$URL/health"
```

Expected: {"status": "ok", "agent": "expense_manager_agent"}.

Check the stored receipts (empty on a fresh deploy):

```
curl -s "$URL/receipts"
```

Expected: {"count": 0, "receipts": []}.

Ask a text question. This is the real /chat contract from
backend/main.py, verified by reading it on Nov 17, 2026. It takes
{"message": "..."} and returns {"reply": "...", "tools_used": [...]}.
It needs a Gemini backend, which this deploy provides through
Vertex AI, so it should answer instead of returning 503:

```
curl -s "$URL/chat" -H 'Content-Type: application/json' \
  -d '{"message": "How much did I spend at Target?"}'
```

If the answer says no Gemini key is set, the service account is
missing Vertex AI permission. See Troubleshooting.

## Demo the website

The Gradio web page does not run on Cloud Run in this setup. Run
it on your own machine and point it at the live backend:

```
cd part3-expense-assistant
BACKEND_URL="$URL/chat" .venv/bin/python frontend/app.py
```

Then open http://localhost:7860 in a browser. That is the page to
record for the demo video. Run the 3 demo turns from the README,
with the sample receipts in data/sample_receipts:

1. Upload data/sample_receipts/target-2026-11-14.png and ask the
   assistant to store it. Expected: Target, 2026-11-14, 87.20 USD,
   5 items, stored successfully.
2. Ask: "How much did I spend at Target?" Expected: 87.20 USD.
3. Ask: "What is my total spending in November?" Expected, after
   all 3 sample receipts are stored: 135.83 USD total, 3 receipts,
   45.28 USD average.

Receipt upload is easiest in the browser, not with curl, because
it is a file upload. If you do want curl for an upload, base64
encode the image first and send it as image_base64 with the
message "Please store this receipt."

## Cost

Cloud Run charges only while a request is running, and this service
scales to zero when nobody uses it. The deploy sets 1 CPU, 1 Gi of
memory, and at most 5 instances. A short class demo should stay
inside the free tier, but check the billing page after the demo.
Gemini calls on Vertex AI are billed to the project
separately from Cloud Run.

## Limits, read this before the demo

- SQLite data is ephemeral on Cloud Run. Receipts are stored in
  data/expenses.db inside the container filesystem. A new revision
  starts with an empty database, and two running instances do not
  share receipts. So store the 3 sample receipts fresh on the live
  URL right before you record the demo, and do not count on the
  data lasting after a redeploy. The codelab used Firestore for
  storage, which keeps data between deploys. This local version
  trades that for no billing setup, and the README says how to swap
  Firestore back in.
- The first request after idle can be slow while Cloud Run starts
  a container. Open the URL once before you start recording.
- The service is public (--allow-unauthenticated) so the demo link
  works without a login. Anyone with the URL can use it and spend
  your Gemini quota. Delete the service or remove public access
  after the demo if you do not want it left open.

## Update and delete

To update, change the code and run the script again. It rebuilds
the image and deploys a new revision with the same URL.

To delete the service when the demo is done:

```
gcloud run services delete cs663-expense-assistant --region us-central1
```

## Troubleshooting

- "backend/main.py was not found": the website build is not
  finished, or the entrypoint is in another file. Set APP_MODULE
  to the real app path and try again.
- The page loads but chat answers fail with a permission error:
  the Cloud Run service account needs permission to call Vertex
  AI. In the Cloud Console, give the service account the
  Vertex AI User role for this project, then redeploy.
- The container starts but Cloud Run reports it as unhealthy:
  check that the backend listens on the PORT environment variable.
  The Dockerfile uses ${PORT:-8081} and the deploy sets
  --port 8081, so they match.
- "gcloud: command not found": you are not in Cloud Shell. Use
  Cloud Shell, or install gcloud and run gcloud auth login first.

## What was verified, and what was not run

Verified in this VM on Nov 17, 2026:

- bash -n deploy/deploy.sh: syntax ok.
- bash deploy/deploy.sh --dry-run: exit 0, prints the exact
  gcloud commands above, including the enable, build, deploy, and
  describe steps. The backend check passed for real, because
  backend/main.py now exists. The earlier stub run in /tmp is no
  longer needed.
- backend/main.py and frontend/app.py were read on Nov 17, 2026,
  after the parallel website build landed them. Confirmed:
  backend/main.py exposes `app`, GET /health, GET /receipts, and
  POST /chat with {"message": "..."} returning {"reply": "...",
  "tools_used": [...]}, and runs uvicorn on port 8081.
  frontend/app.py is a Gradio app on port 7860 that reads
  BACKEND_URL from settings, default http://localhost:8081/chat,
  so BACKEND_URL="$URL/chat" python frontend/app.py points the
  local web page at the live backend.
- Dockerfile read check: base image python:3.12-slim, installs
  requirements.txt plus fastapi, uvicorn, and gradio, copies the
  project, exposes 8081, runs uvicorn on ${PORT:-8081}.
- No em dashes in any file written here, and no keys or
  credentials in any file. Only placeholders and the project id.

Not run, because this VM has no docker, no gcloud, and no Google
Cloud credentials:

- No docker build, so the image was not built or tested locally.
- No gcloud deploy, so the Cloud Run service does not exist yet.
- No live URL test. The first live test happens after step 4
  above, in Cloud Shell.

The Dockerfile import check inside the image (python -c "import
expense_manager_agent.agent") can only run at build time, when the
backend and frontend folders exist. It is the first thing that
will fail the Cloud Build if the agent code is broken.
