# Build Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
# Use a placeholder or environment variable for the API URL
# For unified deployment, we can use empty string for relative paths
ENV VITE_API_URL=/api
ENV VITE_WS_URL=/ws
RUN npm run build

# Final Image
FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port (HF uses 7860, Render uses 10000, others 8000)
# We'll use 7860 as default for HF compatibility
ENV PORT=7860
EXPOSE 7860

# Start command (uses PORT env var dynamically)
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}
