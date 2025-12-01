"""
Slack integration for monitoring messages and sending responses.
"""
import os
import threading
from typing import Dict, Any, Callable
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from integrations.base_monitor import BaseMonitor
from utils.logger import get_logger

logger = get_logger(__name__)


class SlackMonitor(BaseMonitor):
    """Monitor Slack for events and messages."""
    
    def __init__(self):
        super().__init__("SlackMonitor")
        self.web_client = None
        self.socket_client = None
        self.thread = None
    
    def start(self, config: Dict[str, Any]):
        """
        Start Slack monitoring.
        
        Args:
            config: Slack configuration with 'token' and 'app_token'
        """
        if self.running:
            logger.warning("Slack monitor already running")
            return
        
        self.config = config
        bot_token = config.get('token') or os.getenv('SLACK_BOT_TOKEN')
        app_token = config.get('app_token') or os.getenv('SLACK_APP_TOKEN')
        
        if not bot_token or not app_token:
            logger.error("Slack tokens not configured")
            return
        
        try:
            # Initialize clients
            self.web_client = WebClient(token=bot_token)
            self.socket_client = SocketModeClient(
                app_token=app_token,
                web_client=self.web_client
            )
            
            # Register event handlers
            self.socket_client.socket_mode_request_listeners.append(self._handle_event)
            
            # Start in separate thread
            self.running = True
            self.thread = threading.Thread(target=self._run_socket_mode, daemon=True)
            self.thread.start()
            
            logger.info("Slack monitor started")
        
        except Exception as e:
            logger.error(f"Failed to start Slack monitor: {e}", exc_info=True)
            self.running = False
    
    def _run_socket_mode(self):
        """Run socket mode client."""
        try:
            self.socket_client.connect()
        except Exception as e:
            logger.error(f"Socket mode error: {e}", exc_info=True)
            self.running = False
    
    def stop(self):
        """Stop Slack monitoring."""
        if not self.running:
            return
        
        self.running = False
        
        if self.socket_client:
            try:
                self.socket_client.close()
            except:
                pass
        
        logger.info("Slack monitor stopped")
    
    def _handle_event(self, client: SocketModeClient, req: SocketModeRequest):
        """
        Handle incoming Slack events.
        
        Args:
            client: Socket mode client
            req: Socket mode request
        """
        try:
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)
            
            # Process event
            if req.type == "events_api":
                event = req.payload.get("event", {})
                event_type = event.get("type")
                
                if event_type == "app_mention":
                    self._handle_mention(event)
                elif event_type == "message":
                    self._handle_message(event)
                
                # Trigger generic event callback
                self.trigger_callbacks("slack_event", event)
        
        except Exception as e:
            logger.error(f"Error handling Slack event: {e}", exc_info=True)
    
    def _handle_mention(self, event: Dict):
        """Handle app mention events."""
        logger.info(f"Mentioned in channel {event.get('channel')}")
        self.trigger_callbacks("mention", event)
    
    def _handle_message(self, event: Dict):
        """Handle message events."""
        # Skip bot messages
        if event.get("bot_id"):
            return
        
        text = event.get("text", "")
        channel = event.get("channel")
        
        # Check for keywords
        keywords = self.config.get('keywords', [])
        for keyword in keywords:
            if keyword.lower() in text.lower():
                logger.info(f"Keyword '{keyword}' detected in {channel}")
                self.trigger_callbacks("keyword", {
                    "keyword": keyword,
                    "event": event
                })
    
    def send_message(self, channel: str, text: str, thread_ts: str = None):
        """
        Send message to Slack channel.
        
        Args:
            channel: Channel ID
            text: Message text
            thread_ts: Thread timestamp (for replies)
        
        Returns:
            Response from Slack API
        """
        if not self.web_client:
            logger.error("Slack client not initialized")
            return None
        
        try:
            response = self.web_client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts
            )
            logger.info(f"Sent message to {channel}")
            return response
        except Exception as e:
            logger.error(f"Failed to send message: {e}", exc_info=True)
            return None
    
    def reply_to_thread(self, channel: str, thread_ts: str, text: str):
        """
        Reply to a thread.
        
        Args:
            channel: Channel ID
            thread_ts: Thread timestamp
            text: Reply text
        """
        return self.send_message(channel, text, thread_ts=thread_ts)
