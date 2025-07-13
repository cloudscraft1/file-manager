# Multi-stage build for React frontend and FastAPI backend
FROM node:20-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package.json frontend/yarn.lock ./

# Install frontend dependencies
RUN yarn install --frozen-lockfile

# Copy frontend source code
COPY frontend/ ./

# Create .env file for build to use internal backend (hardcoded)
RUN echo 'REACT_APP_BACKEND_URL=http://localhost:8000' > .env.production

# Build the React app for production with internal backend URL
RUN REACT_APP_BACKEND_URL=http://localhost:8000 yarn build

# Main stage - Python with Node.js for running both services
FROM python:3.11-slim

# Install Node.js and npm (for serving the frontend)
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install serve globally for serving the React build
RUN npm install -g serve

# Create a non-root user with UID 10001
RUN groupadd -g 10001 appuser
RUN useradd -u 10001 -g appuser -m -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy .env file to backend directory
COPY backend/.env ./backend/.env

# Copy built frontend from the builder stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create a startup script
COPY <<EOF /app/start.sh
#!/bin/bash
# Start the FastAPI backend in the background
cd /app/backend && uvicorn server:app --host 0.0.0.0 --port 8000 &

# Wait a moment for backend to start
sleep 2

# Start the frontend server
cd /app/frontend && serve -s build -l 3000
EOF

# Make the startup script executable
RUN chmod +x /app/start.sh

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER 10001

# Expose only the frontend port
EXPOSE 3000

# Use the startup script as the entrypoint
CMD ["/app/start.sh"]
