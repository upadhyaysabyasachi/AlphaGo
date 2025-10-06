# n8n Local Setup with Docker Desktop

A comprehensive guide to install and run n8n locally using Docker Desktop with GUI setup - no command line needed!

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Running n8n](#running-n8n)
- [Accessing Your Instance](#accessing-your-instance)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

## Prerequisites

- **A computer** (Mac, Windows, or Linux)
- **Admin/Root access** (required for Docker installation)
- **Internet connection** for downloading Docker and n8n image

### System Requirements by OS:

**Mac:**
- **M1/M2/M3 Mac (Apple Silicon)**: Select Apple Silicon version
- **Intel Mac**: Select Intel chip version

**Windows:**
- **Standard PCs**: AMD64 architecture
- **Copilot+ PCs**: ARM64 architecture
- **WSL 2** will be installed automatically if not present

## Installation Steps

### Step 1: Download Docker Desktop

1. Go to [docker.com](https://docker.com)
2. Click **"Download Docker Desktop"**
3. Select the appropriate version for your system:
   - **Mac M-series**: Apple Silicon
   - **Mac Intel**: Intel chip
   - **Windows Standard**: AMD64
   - **Windows Copilot+ PC**: ARM64

### Step 2: Install Docker Desktop

**Mac Installation:**
1. Mount the downloaded disc image
2. Drag Docker to Applications folder
3. Open Docker Desktop

**Windows Installation:**
1. Run the installer with admin privileges
2. Follow the installation wizard
3. WSL 2 will be installed automatically if needed
4. Restart if prompted

### Step 3: Get Your Timezone

1. Visit the timezone reference link from n8n docs
2. Find your timezone (e.g., `Europe/Berlin`, `America/New_York`, `Asia/Kolkata`)
3. Note it down for later use

## Configuration

### Step 4: Create Persistent Data Volume

1. Open Docker Desktop
2. Navigate to **Volumes** tab
3. Click **"Create Volume"**
4. Name the volume: `n8n_data`

> **Why create a volume?** This ensures your workflows and data persist even when you upgrade n8n, restart your computer, or recreate the container.

### Step 5: Download n8n Image

1. Go to **Images** tab in Docker Desktop
2. Click **"Search for images"**
3. Search for: `n8n`
4. Click **"Pull"** to download the official n8n image

### Step 6: Configure Container Settings

1. After the image downloads, click **"Run"**
2. Fill in the **Optional Settings**:

#### Container Configuration:
- **Container Name**: `n8n`
- **Host Port**: `5678`

#### Volume Mapping:
- **Host Path**: Select the `n8n_data` volume you created
- **Container Path**: `/home/node/.n8n`

### Step 7: Set Environment Variables

Add the following environment variables in Docker Desktop:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `GENERIC_TIMEZONE` | `Your/Timezone` | Generic timezone setting |
| `TZ` | `Your/Timezone` | System timezone |
| `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS` | `true` | Enforce file permissions |
| `NODE_FUNCTION_ALLOW_EXTERNAL` | `true` | Enable external node functions |

**Example with Europe/Berlin timezone:**
```
GENERIC_TIMEZONE=Europe/Berlin
TZ=Europe/Berlin
N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true
NODE_FUNCTION_ALLOW_EXTERNAL=true
```

## Running n8n

1. After configuring all settings, click **"Run"**
2. Docker will create and start the container
3. Wait a few seconds for the container to initialize

## Accessing Your Instance

1. Open your web browser
2. Navigate to: `http://localhost:5678`
3. Create your n8n account (this is local to your machine)
4. Start building workflows!

## Limitations

### Current Limitations:
- **Webhooks**: Not directly accessible from external sources without tunneling
- **External API calls to your instance**: Requires tunnel setup
- **Mobile app notifications**: May need additional configuration

### Solutions:
- **Tunneling**: Set up ngrok or similar service for webhook functionality
- **Cloud alternative**: Consider n8n Cloud for production use

## Environment Variables

### Complete Environment Variables Reference:

```bash
# Timezone Configuration
GENERIC_TIMEZONE=Your/Timezone          # Replace with your timezone
TZ=Your/Timezone                        # Replace with your timezone

# Security Settings
N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true

# Node.js Configuration
NODE_FUNCTION_ALLOW_EXTERNAL=true       # Allows external npm packages

# Optional: Additional Settings
N8N_LOG_LEVEL=info                      # Set logging level
N8N_PORT=5678                          # Internal port (don't change)
N8N_PROTOCOL=http                      # Protocol for local use
N8N_HOST=localhost                     # Host for local use
```

### Common Timezone Examples:
```bash
# Americas
America/New_York
America/Los_Angeles
America/Chicago
America/Toronto
America/Sao_Paulo

# Europe
Europe/London
Europe/Berlin
Europe/Paris
Europe/Amsterdam
Europe/Madrid

# Asia
Asia/Tokyo
Asia/Shanghai
Asia/Kolkata
Asia/Dubai
Asia/Singapore

# Australia
Australia/Sydney
Australia/Melbourne
```

## Troubleshooting

### Container Won't Start
- Check if port 5678 is already in use
- Verify all environment variables are correctly set
- Ensure the volume is properly mounted

### Can't Access n8n Interface
- Confirm container is running in Docker Desktop
- Check if `http://localhost:5678` is accessible
- Verify firewall isn't blocking port 5678

### Data Not Persisting
- Ensure volume `n8n_data` is created and mounted
- Check volume mount path is `/home/node/.n8n`
- Verify volume permissions

### Performance Issues
- Allocate more resources to Docker Desktop
- Check available disk space for volume storage
- Monitor Docker Desktop resource usage

### Docker Desktop Issues
- **Mac**: Ensure Docker has proper permissions
- **Windows**: Verify WSL 2 is running correctly
- **All platforms**: Try restarting Docker Desktop

## Maintenance

### Updating n8n
1. Stop the current container
2. Pull the latest n8n image
3. Recreate container with same settings
4. Your data will persist due to volume mounting

### Backup Your Data
Your workflows are stored in the Docker volume. To backup:
1. Export workflows from n8n interface
2. Or backup the entire Docker volume

### Container Management
- **Start**: Use Docker Desktop interface
- **Stop**: Click stop button in Docker Desktop
- **Logs**: View logs in Docker Desktop for debugging

## Additional Resources

### Official Documentation
- [n8n Docker Documentation](https://go.n8n.io/n8n-docker)
- [n8n Cloud Pricing](https://go.n8n.io/n8n-pricing)

### Learning Resources
- n8n Official YouTube Channel
- n8n Community Forum
- n8n Documentation Website

### Next Steps
- **Webhooks Setup**: Look for tunneling tutorials (ngrok, cloudflare tunnels)
- **Advanced Workflows**: Explore n8n's node library
- **Integrations**: Connect with your favorite services
- **AI Agents**: Build automated AI workflows

## Quick Command Reference

### Docker Desktop Actions
| Action | Location | Description |
|--------|----------|-------------|
| Create Volume | Volumes → Create | Persistent data storage |
| Pull Image | Images → Search | Download n8n image |
| Run Container | Images → Run | Start n8n instance |
| View Logs | Containers → Logs | Debug issues |
| Stop Container | Containers → Stop | Halt n8n |

### URLs
- **Local n8n**: `http://localhost:5678`
- **Docker Desktop**: Available in your applications
- **n8n Docs**: `https://docs.n8n.io`

---

## Notes

- This setup is identical to command-line installation but uses Docker Desktop's GUI
- Perfect for beginners who prefer visual interfaces
- Container settings can be modified later through Docker Desktop
- All data persists across restarts thanks to volume mounting

**Ready to automate your workflows?** This is the easiest way to get started with n8n locally! 
