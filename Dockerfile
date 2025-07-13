# Multi-stage build for React frontend and FastAPI backend
FROM node:18-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package.json frontend/yarn.lock ./

# Install frontend dependencies
RUN yarn install --frozen-lockfile

# Copy frontend source code
COPY frontend/ ./

# Build the React app for production
RUN yarn build

# Main stage - Python with Node.js for running both services
FROM python:3.11-slim

# Install Node.js and npm (for serving the frontend)
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install serve globally for serving the React build
RUN npm install -g serve

# Set working directory
WORKDIR /app

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend from the builder stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create a startup script
RUN echo '#!/bin/bash\n\
# Start the FastAPI backend in the background\n\
cd /app/backend && uvicorn server:app --host 0.0.0.0 --port 8000 &\n\
\n\
# Start the frontend server\n\
cd /app/frontend && serve -s build -l 3000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Create environment file for frontend to use local backend
RUN echo 'REACT_APP_BACKEND_URL=http://localhost:8000' > /app/frontend/.env

# Expose only the frontend port
EXPOSE 3000

# Use the startup script as the entrypoint
CMD ["/app/start.sh"]
