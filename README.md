# 🌤️ Weather Intelligence Agent

The **Weather Intelligence Agent** is a production-ready, serverless AI assistant built using the **Google Agent Development Kit (ADK)** and **Gemini 2.5 Flash**. It democratizes access to complex data by allowing users to ask natural language questions about historical weather (e.g., *"What was the average rainfall in New York in June 2023?"*). 

Instead of relying on pre-trained knowledge, the agent dynamically translates the user's intent into BigQuery SQL, executes it securely against NOAA's massive Global Historical Climatology Network (GHCN) public dataset using the **MCP Toolbox**, and returns accurate, data-backed insights via a seamless web UI.

## 🏗️ Architecture
1. **Frontend:** A clean HTML/JS interface served via FastAPI.
2. **Backend:** A FastAPI server handling HTTP requests and managing stateless ADK sessions.
3. **Agent:** ADK orchestration powered by Gemini 2.5 Flash for reasoning, parameter extraction, and plain-English generation.
4. **Tools:** The Model Context Protocol (MCP) Toolbox running as a sidecar, executing parameterized SQL queries directly against BigQuery.

## Prerequisites

* Python 3.12+
* Google Cloud SDK (`gcloud`) installed and authenticated
* A Google Cloud Project with Billing Enabled
* Required APIs enabled: `aiplatform.googleapis.com`, `run.googleapis.com`, `bigquery.googleapis.com`, `artifactregistry.googleapis.com`, `cloudbuild.googleapis.com`

## 🚀 Step-by-Step Deployment Guide

This guide assumes you are using **Google Cloud Shell**, which comes pre-installed with all the necessary CLI tools.

### Phase 1: Prerequisites & Setup

1. **Open Google Cloud Shell** in your Google Cloud Console.
2. **Set your active project:**

    ```bash
     gcloud config set project <YOUR_PROJECT_ID>
    ```

3. **Link billing account** (required for BigQuery + Cloud Run):

    ```bash
    gcloud billing accounts list
    gcloud billing projects link YOUR_PROJECT_ID \
      --billing-account=YOUR_BILLING_ACCOUNT_ID
    ```

4. **Enable Required APIs:**

    ```bash
    gcloud services enable \
    aiplatform.googleapis.com \
    run.googleapis.com \
    bigquery.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com
    ```

### Phase 2: Clone & Configure

1. **Clone the repository:**

    ```bash
    git clone https://github.com/thatengineerguy21/ weather-intelligence-agent.git
    cd weather-intelligence-agent
    ```

2. **Download the MCP Toolbox Binary:**

    Because the toolbox is a large binary, it is not stored in source control. Download it directly into the mcp-toolbox directory:

    ```bash
    cd mcp-toolbox
    export VERSION=0.23.0
    curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
    chmod +x toolbox
    cd ..
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
    cd ..
    ```
  
    Last Resort (Not Recommended, only do if curl doesn't work at all):

    ```bash
    gsutil cp gs://genai-toolbox/v$VERSION/linux/amd64/toolbox .
    chmod +x toolbox
    cd ..
    ```

3. **Update Configuration Files:**

    * Open mcp-toolbox/tools.yaml and replace YOUR_PROJECT_ID with your actual GCP Project ID.
    * Copy the environment template:

      ```bash
      cp .env.example .env
      ``` 

    * Open .env and replace the placeholder with your Project ID.
    * Replace `YOUR_PROJECT_ID` in `tools.yaml` with your actual GCP project ID.


### Phase 3: Grant IAM Permissions

For the build process to succeed and the deployed Cloud Run agent to access Gemini and BigQuery, the service accounts need specific permissions.

First, get your Project Number (different from your Project ID):

```bash
gcloud projects describe <YOUR_PROJECT_ID> --format="value(projectNumber)"
```
Then, run these commands (replace <YOUR_PROJECT_ID> and <YOUR_PROJECT_NUMBER> accordingly):

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

### Phase 4: Build & Deploy to Cloud Run

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

### 💻 Usage

Once the deployment completes, the terminal will output a Service URL (e.g., `https://weather-intelligence-agent-xxx.a.run.app` ).

1. **Web UI:**
Simply click the Service URL to open the interactive chat interface in your browser.

2. **API Endpoint:**
You can interact with the agent programmatically via HTTP POST:

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

### 🛠️ Local Development (Optional)

If you wish to test the agent locally before deploying (Local here can be your own machine or cloud shell):

1. **Create a virtual environment:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2. **In Terminal 1, start the MCP Toolbox:**

    ```bash
    cd mcp-toolbox
    ./toolbox --tools-file tools.yaml
    ```

3. **In Terminal 2, start the FastAPI server:**

    ```bash
    python main.py
    ```

4. **Access the UI at http://localhost:8080 (or use Cloud Shell Web Preview).**

### Preview

Web UI:
![Web UI Preview Image](https://github.com/thatengineerguy21/weather-intelligence-agent/blob/main/preview/ui.png)

CLI:
![CLI Preview Image](https://github.com/thatengineerguy21/weather-intelligence-agent/blob/main/preview/cli.png)