---
name: vertex-ai-optimization
description: Best practices for optimizing Gemini 3.5 Flash models on Vertex AI with Structured Outputs, Prompt Caching, and low-latency retries.
---

# Vertex AI & Gemini Model Optimization Skill

## Overview
This skill provides instructions and patterns for optimizing Vertex AI Gemini models (Gemini 3.5 Flash and Gemini 2.5 Flash) within the Beauty Care Multi-Agent Platform.

## Core Guidelines
1. **Structured Outputs**:
   - Always enforce `response_mime_type="application/json"` in `generate_content_config`.
   - Pass explicit Pydantic models (such as `StructuredAgentMessage`) into `output_schema` when initializing Google ADK agents.

2. **Model Fallback Cascade**:
   - Primary Model: `gemini-3.5-flash` (for fast reasoning & structured buttons).
   - Fallback Model: `gemini-2.5-flash` (if region availability or quota constraints occur).

3. **PII Token Preservation**:
   - When PII tokens (e.g. `[PHONE_TOKEN_...]`, `[EMAIL_TOKEN_...]`) are present in input prompts, system instructions MUST enforce literal preservation of token names without modification.
