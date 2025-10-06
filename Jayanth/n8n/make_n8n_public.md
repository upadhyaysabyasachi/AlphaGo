# Make n8n Public — Free Production Setup (Docker + Ngrok)
**Expose your self-hosted  [n8n](https://n8n.io/)  server to the internet for free with  [Ngrok](https://ngrok.com/).**  
No domain. No paid hosting. No data loss.
## Why do this?

-   Run webhooks and integrations (Telegram, Gmail, YouTube, Stripe, etc.) that require a public HTTPS URL.
    
-   Access your automations from anywhere, like n8n cloud—but self-hosted and free.
## Prerequisites

-   Basic Docker knowledge (but step-by-step provided)
    
-   [Docker Desktop](https://www.docker.com/products/docker-desktop)  installed
    
-   [Ngrok account (free tier)](https://ngrok.com/)
    
-   n8n installed locally (Docker container)
    
-   Optional: n8n workflows already created
## Step 1: Install Ngrok

1.  **Sign up**  for a free account at  [ngrok.com](https://ngrok.com/).
    
2.  **Download**  Ngrok from your dashboard.
    
3.  **Unzip**  the Ngrok archive to any folder.
## Step 2: Prepare n8n Docker Data

-   **Stop and remove**  your existing n8n container (but keep the data folder/volume!).
    
-   This ensures you keep your workflows, credentials, and execution history.
## Step 3: Set Up the Docker Container (with Ngrok Domain)

1.  On Docker Desktop, run a new n8n container but  **reuse the same data folder**  (volume) as your old instance.
    
2.  **Set Environment Variables**  (important!):
# These env variables MUST point to your public ngrok URL
```
# These env variables MUST point to your public ngrok URL
- N8N_EDITOR_BASE_URL=<Ngrok HTTPS domain>      # e.g. https://extra-coder.ngrok-free.dev
- WEBHOOK_URL=<Ngrok HTTPS domain>              # same as above
- N8N_DEFAULT_BINARY_DATA_MODE=filesystem       # improves stability for large files
- N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE=true            # optional for extra nodes
```
**Volume Mapping:**  
Map your Docker host's data directory to `/home/node/.n8n`  **(EXACTLY as before)** so nothing is lost.
## Step 4: Start Your n8n Docker Container

-   Example (edit ports/paths as needed):
```
docker run -it --rm \
  -p 5678:5678 \
  -v ~/n8n_data:/home/node/.n8n \
  -e N8N_EDITOR_BASE_URL=https://your-ngrok-domain.ngrok-free.dev \
  -e WEBHOOK_URL=https://your-ngrok-domain.ngrok-free.dev \
  -e N8N_DEFAULT_BINARY_DATA_MODE=filesystem \
  n8nio/n8n
```
-   Wait for the container to start and make sure all your old workflows are present.
## Step 5: Authenticate Ngrok & Start the Tunnel

1.  **Add your Ngrok Auth Token**  (from the dashboard):
2. Go to the folder where you've unzipped ngrok  and run below command, if it's a Windows machine, remove ./ before the command.
```
./ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>
```
3. **Expose your local n8n port** using Ngrok:
```
./ngrok http --url=<dev domain> 5678
```
4.  Copy the  **public HTTPS URL**  Ngrok generates (e.g.,  `https://extra-coder.ngrok-free.dev`).
## Step 6: Test Everything

-   Open the  **ngrok public URL**  in your browser.
    
-   Log in to n8n. Ensure all previous workflows/data remain.
    
-   Use the public URL for webhook integrations (Telegram, Stripe, etc.).
    
-   Your local instance is now live online, securely tunnelled with HTTPS!
