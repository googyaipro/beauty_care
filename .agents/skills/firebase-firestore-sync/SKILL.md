---
name: firebase-firestore-sync
description: Real-time persistence for salon bookings, client history, and master preferences using Google Cloud Firestore.
---

# Firebase Firestore Sync Skill

## Overview
Guidelines for persisting appointment history, client preferences, and dialogue sessions in Google Cloud Firestore.

## Architecture Guidelines
1. **Dialogue Store Backup**:
   - `SharedDialogueStore` maintains fast in-memory session contexts for immediate LLM context window assembly.
   - Session messages can asynchronously flush to Firestore collections (`salon_sessions/{session_id}/messages`) for persistent audit logging.

2. **Client Profile Enrichment**:
   - Store master preferences (e.g. "Anna (Top Stylist)"), past appointment dates, and favorite services in `salon_clients/{client_id}`.
