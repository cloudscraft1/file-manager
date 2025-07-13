# Docker Setup for File Manager

This setup allows you to run both the React frontend and FastAPI backend in a single Docker container, with only the frontend port (3000) exposed.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for easier management)

## Quick Start

### Method 1: Using Docker Compose (Recommended)

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

2. **Build and run:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: The frontend automatically connects to the backend running internally on port 8000

### Method 2: Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t file-manager .
   ```

2. **Run the container:**
   ```bash
   docker run -p 3000:3000 \
     -e MONGO_URL="your_mongo_url" \
     -e DB_NAME="your_db_name" \
     -e APPWRITE_ENDPOINT="your_appwrite_endpoint" \
     -e APPWRITE_PROJECT_ID="your_project_id" \
     -e APPWRITE_API_KEY="your_api_key" \
     -e APPWRITE_BUCKET_ID="your_bucket_id" \
     file-manager
   ```

## Container Architecture

- **Frontend**: React app built and served on port 3000
- **Backend**: FastAPI server running on port 8000 (internal only)
- **Communication**: Frontend configured to communicate with backend via localhost:8000
- **Exposed Port**: Only port 3000 is exposed to the host

## Important Note about Backend URL

The Docker setup automatically configures the frontend to use the local backend (`http://localhost:8000`) instead of any external URL that might be configured in your local `.env` files. This is done during the Docker build process to ensure the frontend and backend communicate properly within the container.

## Environment Variables

The container needs the following environment variables:

- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: MongoDB database name
- `APPWRITE_ENDPOINT`: Appwrite server endpoint
- `APPWRITE_PROJECT_ID`: Appwrite project ID
- `APPWRITE_API_KEY`: Appwrite API key
- `APPWRITE_BUCKET_ID`: Appwrite storage bucket ID

## Development

For development, you can:

1. **Mount volumes for live editing:**
   ```bash
   docker run -p 3000:3000 \
     -v $(pwd)/backend:/app/backend \
     -v $(pwd)/frontend/src:/app/frontend/src \
     file-manager
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Access container shell:**
   ```bash
   docker-compose exec file-manager /bin/bash
   ```

## Troubleshooting

1. **Port conflicts**: Make sure port 3000 is not being used by other applications
2. **Environment variables**: Ensure all required environment variables are set correctly
3. **Build failures**: Check that all dependencies are correctly specified in package.json and requirements.txt
4. **Backend connectivity**: The frontend is configured to use localhost:8000 for backend API calls

## Stopping the Container

```bash
# With Docker Compose
docker-compose down

# With Docker directly
docker stop <container_id>
```
