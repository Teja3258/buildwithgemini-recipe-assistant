# Recipe Assistant Agent 🍲

A full-stack, intelligent Recipe Assistant built with the **Google Agent Development Kit (ADK)**, **Agent Platform (Reasoning Engine)**, **GCP Firestore**, and **Cloud Run**. It provides recipe recommendations, pantry inventory tracking, automated shopping list generation, AI food illustration generation using `gemini-3.1-flash-lite-image`, and rich **A2UI card interfaces**.

---

## 🚀 Live Cloud Run Application

Experience the live deployed application on Cloud Run:
👉 **[https://recipe-assistant-frontend-519752822407.us-east1.run.app](https://recipe-assistant-frontend-519752822407.us-east1.run.app)**

---

## 🎥 Demo Video

Watch the agent in action executing recipe searches and generating AI food photography with A2UI card interfaces:

[![Recipe Assistant Demo Video](https://raw.githubusercontent.com/Teja3258/buildwithgemini-recipe-assistant/main/recipe_assistant_demo.webm)](https://github.com/Teja3258/buildwithgemini-recipe-assistant/blob/main/recipe_assistant_demo.webm)

---

## 🌟 Architecture Overview

```
                        ┌─────────────────────────────────────────┐
                        │      Cloud Run Chat UI / ADK Web        │
                        │    (FastAPI Proxy + A2UI Renderer)      │
                        └────────────────────┬────────────────────┘
                                             │ A2A Protocol
                                             ▼
                        ┌─────────────────────────────────────────┐
                        │         Agent Platform Engine           │
                        │  (Reasoning Engine / ADK Root Agent)    │
                        └────────┬──────────────────────┬─────────┘
                                 │                      │
                                 ▼                      ▼
                    ┌────────────────────────┐    ┌────────────────────────┐
                    │   Google Cloud Storage │    │     GCP Firestore      │
                    │  Public Recipe Assets  │    │  (recipes & pantry)    │
                    └────────────────────────┘    └────────────────────────┘
```

---

## ✨ Features

- **Recipe Search (`search_recipes`)**: Query stored recipes filtered by cuisine, prep time, and ingredients.
- **Pantry Inventory (`list_pantry_items`, `add_pantry_item`)**: Track pantry items with real-time Firestore persistence.
- **Shopping List Generator (`generate_shopping_list`)**: Compare available pantry stock against recipe ingredients to find missing items.
- **AI Food Illustration (`generate_item_image`)**: Generate appetizing studio food photography using Vertex AI `gemini-3.1-flash-lite-image` model stored in Google Cloud Storage.
- **Rich A2UI Display**: Renders responses as responsive display cards, ingredient lists, and image hero components.

---

## 🚀 Project Structure

```
recipe-assistant/
├── app/
│   ├── agent.py           # ADK Agent definition & prompt
│   ├── tools.py           # Tool definitions (Recipes, Pantry, Image Gen)
│   ├── firestore_db.py    # GCP Firestore persistence layer
│   └── a2ui_utils.py     # A2UI response formatting & image sanitization
├── frontend/
│   ├── main.py            # FastAPI proxy server (A2A protocol bridge)
│   ├── static/            # Chat UI & A2UI web renderer
│   └── Dockerfile         # Cloud Run container setup
├── deployment_metadata.json # Deployed Reasoning Engine metadata
└── pyproject.toml         # Project dependencies
```

---

## 🛠️ Setup & Local Development

### 1. Prerequisites
- Python 3.11+
- Google Cloud SDK (`gcloud`)
- `agents-cli` (v1.1.0+)

### 2. Environment Variables
Ensure GCP credentials and project ID are configured:
```bash
export GCP_PROJECT="qwiklabs-gcp-02-49bffb3cf692"
export GOOGLE_CLOUD_LOCATION="global"
```

### 3. Run Locally with ADK Web
```bash
# Start local agent playground
agents-cli web --agent app:root_agent
```

### 4. Run Frontend Proxy Locally
```bash
cd frontend
pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="projects/519752822407/locations/us-east1/reasoningEngines/6308181882550878208"
export AGENT_DIRECTORY="app"
python main.py
```
Open http://localhost:8080 in your browser.

---

## 🚢 Deployment

### 1. Deploy Agent to Agent Platform
```bash
agents-cli deploy --no-confirm-project
```

### 2. Deploy Frontend to Cloud Run
```bash
cd frontend
gcloud run deploy recipe-assistant-frontend \
  --source . \
  --region us-east1 \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="<REASONING_ENGINE_RESOURCE_NAME>",AGENT_DIRECTORY="app" \
  --allow-unauthenticated
```

---

## 🧪 Testing the Agent

Test the deployed agent directly using `agents-cli`:

```bash
# Query available recipes
agents-cli run "Show me available recipes." --url <REASONING_ENGINE_URL> --mode a2a

# Generate a dish image
agents-cli run "Generate an image for Garlic Butter Chicken Bowl" --url <REASONING_ENGINE_URL> --mode a2a
```
