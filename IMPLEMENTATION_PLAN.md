# 🌸 Beauty Care — Multi-Agent Ecosystem for Salon & Spa

Платформа автономии и обслуживания клиентов салонов красоты на базе мультиагентной архитектуры (**A2A + Agent Registry + MCP + RAG + PII Security 152-ФЗ + i18n + Payments & Receipts + Health Monitoring & RBAC + STT Voice Transcription + No-Show Prevention & LTV Retention + Google Maps + Dedicated GCP: beauty-care-platform + Free Cloudflare SSL Architecture: *.oxyjet.win + Dokploy PaaS**).

---

## 🌐 Продакшен-домен и Бесплатный Cloudflare Universal SSL

Официальная поддоменная схема платформы: **`beauty-*.oxyjet.win`** (Управление через **Cloudflare Universal SSL & Proxy 🟧** + **Dokploy PaaS**).

### Поддоменная карта платформы (100% покрытие бесплатным SSL):
* 🌐 **Главный сайт и Виджет записи салона**: `https://beauty.oxyjet.win`
* 🔌 **Шлюзы мессенджеров (Webhooks WhatsApp/TG/VK/Payments)**: `https://beauty-api.oxyjet.win/v1/webhook/`
* 🗂️ **Реестр Агентов (Agent Registry MCP Server)**: `https://beauty-registry.oxyjet.win/mcp`
* 🎛️ **Панель Управления Знаниями (Admin RAG CMS)**: `https://beauty-admin.oxyjet.win`
* 🤖 **Точки подключения A2A Агентов**: `https://beauty-agents.oxyjet.win/{agent-id}/`

---

## ☁️ Выделенный Google Cloud Проект: `beauty-care-platform`

1. `aiplatform.googleapis.com` (Vertex AI / Gemini 3.5 Flash-Lite)
2. `places.googleapis.com` (Google Maps Places API New)
3. `routes.googleapis.com` (Google Maps Routes API)
4. `agentregistry.googleapis.com` (Agent Registry API)

---

## 📁 Дерево файлов проекта

```text
beauty_care/
├── .env.example
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── IMPLEMENTATION_PLAN.md
├── README.md
├── BRAINSTORMING_LOG.md
├── locales/
│   ├── en.json
│   ├── ru.json
│   ├── ka.json
│   ├── de.json
│   ├── it.json
│   ├── es.json
│   └── fr.json
├── common/
│   ├── a2a_client.py
│   ├── auth.py
│   ├── rbac.py
│   ├── health_checker.py
│   ├── dialogue_archiver.py
│   ├── stt_engine.py
│   ├── language_detector.py
│   ├── pii_sanitizer.py
│   └── registry_client.py
├── registry_server/
│   └── server.py
├── agents/
│   ├── concierge_agent/
│   ├── hair_care_agent/
│   ├── cosmetology_agent/
│   ├── nail_style_agent/
│   ├── navigation_agent/
│   ├── marketing_retention_agent/
│   ├── reputation_agent/
│   └── booking_crm_agent/
├── mcp_servers/
│   ├── dikidi_crm_mcp/
│   ├── payment_mcp/
│   ├── maps_mcp/
│   └── rag_knowledge_mcp/
├── gateways/
│   ├── telegram_gateway.py
│   ├── whatsapp_gateway.py
│   └── payment_webhook_gateway.py
└── admin_cms/
    └── app.py
```
