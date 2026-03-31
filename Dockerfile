###############################################################################
# MiroFish – Lightweight Production Dockerfile for Railway
#
# Strategy:
#   Stage 1 – Build the Vue frontend into static files (Node 18)
#   Stage 2 – Run the Flask backend on python:3.11-slim and serve the
#             frontend static build via Flask on a single port.
#
# Heavy simulation dependencies (camel-ai, camel-oasis, PyTorch) are
# declared as optional extras in pyproject.toml and are NOT installed
# here, keeping the image small enough for Railway (< 2 GB).
# The simulation scripts (scripts/run_*.py) will only work when those
# extras are installed on a more powerful host.
###############################################################################

# ========================== Stage 1: Frontend Build ==========================
FROM node:22-slim AS frontend-build

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts

COPY frontend/ ./
RUN npm run build

# ========================== Stage 2: Backend Runtime =========================
FROM python:3.11-slim

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Copy backend dependency manifest AND lockfile
COPY backend/pyproject.toml backend/uv.lock ./backend/

# Install only the core (lightweight) dependencies — no simulation extras.
# --no-install-project avoids building the project wheel at this stage.
RUN cd backend && uv sync --frozen --no-dev --no-install-project

# Copy the full backend source
COPY backend/ ./backend/

# Now install the project itself (cheap, just links the source)
RUN cd backend && uv sync --frozen --no-dev

# Copy the built frontend
COPY --from=frontend-build /build/dist ./frontend/dist

# Create required directories
RUN mkdir -p ./backend/uploads

# Railway injects PORT (typically 3000)
EXPOSE 3000

ENV FLASK_DEBUG=false
ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "cd backend && uv run python run.py"]
