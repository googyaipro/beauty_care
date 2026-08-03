"""PII Sanitizer & De-anonymization Gateway for 152-ФЗ / GDPR Compliance.

Strips personal identifiable information (PII) before sending prompts to external LLMs,
and restores client details for local messaging channels.
"""

import re
import uuid
from typing import Dict, Tuple


class PIISanitizer:

    def __init__(self) -> None:
        # Maps anonymized tokens to real data for the active session
        self._vault: Dict[str, str] = {}
        self._reverse_vault: Dict[str, str] = {}

    def sanitize(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Scan text for PII (Phone numbers, emails, names) and replace with tokens.

        Returns:
            Sanitized text and mapping dict.
        """
        if not text:
            return text, {}

        sanitized_text = text

        # 1. Sanitize Phone Numbers (E.164, Russian, European formats)
        phone_pattern = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}"
        for match in re.finditer(phone_pattern, sanitized_text):
            phone = match.group(0)
            if len(re.sub(r"\D", "", phone)) >= 10:  # Ensure it's a real phone number
                if phone not in self._reverse_vault:
                    token = f"[PHONE_TOKEN_{uuid.uuid4().hex[:6].upper()}]"
                    self._vault[token] = phone
                    self._reverse_vault[phone] = token
                sanitized_text = sanitized_text.replace(phone, self._reverse_vault[phone])

        # 2. Sanitize Email Addresses
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        for match in re.finditer(email_pattern, sanitized_text):
            email = match.group(0)
            if email not in self._reverse_vault:
                token = f"[EMAIL_TOKEN_{uuid.uuid4().hex[:6].upper()}]"
                self._vault[token] = email
                self._reverse_vault[email] = token
            sanitized_text = sanitized_text.replace(email, self._reverse_vault[email])

        return sanitized_text, dict(self._vault)

    def restore(self, text: str) -> str:
        """Replace anonymized tokens back to original PII for local messaging."""
        if not text:
            return text

        restored_text = text
        for token, original_value in self._vault.items():
            restored_text = restored_text.replace(token, original_value)

        return restored_text
