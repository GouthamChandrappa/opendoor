# door_installation_assistant/agent_system/memory/conversation_memory.py
import logging
from typing import Dict, List, Any, Optional
import time

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Manages conversation memory across sessions."""
    
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.sessions = {}  # Map of session_id to message list
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to the conversation memory.
        
        Args:
            session_id: Session identifier.
            role: Message role (system, user, assistant).
            content: Message content.
        """
        # Create session if it doesn't exist
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        # Add timestamp to message
        timestamp = time.time()
        
        # Add message to session
        self.sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": timestamp
        })
        
        # Trim session if it exceeds max_messages
        if len(self.sessions[session_id]) > self.max_messages:
            # Remove oldest message(s)
            excess = len(self.sessions[session_id]) - self.max_messages
            self.sessions[session_id] = self.sessions[session_id][excess:]
    
    def add_user_message(self, session_id: str, content: str) -> None:
        """
        Add a user message to the conversation memory.
        
        Args:
            session_id: Session identifier.
            content: Message content.
        """
        self.add_message(session_id, "user", content)
    
    def add_assistant_message(self, session_id: str, content: str) -> None:
        """
        Add an assistant message to the conversation memory.
        
        Args:
            session_id: Session identifier.
            content: Message content.
        """
        self.add_message(session_id, "assistant", content)
    
    def add_system_message(self, session_id: str, content: str) -> None:
        """
        Add a system message to the conversation memory.
        
        Args:
            session_id: Session identifier.
            content: Message content.
        """
        self.add_message(session_id, "system", content)
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get messages for a session.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            List of messages in the session.
        """
        return self.sessions.get(session_id, [])
    
    def get_last_n_messages(self, session_id: str, n: int) -> List[Dict[str, Any]]:
        """
        Get the last n messages for a session.
        
        Args:
            session_id: Session identifier.
            n: Number of messages to get.
            
        Returns:
            List of the last n messages in the session.
        """
        messages = self.get_messages(session_id)
        return messages[-n:] if n < len(messages) else messages
    
    def clear_messages(self, session_id: str) -> None:
        """
        Clear messages for a session.
        
        Args:
            session_id: Session identifier.
        """
        if session_id in self.sessions:
            self.sessions[session_id] = []
    
    def get_sessions(self) -> List[str]:
        """
        Get all session IDs.
        
        Returns:
            List of session IDs.
        """
        return list(self.sessions.keys())
    
    def get_formatted_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get formatted message history for LLM consumption.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            List of messages formatted for LLM (without timestamps).
        """
        messages = self.get_messages(session_id)
        
        # Format messages for LLM (remove timestamps)
        formatted_messages = []
        for message in messages:
            formatted_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        return formatted_messages
    
    def get_formatted_history_with_context(self, session_id: str, context: str) -> List[Dict[str, str]]:
        """
        Get formatted message history with context for LLM consumption.
        
        Args:
            session_id: Session identifier.
            context: Context to add to the system message.
            
        Returns:
            List of messages with context formatted for LLM.
        """
        formatted_messages = self.get_formatted_history(session_id)
        
        # Check if there's a system message
        has_system = any(msg["role"] == "system" for msg in formatted_messages)
        
        if has_system:
            # Update existing system message
            for i, msg in enumerate(formatted_messages):
                if msg["role"] == "system":
                    formatted_messages[i]["content"] = f"{msg['content']}\n\nContext: {context}"
                    break
        else:
            # Add new system message with context
            formatted_messages.insert(0, {
                "role": "system",
                "content": f"You are an AI assistant helping with door installation. Context: {context}"
            })
        
        return formatted_messages