# 🌤️ Weather Intelligence Agent

The **Weather Intelligence Agent** is a production-ready, serverless AI assistant built using the **Google Agent Development Kit (ADK)** and **Gemini 2.5 Flash**. It democratizes access to complex data by allowing users to ask natural language questions about historical weather (e.g., *"What was the average rainfall in New York in June 2023?"*).

Instead of relying on pre-trained knowledge, the agent dynamically translates the user's intent into BigQuery SQL, executes it securely against NOAA's massive Global Historical Climatology Network (GHCN) public dataset using the **MCP Toolbox**, and returns accurate, data-backed insights via a seamless web UI.

---

## 🚀 Step-by-Step Deployment Guide

This guide assumes you are using **Google Cloud Shell**, which comes pre-installed with all the necessary CLI tools.

### Phase 1: Prerequisites & Setup

1. **Open Google Cloud Shell** in your Google Cloud Console.
2. **If you don't know your Project ID:**

    ```bash
    gcloud projects list
    ```

3. **Set your active project:**

    ```bash
    gcloud config set project <YOUR_PROJECT_ID>
    ```

4. **Link billing account** (required for BigQuery + Cloud Run):

    ```bash
    gcloud billing accounts list
    gcloud billing projects link YOUR_PROJECT_ID \
      --billing-account=YOUR_BILLING_ACCOUNT_ID
    ```

5. Enable Required APIs:

    ```bash
    gcloud services enable \
    bigquery.googleapis.com \
    run.googleapis.com \
    aiplatform.googleapis.com \
    cloudbuild.googleapis.com
    ```

6. **Setup Project Structure:**

    ```bash
    mkdir mcp-toolbox
    mkdir weather_agent_app
    ```

7. **Install MCP Toolbox for Databases:**

    ```bash
    cd mcp-toolbox
    export VERSION=0.23.0
    curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
    chmod +x toolbox
    ```

    Sometimes `curl` command stalls, Try(Not Recommended):

    ```bash
    # Kill the current download first
    Ctrl+C

    # Try again
    curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
    ```

    OR Else Try:

    ```bash
    wget https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
    chmod +x toolbox
    ```
  
    Last Resort (Not Recommended, only do if curl doesn't work at all):

    ```bash
    gsutil cp gs://genai-toolbox/v$VERSION/linux/amd64/toolbox .
    chmod +x toolbox
    ```

8. **Configure and Start MCP Toolbox:**

    Replace `YOUR_PROJECT_ID` in `tools.yaml` with your actual GCP project ID.

    ```bash
    ./toolbox --tools-file tools.yaml
    ```

### Phase 2: Grant IAM Permissions

For the deployed Cloud Run agent to access Gemini and BigQuery, its service account needs the correct permissions. Run these commands (replace `<YOUR_PROJECT_NUMBER>` with your actual numeric project number):

```bash
# Grant Artifact Registry write access
gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
  --member="serviceAccount:<YOUR_PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Grant Vertex AI access for Gemini
gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
  --member="serviceAccount:<YOUR_PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Grant BigQuery access for the MCP Toolbox
gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
  --member="serviceAccount:<YOUR_PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
  --member="serviceAccount:<YOUR_PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

# Grant Storage access to Cloud Build service account
gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
  --member="serviceAccount:<YOUR_PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
  --member="serviceAccount:<YOUR_PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Also grant Cloud Build service account proper permissions
gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
  --member="serviceAccount:<YOUR_PROJECT_NUMBER>@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Grant Logging Permissions
gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
  --member="serviceAccount:<YOUR_PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --role="roles/logging.logWriter"
```

### Phase 3: Build & Deploy to Cloud Run

We use Artifact Registry and Cloud Build to securely package the application and the MCP Toolbox binary.

1. **Create an Artifact Registry Repository (One-time setup):**

    ```bash
    gcloud artifacts repositories create weather-agent \
      --repository-format=docker \
      --location=us-central1
    ```

2. **Build the Docker Image:**

    ```bash
    gcloud builds submit \
      --tag us-central1-docker.pkg.dev/<YOUR_PROJECT_ID>/weather-agent/weather-intelligence-agent:latest
    ```

3. **Deploy the Image to Cloud Run:**

    ```bash
    gcloud run deploy weather-intelligence-agent \
      --image us-central1-docker.pkg.dev/<YOUR_PROJECT_ID>/weather-agent/weather-intelligence-agent:latest \
      --region us-central1 \
      --allow-unauthenticated \
      --memory 512Mi \
      --timeout 120 \
      --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=1,GOOGLE_CLOUD_PROJECT=<YOUR_PROJECT_ID>,GOOGLE_CLOUD_LOCATION=us-central1
    ```

### Phase 4: Testing the deployed endpoint

```bash
curl -X POST https://YOUR-CLOUD-RUN-URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the average rainfall in Delhi in June 2023?"}'
```

Expected response:

```json
{
  "answer": "Based on NOAA weather station data, Mumbai received an 
  average daily rainfall of approximately 18.4mm during June 2023, 
  with the wettest day recorded on June 14th at 52mm."
}
```

Alternatively, you can also test the Agent in adk development environment, do this in agent cloud shell:

```bash
adk web --host 0.0.0.0 --port 8080 --allow_origins "*"
```
This above command allows for unauthenticated access for testing, **DO NOT LEAK YOUR URL**

