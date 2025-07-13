#!/bin/bash

# Test script to verify Docker configuration
echo "🔍 Testing Docker configuration..."

# Build the image
echo "📦 Building Docker image..."
docker build -t file-manager-test . || exit 1

# Run a test container
echo "🚀 Starting test container..."
docker run -d --name file-manager-test -p 3001:3000 \
  -e MONGO_URL="mongodb://localhost:27017" \
  -e DB_NAME="test_database" \
  -e APPWRITE_ENDPOINT="https://fra.cloud.appwrite.io/v1" \
  -e APPWRITE_PROJECT_ID="test_project_id" \
  -e APPWRITE_API_KEY="test_api_key" \
  -e APPWRITE_BUCKET_ID="test_bucket_id" \
  file-manager-test

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 10

# Check if frontend is accessible
echo "🌐 Testing frontend accessibility..."
if curl -f http://localhost:3001 > /dev/null 2>&1; then
  echo "✅ Frontend is accessible on port 3001"
else
  echo "❌ Frontend is not accessible"
fi

# Check container logs
echo "📋 Container logs:"
docker logs file-manager-test

# Cleanup
echo "🧹 Cleaning up..."
docker stop file-manager-test
docker rm file-manager-test
docker rmi file-manager-test

echo "🎉 Test completed!"
