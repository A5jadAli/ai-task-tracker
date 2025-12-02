"""
Slack integration for monitoring messages and sending responses.
Supports both bot mode and user mode (personal account).
"""
import os
import re
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
    """Monitor Slack for events and messages.
    
    Supports two modes:
    - Bot mode: Uses bot token, monitors bot mentions
    - User mode: Uses user token, monitors user mentions (personal account)
    """
    
    def __init__(self):
        super().__init__("SlackMonitor")
        self.web_client = None
        self.socket_client = None
        self.thread = None
        self.mode = "bot"  # "bot" or "user"
        self.user_id = None  # For user mode
    
    def start(self, config: Dict[str, Any]):
        """
        Start Slack monitoring.
        
        Args:
            config: Slack configuration with tokens and mode
                For bot mode: 'token' (bot token) and 'app_token'
                For user mode: 'user_token' and 'user_id'
        """
        if self.running:
            logger.warning("Slack monitor already running")
            return
        
        self.config = config
        self.mode = config.get('mode', 'bot')  # Default to bot mode for backward compatibility
        
        # Determine which tokens to use based on mode
        if self.mode == 'user':
            bot_token = config.get('user_token') or os.getenv('SLACK_USER_TOKEN')
            app_token = config.get('app_token') or os.getenv('SLACK_APP_TOKEN')
            self.user_id = config.get('user_id') or os.getenv('SLACK_USER_ID')
            
            if not self.user_id:
                logger.warning("User ID not provided, will attempt to fetch from API")
        else:
            # Bot mode (legacy)
            bot_token = config.get('token') or os.getenv('SLACK_BOT_TOKEN')
            app_token = config.get('app_token') or os.getenv('SLACK_APP_TOKEN')
        
        if not bot_token or not app_token:
            logger.error(f"Slack tokens not configured for {self.mode} mode")
            return
        
        try:
            # Initialize clients
            self.web_client = WebClient(token=bot_token)
            
            # Get user ID if in user mode and not provided
            if self.mode == 'user' and not self.user_id:
                self.user_id = self._get_authenticated_user_id()
                if not self.user_id:
                    logger.error("Failed to get user ID for user mode")
                    return
                logger.info(f"Authenticated as user: {self.user_id}")
            
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
            
            logger.info(f"Slack monitor started in {self.mode} mode")
        
        except Exception as e:
            logger.error(f"Failed to start Slack monitor: {e}", exc_info=True)
            self.running = False
    
    def _get_authenticated_user_id(self) -> str:
        """Get the authenticated user's ID from Slack API.
        
        Returns:
            User ID or None if failed
        """
        try:
            response = self.web_client.auth_test()
            return response.get('user_id')
        except Exception as e:
            logger.error(f"Failed to get user ID: {e}", exc_info=True)
            return None
    
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
                    # Bot mention (legacy)
                    self._handle_mention(event)
                elif event_type == "message":
                    self._handle_message(event)
                
                # Trigger generic event callback
                self.trigger_callbacks("slack_event", event)
        
        except Exception as e:
            logger.error(f"Error handling Slack event: {e}", exc_info=True)
    
    def _handle_mention(self, event: Dict):
        """Handle app mention events (bot mode)."""
        logger.info(f"Bot mentioned in channel {event.get('channel')}")
        self.trigger_callbacks("mention", event)
    
    def _is_user_mentioned(self, text: str) -> bool:
        """Check if the authenticated user is mentioned in the text.
        
        Args:
            text: Message text
            
        Returns:
            True if user is mentioned
        """
        if not self.user_id:
            return False
        
        # Slack mentions format: <@USER_ID>
        mention_pattern = f"<@{self.user_id}>"
        return mention_pattern in text
    
    def _handle_message(self, event: Dict):
        """Handle message events.
        
        In user mode: Check for user mentions
        In bot mode: Check for keywords only
        """
        # Skip bot messages (unless it's our own user in user mode)
        if event.get("bot_id") and self.mode != 'user':
            return
        
        # Skip messages from self in user mode
        if self.mode == 'user' and event.get('user') == self.user_id:
            return
        
        text = event.get("text", "")
        channel = event.get("channel")
        channel_type = event.get("channel_type", "")
        
        # Check for commands in command channel (if configured)
        command_channel = self.config.get('command_channel')
        if command_channel and channel == command_channel:
            # Check if this looks like a command
            command_prefix = self.config.get('command_prefix', 'agent')
            if text.strip().lower().startswith(command_prefix.lower()):
                logger.info(f"Command detected in channel {channel}")
                self.trigger_callbacks("command", event)
                return  # Don't process as regular message
        
        # Check for user mentions in user mode
        if self.mode == 'user' and self._is_user_mentioned(text):
            logger.info(f"User mentioned in {channel_type} {channel}")
            self.trigger_callbacks("user_mention", event)
            # Also trigger generic mention for backward compatibility
            self.trigger_callbacks("mention", event)
        
        # Check for DMs in user mode
        if self.mode == 'user' and channel_type == "im":
            monitor_dms = self.config.get('monitor_dms', True)
            if monitor_dms:
                logger.info(f"DM received from user {event.get('user')}")
                self.trigger_callbacks("dm_received", event)
        
        # Check for keywords (both modes)
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
        
        In user mode: Sends as the authenticated user
        In bot mode: Sends as the bot
        
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
            mode_desc = "user" if self.mode == 'user' else "bot"
            logger.info(f"Sent message as {mode_desc} to {channel}")
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
    
    def send_dm(self, user_id: str, text: str):
        """
        Send a direct message to a user.
        
        Args:
            user_id: User ID to send DM to
            text: Message text
            
        Returns:
            Response from Slack API
        """
        if not self.web_client:
            logger.error("Slack client not initialized")
            return None
        
        try:
            # Open DM channel
            response = self.web_client.conversations_open(users=[user_id])
            channel_id = response['channel']['id']
            
            # Send message
            return self.send_message(channel_id, text)
        except Exception as e:
            logger.error(f"Failed to send DM: {e}", exc_info=True)
            return None

