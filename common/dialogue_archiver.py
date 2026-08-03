"""Dialogue Archiver & Storage Vault.

Manages recording of text dialogues, session history, and toggleable raw audio file retention.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class DialogueArchiver:

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = data_dir or Path(__file__).resolve().parent.parent / "data"
        self.audio_dir = self.data_dir / "audio"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self._dialogues: Dict[str, List[Dict[str, Any]]] = {}

        # Default setting: Save Audio Recordings is OFF for privacy & disk space
        self.save_audio_enabled = False

    def archive_message(
        self,
        session_id: str,
        sender_role: str,
        content: str,
        channel: str = "whatsapp",
        language: str = "en",
        audio_file_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Record a single dialogue message into session history."""
        timestamp = datetime.now(timezone.utc).isoformat()

        saved_audio_path: Optional[str] = None

        if audio_file_path and audio_file_path.exists():
            if self.save_audio_enabled:
                # Save audio file to storage
                dest_file = self.audio_dir / f"{session_id}_{int(datetime.now().timestamp())}{audio_file_path.suffix}"
                dest_file.write_bytes(audio_file_path.read_bytes())
                saved_audio_path = str(dest_file)
            else:
                # Delete temporary audio file (default mode)
                try:
                    audio_file_path.unlink(missing_ok=True)
                except Exception:
                    pass

        entry = {
            "session_id": session_id,
            "timestamp": timestamp,
            "sender_role": sender_role,
            "content": content,
            "channel": channel,
            "language": language,
            "audio_file": saved_audio_path,
        }

        if session_id not in self._dialogues:
            self._dialogues[session_id] = []

        self._dialogues[session_id].append(entry)
        return entry

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve full dialogue history for a session."""
        return self._dialogues.get(session_id, [])
