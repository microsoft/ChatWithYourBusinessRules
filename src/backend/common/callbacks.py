import sys
from typing import Any, Dict, List, Optional, Union
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult

from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ActivityTypes

# Callback handler to use in notebooks, uses stdout
class StdOutCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming in agents.
    Only works with agents using LLMs that support streaming.
    """
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        sys.stdout.write(token)
        sys.stdout.flush()

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        """Run when LLM errors."""
        sys.stdout.write(f"LLM Error: {error}\n")

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        sys.stdout.write(f"Tool: {serialized['name']}\n")
        
    def on_retriever_start(self, serialized: Dict[str, Any], query: str) -> Any:
        sys.stdout.write(f"Retriever: {serialized}\n")
        
    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        sys.stdout.write(f"Agent Action: {action.log}\n")

# Callback hanlder used for the bot service to inform the client of the thought process before the final response
class BotServiceCallbackHandler(BaseCallbackHandler):
    """Callback handler to use in Bot Builder Application"""
    
    def __init__(self, turn_context: TurnContext) -> None:
        self.tc = turn_context

    async def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        await self.tc.send_activity(f"LLM Error: {error}\n")

    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        await self.tc.send_activity(f"Tool: {serialized['name']}")

    async def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        await self.tc.send_activity(f"\u2611{action.log} ...")
        await self.tc.send_activity(Activity(type=ActivityTypes.typing))
