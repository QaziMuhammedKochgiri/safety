"""
Base Claude API Client
Handles all communication with Anthropic's Claude API.
"""

import os
import anthropic
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClaudeConfig:
    """Configuration for Claude API."""
    api_key: str
    model: str = "claude-3-haiku-20240307"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60


class ClaudeClient:
    """
    Centralized Claude API client.
    Handles rate limiting, error handling, and logging.
    """

    def __init__(self, config: Optional[ClaudeConfig] = None):
        """Initialize Claude client with config."""
        if config is None:
            config = ClaudeConfig(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307"),
                max_tokens=int(os.getenv("CLAUDE_MAX_TOKENS", 4096))
            )

        if not config.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)

        logger.info(f"Claude client initialized with model: {config.model}")

    async def send_message(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Claude and get response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Dict with response content, usage stats, etc.
        """
        try:
            kwargs = {
                "model": self.config.model,
                "max_tokens": max_tokens or self.config.max_tokens,
                "temperature": temperature or self.config.temperature,
                "messages": messages
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            # Log request (without sensitive data)
            logger.info(f"Claude API request: {len(messages)} messages, {kwargs['max_tokens']} max tokens")

            # Make API call
            response = self.client.messages.create(**kwargs)

            # Extract response
            result = {
                "content": response.content[0].text,
                "model": response.model,
                "stop_reason": response.stop_reason,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "timestamp": datetime.now().isoformat()
            }

            # Log response
            logger.info(
                f"Claude API response: {result['usage']['input_tokens']} input tokens, "
                f"{result['usage']['output_tokens']} output tokens"
            )

            return result

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Claude client: {e}")
            raise

    async def simple_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Simplified interface for single prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system context
            **kwargs: Additional parameters

        Returns:
            Claude's response as string
        """
        messages = [{"role": "user", "content": prompt}]
        response = await self.send_message(
            messages=messages,
            system_prompt=system_prompt,
            **kwargs
        )
        return response["content"]

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Multi-turn chat interface.

        Args:
            messages: Conversation history
            system_prompt: System context

        Returns:
            Claude's response
        """
        response = await self.send_message(
            messages=messages,
            system_prompt=system_prompt
        )
        return response["content"]

    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters).

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return len(text) // 4

    async def health_check(self) -> bool:
        """
        Check if Claude API is accessible.

        Returns:
            True if API is healthy
        """
        try:
            await self.simple_prompt(
                "Hello",
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
