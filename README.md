# 🌸 Beauty Care — Multi-Agent AI Platform for Beauty Salons & Spas

Multilingual Production-Ready AI Platform for Beauty Salons built on a decentralized Multi-Agent Architecture (**A2A + Agent Registry + MCP + RAG + PII Security + i18n + Instant Google Calendar CRM + Payments & Receipts + Health Monitoring & RBAC + STT Voice Transcription + LTV Retention & Reputation Boosters + Google Maps + Dokploy PaaS + Dedicated GCP: beauty-care-platform + Free Cloudflare SSL Subdomain Architecture: *.oxyjet.win**).

---

## 📅 Instant CRM Integration: Google Calendar API

The platform uses **Google Calendar API** within the dedicated GCP project `beauty-care-platform` for instant, zero-cost, 100% open CRM calendar scheduling:
* **Instant Start**: No approval process or partner API keys required.
* **Master Smartphone Sync**: Masters and salon managers see appointment bookings in real-time on Google Calendar app (iOS / Android).
* **Open MCP Tools**: Uses `get_services()`, `get_available_slots()`, `create_booking()`, `cancel_booking()` MCP interface.

---

## 🌐 Free Cloudflare Universal SSL Subdomain Architecture (*.oxyjet.win)

* **Main Salon Website & Web Widget**: `https://beauty.oxyjet.win`
* **Messaging & Payment Webhooks**: `https://beauty-api.oxyjet.win/v1/webhook/`
* **Agent Registry MCP**: `https://beauty-registry.oxyjet.win/mcp`
* **Admin Knowledge CMS & Settings**: `https://beauty-admin.oxyjet.win`
* **A2A Agent Endpoints**: `https://beauty-agents.oxyjet.win/{agent-id}/`

---

## ☁️ Dedicated Google Cloud Project: `beauty-care-platform`

* **Vertex AI API** (`aiplatform.googleapis.com`)
* **Google Calendar API** (`calendar.googleapis.com`)
* **Google Maps Places API (New)** (`places.googleapis.com`)
* **Google Maps Routes API** (`routes.googleapis.com`)
* **Agent Registry API** (`agentregistry.googleapis.com`)

---

## 🛠️ Technology Stack

* **CRM Calendar**: Google Calendar API (Instant & Open) / DIKIDI / YClients
* **Cloudflare SSL Subdomain Scheme**: `beauty-*.oxyjet.win`
* **Dedicated GCP Project**: `beauty-care-platform`
* **Production Deployment**: Dokploy PaaS, Docker, Traefik
* **Domain & DNS**: Cloudflare DNS & Proxy (Universal SSL 🟧)
* **Growth Engines**: MarketingRetentionAgent, ReputationAgent
* **Security & Access Control**: JWT Authentication, RBAC
* **Observability & Logging**: OpenTelemetry, `/healthz` Probes, Telegram/Sentry Alerting
* **Payment Gateways**: Stripe API, TBC Bank API, YooKassa API (54-ФЗ)
* **Voice Transcription (STT)**: Whisper / Google Speech-to-Text / SpeechKit
* **Dialogue Database**: Encrypted PostgreSQL (on Dokploy)
* **Mapping Service**: Google Maps Platform (Places API New, Routes API, Geocoding API)
* **Language & Package Manager**: Python 3.11+, `uv`
* **Agent Inter-communication**: Agent-to-Agent (A2A) Protocol
* **Tool Interface Protocol**: Model Context Protocol (MCP)
* **Agent Catalog**: Custom / Cloud-Agnostic Agent Registry Server
* **LLM Engines**: Gemini 3.5 Flash-Lite / Open-Source (Llama 3.3, Qwen 2.5 via Ollama / vLLM)
* **Multilingual Vector Search (RAG)**: Qdrant / Pgvector (`multilingual-e5-large` / `text-embedding-004`)
* **Messaging Gateways**: WhatsApp Business API / GreenAPI, Telegram Bot API
