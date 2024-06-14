from typing import Type, Optional
import asyncio
import requests

from langchain_openai import AzureChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.runnables import ConfigurableFieldSpec
from langchain.agents import AgentExecutor
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from langchain.callbacks.manager import CallbackManagerForToolRun

from prompts import CUSTOM_CHATBOT_PROMPT
from session_history import get_session_history
from config import AzureOpenAIConfig, EligibilityEndpointConfig

async def send_request_to_agent_async(question: str, user_id: str, session_id: str, cb_handler: BaseCallbackHandler):
    cb_manager = CallbackManager(handlers=[cb_handler])

    # Set LLM 
    llm = AzureChatOpenAI(
        azure_endpoint=AzureOpenAIConfig.ENDPOINT,
        deployment_name=AzureOpenAIConfig.MODEL_NAME, 
        temperature=0, 
        max_tokens=1500, 
        callback_manager=cb_manager,
        api_version=AzureOpenAIConfig.API_VERSION, 
        streaming=True)

    # Initialize our Tools/Experts

    eligibility_tool = EligibilityTool()
    tools = [eligibility_tool]

    agent = create_openai_tools_agent(llm, tools, CUSTOM_CHATBOT_PROMPT)
    agent_executor = AgentExecutor(agent=agent, tools=tools)
    brain_agent_executor = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history",
        history_factory_config=[
            ConfigurableFieldSpec(
                id="user_id",
                annotation=str,
                name="User ID",
                description="Unique identifier for the user.",
                default="",
                is_shared=True,
            ),
            ConfigurableFieldSpec(
                id="session_id",
                annotation=str,
                name="Session ID",
                description="Unique identifier for the conversation.",
                default="",
                is_shared=True,
            ),
        ],
    )

    config={"configurable": {"session_id": session_id, "user_id": user_id}}


    answer = brain_agent_executor.invoke({"question": question}, config=config)["output"]
    return answer

#####################################################################################################
############################### AGENTS AND TOOL CLASSES #############################################
#####################################################################################################

class EchoToolInput(BaseModel):
    text: str = Field(description="The text to echo back")

class EchoTool(BaseTool):
    name = "Echo"
    description = "Echoes back the input text"
    args_schema: Type[BaseModel] = EchoToolInput
    return_direct: bool = False
    
    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return text
    
class EligibilityToolInput(BaseModel):
    codes: list[str] = Field(description="A list of numeric customer attribute codes to check the offer eligibility for")

class EligibilityTool(BaseTool):
    name = "Eligibility"
    description = "Given a list of numeric attribute codes for a single customer, checks the eligibility of that customer for a special offer"
    args_schema: Type[BaseModel] = EligibilityToolInput
    return_direct: bool = False
    
    def _run(self, codes: list[str], run_manager: Optional[CallbackManagerForToolRun] = None) -> dict:
        eligibility = requests.post(url=EligibilityEndpointConfig.ENDPOINT, 
                      headers={"x-functions-key": EligibilityEndpointConfig.FUNCTION_KEY}, 
                      json=codes)
        eligibility.raise_for_status()
        return eligibility.json()

### Testing ###
if (__name__ == "__main__"):
    from callbacks import StdOutCallbackHandler

    question = None
    user_id = "1234"
    session_id = "5678"
    cb_handler = StdOutCallbackHandler()

    while(question != "quit"):
        question = input("\n\nEnter a question (or \"quit\"): ")
        if (question == "quit"):
            break
        answer = asyncio.run(send_request_to_agent_async(question, user_id, session_id, cb_handler))
        ## No need to print, the handler does that
