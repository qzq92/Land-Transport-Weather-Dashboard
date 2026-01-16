# Plotly Cloud Deployment Guide

This guide will help you deploy this Dash application to Plotly Cloud.

## Prerequisites

1. **Plotly Cloud Account**: Sign up at [Plotly Cloud](https://plotly.com/)
2. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, Bitbucket, etc.)
3. **API Keys**: Ensure you have all required API keys ready

## Pre-Deployment Checklist

### ✅ Code Configuration
- [x] `server = app.server` is exposed in `app.py` (line 874)
- [x] `app.run()` is wrapped in `if __name__ == "__main__":` block
- [x] `gunicorn` is included in `requirements.txt`
- [x] All dependencies are listed in `requirements.txt`

### ✅ Environment Variables
You'll need to set these in Plotly Cloud:
- `DATA_GOV_API` - Your Data.gov.sg API key
- `ONEMAP_API_KEY` - Your OneMap API key  
- `LTA_API_KEY` - Your LTA DataMall API key

### ✅ Files to Exclude
Ensure `.gitignore` includes:
- `.env` (never commit API keys!)
- `data/` directory (will be created on first run)
- `*.pyc` files
- Virtual environment directories

## Deployment Steps

### 1. Prepare Your Repository

```bash
# Ensure all changes are committed
git add .
git commit -m "Prepare for Plotly Cloud deployment"
git push origin main
```

### 2. Connect to Plotly Cloud

1. Log in to [Plotly Cloud](https://plotly.com/)
2. Navigate to your workspace
3. Click **"Create App"** or **"New App"**
4. Select **"Connect to Git Repository"**
5. Authorize Plotly Cloud to access your repository
6. Select your repository and branch (usually `main` or `master`)

### 3. Configure Environment Variables

1. In your Plotly Cloud app settings, go to **"Environment Variables"**
2. Add the following variables:

```
DATA_GOV_API=your_data_gov_api_key_here
ONEMAP_API_KEY=your_onemap_api_key_here
LTA_API_KEY=your_lta_api_key_here
```

**Important**: Never commit these keys to your repository!

### 4. Deploy

1. Plotly Cloud will automatically detect your Dash app
2. Click **"Deploy"** or **"Build"**
3. Monitor the build logs for any errors
4. The app will be available at `https://your-app-name.plotly.com`

## Post-Deployment

### First Startup Behavior

On first deployment, the app will automatically:
- Create the `data/` directory
- Download HDB carpark information (if file doesn't exist)
- Download speed camera locations (if file doesn't exist)
- Initialize OneMap API authentication
- Start fetching and caching data from APIs

### Monitoring

- Check build logs for any startup errors
- Monitor app performance in Plotly Cloud dashboard
- Verify all API calls are working correctly
- Check that environment variables are properly set

## Troubleshooting

### Common Issues

1. **Build Fails**
   - Check that all dependencies in `requirements.txt` are valid
   - Verify Python version compatibility
   - Check build logs for specific error messages

2. **API Calls Fail**
   - Verify environment variables are set correctly
   - Check API key validity
   - Review app logs for authentication errors

3. **Data Files Not Downloading**
   - Check network connectivity
   - Verify API endpoints are accessible
   - Review startup logs for download errors

4. **App Crashes on Startup**
   - Check that `server = app.server` is exposed
   - Verify `app.run()` is only called in `if __name__ == "__main__":` block
   - Review error logs in Plotly Cloud dashboard

## Application Architecture

### Async API Pattern

All API calls use the `@run_in_thread` decorator pattern:

```python
from utils.async_fetcher import run_in_thread

@run_in_thread
def fetch_data_async():
    # API call implementation
    return data

# Usage in callbacks
future = fetch_data_async()
data = future.result() if future else None
```

This ensures:
- Non-blocking API calls
- Improved responsiveness
- Better scalability
- Consistent async pattern across all API calls

## Support

For issues specific to:
- **Plotly Cloud**: Contact Plotly Cloud support
- **API Access**: Contact respective API providers (Data.gov.sg, OneMap, LTA)
- **Application Code**: Review logs and check GitHub issues

