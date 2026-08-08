---
name: gcp-secret-management
description: Secure credential handling, GCP Secret Manager integration, and 152-ФЗ / GDPR PII encryption compliance.
---

# GCP Secret Management & Security Skill

## Overview
This skill governs secure credential retrieval and PII data sanitization across all Beauty Care microservices.

## Core Rules
1. **Credentials Materialization**:
   - `SERVICE_ACCOUNT_KEY_JSON` is stored securely as environment variables or Secret Manager payloads.
   - Microservices dynamically materialize credentials to `/tmp/service-account-key.json` and export `GOOGLE_APPLICATION_CREDENTIALS=/tmp/service-account-key.json` for Google ADK ADC compatibility.

2. **PII Sanitization (GDPR & 152-ФЗ)**:
   - All incoming text from Telegram/WhatsApp gateways must pass through `PIISanitizer` before reaching the LLM orchestrator.
   - Phone numbers and emails are replaced with token vaults (`[PHONE_TOKEN_...]`, `[EMAIL_TOKEN_...]`) and restored prior to outbound API delivery.
