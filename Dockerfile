###############################################################################
# MiroFish – Production Dockerfile for Railway
# - Stage 1: Build the Vue frontend into static files
# - Stage 2: Run the Flask backend and serve the frontend via Flask
###############################################################################

# ========================== Stage 1: Frontend Build ==========================
FROM node:18-slim AS frontend-build

WORKDIR /app/frontend

# Install frontend dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# ========================== Stage 2: Backend Runtime =========================
FROM python:3.11-slim

# Install system dependencies needed by some Python packages
RUN apt-get update \
  && apt-get install -y --no-install-recommends gcc g++ \
  && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Copy backend dependency files and install
COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv sync --frozen

# Copy the full backend source
COPY backend/ ./backend/

# Copy the built frontend into a directory the backend can serve
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Copy root-level files that backend may reference (.env loading path, etc.)
COPY .env.example ./

# Create uploads directory
RUN mkdir -p ./backend/uploads

# Railway injects PORT as an environment variable (typically 3000).
# The backend will read it via os.environ.get('PORT', 5001).
EXPOSE 3000

# Production defaults
ENV FLASK_DEBUG=false
ENV PYTHONUNBUFFERED=1

# Start the backend (which also serves the frontend static files)
CMD ["sh", "-c", "cd backend && uv run python run.py"]
