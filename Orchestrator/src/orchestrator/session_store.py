"""Persistent session storage for Orchestrator Agent."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict
from google.adk.sessions import InMemorySessionService


# Default sessions directory
SESSIONS_DIR = Path(os.getenv("ORCHESTRATOR_SESSIONS_DIR", "./sessions"))


@dataclass
class ConversationMessage:
    """A single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SessionData:
    """Persistent session data."""
    session_id: str
    user_id: str
    app_name: str = "orchestrator"
    title: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    messages: list[ConversationMessage] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "app_name": self.app_name,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in self.messages
            ],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SessionData":
        """Create from dictionary."""
        messages = [
            ConversationMessage(
                role=m["role"],
                content=m["content"],
                timestamp=m.get("timestamp", "")
            )
            for m in data.get("messages", [])
        ]
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            app_name=data.get("app_name", "orchestrator"),
            title=data.get("title", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            messages=messages,
            metadata=data.get("metadata", {})
        )
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append(ConversationMessage(role=role, content=content))
        self.updated_at = datetime.now().isoformat()
        
        # Auto-generate title from first user message if not set
        if not self.title and role == "user":
            self.title = content[:50] + ("..." if len(content) > 50 else "")


class PersistentSessionStore:
    """
    Persistent session storage that saves conversations to disk.
    
    This allows sessions to be resumed across application restarts.
    """
    
    def __init__(self, sessions_dir: Optional[Path] = None):
        """Initialize the session store."""
        self.sessions_dir = sessions_dir or SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, SessionData] = {}
    
    def _get_session_file(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.sessions_dir / f"{session_id}.json"
    
    def create_session(
        self,
        session_id: str,
        user_id: str,
        app_name: str = "orchestrator",
        title: str = ""
    ) -> SessionData:
        """Create a new session."""
        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            app_name=app_name,
            title=title
        )
        self._cache[session_id] = session
        self.save_session(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get a session by ID."""
        # Check cache first
        if session_id in self._cache:
            return self._cache[session_id]
        
        # Try to load from disk
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                session = SessionData.from_dict(data)
                self._cache[session_id] = session
                return session
            except Exception as e:
                print(f"Error loading session {session_id}: {e}")
                return None
        return None
    
    def save_session(self, session: SessionData) -> None:
        """Save a session to disk."""
        session_file = self._get_session_file(session.session_id)
        try:
            with open(session_file, "w") as f:
                json.dump(session.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving session {session.session_id}: {e}")
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: str = "default_user"
    ) -> Optional[SessionData]:
        """Add a message to a session, creating it if necessary."""
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id, user_id)
        
        session.add_message(role, content)
        self.save_session(session)
        return session
    
    def list_sessions(self, user_id: Optional[str] = None) -> list[SessionData]:
        """List all sessions, optionally filtered by user."""
        sessions = []
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                session = SessionData.from_dict(data)
                
                if user_id is None or session.user_id == user_id:
                    sessions.append(session)
            except Exception as e:
                print(f"Error loading session from {session_file}: {e}")
        
        # Sort by updated_at descending (most recent first)
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        # Remove from cache
        if session_id in self._cache:
            del self._cache[session_id]
        
        # Remove from disk
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            try:
                session_file.unlink()
                return True
            except Exception as e:
                print(f"Error deleting session {session_id}: {e}")
                return False
        return False
    
    def get_session_summary(self, session_id: str) -> Optional[dict]:
        """Get a summary of a session (without full message content)."""
        session = self.get_session(session_id)
        if session is None:
            return None
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": len(session.messages)
        }


# Global session store instance
session_store = PersistentSessionStore()