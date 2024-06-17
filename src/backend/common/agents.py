import json, requests

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

from opentelemetry.instrumentation.langchain import LangchainInstrumentor
from promptflow.tracing import trace, start_trace
from promptflow.core import tool

from prompts import CUSTOM_CHATBOT_PROMPT
from session_history import get_session_history
from config import AzureOpenAIConfig, AzureSearchConfig, EligibilityEndpointConfig

@trace
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

    code_2_text_tool = Code2TextTool(run_manager=cb_manager)
    text_2_code_tool = Text2CodeTool(run_manager=cb_manager)
    eligibility_tool = EligibilityTool(run_manager=cb_manager)
    
    tools = [code_2_text_tool, text_2_code_tool, eligibility_tool]

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
    
    @trace
    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return text
    
class EligibilityToolInput(BaseModel):
    codes: list[str] = Field(description="A list of numeric customer attribute codes to check the offer eligibility for")

class EligibilityTool(BaseTool):
    name = "Eligibility"
    description = "Given a list of numeric attribute codes for a single customer, checks the eligibility of that customer for a special offer"
    args_schema: Type[BaseModel] = EligibilityToolInput
    return_direct: bool = False
    
    @trace
    def _run(self, codes: list[str], run_manager: Optional[CallbackManagerForToolRun] = None) -> dict:
        eligibility = requests.post(url=EligibilityEndpointConfig.ENDPOINT, 
                      headers={"x-functions-key": EligibilityEndpointConfig.FUNCTION_KEY}, 
                      json=codes)
        eligibility.raise_for_status()
        return eligibility.json()
    
class SearchToolInput(BaseModel):
    question: str = Field(description="The question to search for")    

class Text2CodeTool(BaseTool):
    name = "text2code"
    description = "Translates text phrases to numeric codes"
    args_schema : Type[BaseModel] = SearchToolInput
    return_direct:bool = False    
 
    @trace
    def _run(self, question:str, run_manager:Optional[CallbackManagerForToolRun]=None) -> str:
       
        headers = {'Content-Type': 'application/json','api-key': AzureSearchConfig.SEARCH_KEY}
        params = {'api-version': AzureSearchConfig.API_VERSION}
                
        search_payload = {
            "search": question,
            "searchFields": "Short_Descr, Long_Descr",
            "select": "code",
            "queryType": "simple",
            "searchMode": "any",
            "top": 5   
        }

        search_url = f"{AzureSearchConfig.ENDPOINT}/indexes/ixcombofieldprodmap/docs/search"       
        result = "Not found"

        try:
            response = requests.post(search_url,
                data=json.dumps(search_payload),
                headers=headers,
                params=params
            )

            response_obj = response.json()
            values = response_obj['value']
            if values:
                
                temp = []
                for value in values:
                    temp.append(value['code'])
                
                result = json.dumps(temp)

        except Exception:
            # log this 
            pass

        return result

class Code2TextTool(BaseTool):
    name = "code2text"
    description = "Translates numeric codes into text phrases"
    args_schema : Type[BaseModel] = SearchToolInput
    return_direct:bool = False    
 
    @trace
    def _run(self, question:str, run_manager:Optional[CallbackManagerForToolRun]=None) -> str:

        headers = {'Content-Type': 'application/json','api-key': AzureSearchConfig.SEARCH_KEY}
        params = {'api-version': AzureSearchConfig.API_VERSION}
                
        search_payload = {
            "search": question,
            "searchFields": "code",
            "select": "Short_Descr, Long_Descr",
            "queryType": "simple",
            "searchMode": "any",
            "top": 5   
        }

        search_url = f"{AzureSearchConfig.ENDPOINT}/indexes/ixcombofieldprodmap/docs/search" 

        result = "Not found"
        try:
            response = requests.post(search_url,
                data=json.dumps(search_payload),
                headers=headers,
                params=params
            )

            response_obj = response.json()
            values = response_obj['value']
            if values:
                
                temp = []
                for value in values:
                    temp.append({
                        "Short_Descr": value['Short_Descr'],
                        "Long_Descr": value['Long_Descr']
                    })                    
                
                result = json.dumps(temp)

        except Exception:
            # log this 
            pass

        return result


### Testing ###
if (__name__ == "__main__"):
    from callbacks import StdOutCallbackHandler

    start_trace()
    instrumentor = LangchainInstrumentor()
    if not instrumentor.is_instrumented_by_opentelemetry:
        instrumentor.instrument()

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
