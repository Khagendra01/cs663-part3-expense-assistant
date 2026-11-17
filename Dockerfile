# CS663 Part 3 Option 3: Personal Expense Assistant
# Cloud Run image for the FastAPI backend (ADK agent) plus the Gradio frontend.
# Build context is the project root (part3-expense-assistant).
# The backend and frontend folders are built by a parallel task. This
# Dockerfile copies the whole project, so backend/ and frontend/ are
# included whenever they exist at build time.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8081

WORKDIR /app

# System deps kept minimal. No build tools are needed because the
# requirements are prebuilt wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first so the layer is cached when only code changes.
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install "fastapi>=0.110" "uvicorn[standard]>=0.29" "gradio>=5.23.1"

# Copy the agent, settings, backend, frontend, and sample receipts.
# The .dockerignore file keeps the venv, caches, local settings, and
# the local SQLite database out of the image.
COPY . .

# Writable folders for receipt images and the SQLite database.
# Note: on Cloud Run this filesystem is ephemeral. See DEPLOY.md.
RUN mkdir -p data/receipts data/sample_receipts \
    && python -c "import expense_manager_agent.agent; print('agent import ok:', expense_manager_agent.agent.root_agent.name)"

EXPOSE 8081

# APP_MODULE defaults to backend.main:app (the FastAPI app in
# backend/main.py). Override it only if the backend entrypoint moves.
# Cloud Run sets PORT, and the deploy script sets --port 8081, so
# uvicorn listens on $PORT with 8081 as the local default.
CMD ["sh", "-c", "uvicorn ${APP_MODULE:-backend.main:app} --host 0.0.0.0 --port ${PORT:-8081}"]
