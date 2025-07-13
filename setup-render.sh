#!/bin/bash

# Render Setup Script
# This script helps you prepare your repository for Render deployment

echo "🚀 Setting up File Manager for Render deployment..."

# Check if render.yaml exists
if [ ! -f "render.yaml" ]; then
    echo "❌ render.yaml not found! Please ensure the file exists in your repository root."
    exit 1
fi

echo "✅ render.yaml found"

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found! Please ensure Docker configuration is complete."
    exit 1
fi

echo "✅ Dockerfile found"

# Check if required directories exist
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Frontend or backend directory not found!"
    exit 1
fi

echo "✅ Frontend and backend directories found"

# Check if package.json exists in frontend
if [ ! -f "frontend/package.json" ]; then
    echo "❌ frontend/package.json not found!"
    exit 1
fi

echo "✅ Frontend package.json found"

# Check if requirements.txt exists in backend
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ backend/requirements.txt not found!"
    exit 1
fi

echo "✅ Backend requirements.txt found"

# Test Docker build
echo "🐳 Testing Docker build..."
if docker build -t file-manager-render-test . > /dev/null 2>&1; then
    echo "✅ Docker build successful"
    docker rmi file-manager-render-test > /dev/null 2>&1
else
    echo "❌ Docker build failed! Please check your Dockerfile and dependencies."
    exit 1
fi

# Check git status
if ! git status > /dev/null 2>&1; then
    echo "❌ Not a git repository! Please initialize git and push to GitHub."
    exit 1
fi

echo "✅ Git repository detected"

# Check if there are uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes. Please commit and push them before deploying."
    echo "Uncommitted files:"
    git status --porcelain
    
    read -p "Do you want to commit and push now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "Add Render configuration and deployment files"
        git push origin main
        echo "✅ Changes committed and pushed"
    else
        echo "Please commit and push your changes manually before deploying to Render."
    fi
fi

echo ""
echo "🎉 Repository is ready for Render deployment!"
echo ""
echo "Next steps:"
echo "1. Go to https://render.com and sign in"
echo "2. Click 'New +' and select 'Blueprint'"
echo "3. Connect your GitHub repository"
echo "4. Select this repository"
echo "5. Set up environment variables in Render dashboard:"
echo "   - MONGO_URL (MongoDB connection string)"
echo "   - DB_NAME (database name)"
echo "   - APPWRITE_ENDPOINT (Appwrite server URL)"
echo "   - APPWRITE_PROJECT_ID (your project ID)"
echo "   - APPWRITE_API_KEY (your API key)"
echo "   - APPWRITE_BUCKET_ID (your bucket ID)"
echo ""
echo "📖 For detailed instructions, see RENDER_DEPLOYMENT.md"
echo ""
echo "🔗 Useful links:"
echo "   - Render Dashboard: https://dashboard.render.com"
echo "   - MongoDB Atlas: https://cloud.mongodb.com"
echo "   - Appwrite Cloud: https://cloud.appwrite.io"
