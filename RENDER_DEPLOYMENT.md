# Render Deployment Guide

This guide will help you deploy your File Manager application to Render with automatic deployments and PR previews.

## Prerequisites

1. **GitHub Repository**: Your code should be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **MongoDB Database**: You'll need a MongoDB connection string (MongoDB Atlas recommended)
4. **Appwrite Account**: Set up your Appwrite project and get the required credentials

## Step 1: Prepare Your Repository

1. **Ensure render.yaml is in your repository root** (✅ Already done)
2. **Commit and push your changes**:
   ```bash
   git add .
   git commit -m "Add Render configuration"
   git push origin main
   ```

## Step 2: Connect to Render

1. Go to [render.com](https://render.com) and sign in
2. Click "New +" and select "Blueprint"
3. Connect your GitHub repository
4. Select your File Manager repository
5. Render will automatically detect the `render.yaml` file

## Step 3: Configure Environment Variables

In the Render dashboard, you'll need to set these environment variables:

### Required Environment Variables:

```env
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
DB_NAME=file_manager
APPWRITE_ENDPOINT=https://fra.cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=your_project_id
APPWRITE_API_KEY=your_api_key
APPWRITE_BUCKET_ID=your_bucket_id
```

### How to Set Environment Variables:

1. In your Render service dashboard, go to "Environment"
2. Add each variable with its corresponding value
3. Click "Save Changes"

## Step 4: MongoDB Setup (Recommended: MongoDB Atlas)

1. **Create MongoDB Atlas Account**:
   - Go to [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)
   - Create a free account

2. **Create a Cluster**:
   - Choose the free tier (M0)
   - Select a region close to your Render region (Oregon)

3. **Create Database User**:
   - Go to "Database Access"
   - Create a user with read/write permissions

4. **Configure Network Access**:
   - Go to "Network Access"
   - Add IP address `0.0.0.0/0` (allow from anywhere)

5. **Get Connection String**:
   - Go to "Database" → "Connect"
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password

## Step 5: Appwrite Setup

1. **Create Appwrite Project**:
   - Go to [cloud.appwrite.io](https://cloud.appwrite.io)
   - Create a new project

2. **Create Storage Bucket**:
   - Go to "Storage"
   - Create a new bucket for file uploads

3. **Get API Key**:
   - Go to "Settings" → "API Keys"
   - Create a new API key with appropriate permissions

4. **Configure Permissions**:
   - Set appropriate read/write permissions for your bucket

## Step 6: Deploy

1. **Automatic Deployment**:
   - Once environment variables are set, Render will automatically deploy
   - Monitor the deployment logs for any issues

2. **Manual Deployment**:
   - Click "Deploy latest commit" if needed

## Step 7: Enable PR Previews

PR Previews are automatically enabled with the `render.yaml` configuration:

- **Automatic**: Every PR will create a preview environment
- **Expiration**: Preview environments expire after 30 days
- **Access**: Preview URLs will be posted in your PR comments

## Troubleshooting

### Common Issues:

1. **Build Failures**:
   - Check that all dependencies are correctly specified
   - Ensure Docker builds successfully locally first

2. **Environment Variable Issues**:
   - Verify all required environment variables are set
   - Check for typos in variable names

3. **Database Connection Issues**:
   - Ensure MongoDB connection string is correct
   - Check network access settings in MongoDB Atlas

4. **Appwrite Issues**:
   - Verify API key permissions
   - Check bucket permissions and settings

### Debugging Steps:

1. **Check Logs**:
   - Go to your service dashboard
   - Check "Logs" tab for error messages

2. **Test Locally**:
   - Use Docker to test the same configuration locally
   - Run: `docker-compose up --build`

3. **Health Check**:
   - Render will check `/` for a 200 response
   - Ensure your frontend serves correctly

## Configuration Options

### Scaling (Paid Plans):

```yaml
services:
  - type: web
    name: file-manager
    plan: starter  # or professional
    scaling:
      minInstances: 1
      maxInstances: 3
```

### Custom Domain:

```yaml
domains:
  - file-manager.yourdomain.com
```

### Resource Limits:

```yaml
disk:
  name: file-manager-disk
  mountPath: /app/data
  sizeGB: 10  # Increase as needed
```

## Monitoring

1. **Render Dashboard**: Monitor deployment status and logs
2. **Health Checks**: Automatic health monitoring
3. **Alerts**: Set up alerts for downtime or errors

## Security Best Practices

1. **Environment Variables**: Never commit sensitive data to your repository
2. **Database Security**: Use strong passwords and restrict IP access
3. **API Keys**: Rotate API keys regularly
4. **HTTPS**: Render automatically provides SSL certificates

## Support

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Render Community**: [community.render.com](https://community.render.com)
- **GitHub Issues**: Create issues in your repository for application-specific problems
