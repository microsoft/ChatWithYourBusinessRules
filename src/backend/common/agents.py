import json, requests

from typing import List, Optional, Type
import asyncio
import hashlib
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

import scenario_prompts as prompts
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
    code_type_tool = CodeTypeTool(run_manager=cb_manager)
    get_expression_meaning_tool = GetExpressionMeaningTool(run_manager=cb_manager)
    
    tools = [
        code_2_text_tool, # Core Tool
        text_2_code_tool, # Core Tool
        eligibility_tool, # Core Tool
        code_type_tool,
        get_expression_meaning_tool
    ]

    agent = create_openai_tools_agent(llm, tools, prompts.CUSTOM_CHATBOT_PROMPT)
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
    
class EligibilityToolInput(BaseModel):
    codes: list[str] = Field(description="A list of numeric customer attribute codes to check the offer eligibility for")

class EligibilityTool(BaseTool):
    name = "Eligibility"    
    args_schema: Type[BaseModel] = EligibilityToolInput
    description = prompts.ELIGIBILITY_TOOL_DESCRIPTION
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
    name = "Text2CodeTool"
    args_schema : Type[BaseModel] = SearchToolInput
    description = prompts.TEXT_2_CODE_TOOL_DESCRIPTION
    return_direct:bool = False    
 
    @trace
    def _run(self, question:str, run_manager:Optional[CallbackManagerForToolRun]=None) -> List[dict]:
       
        headers = {'Content-Type': 'application/json','api-key': AzureSearchConfig.SEARCH_KEY}
        params = {'api-version': AzureSearchConfig.API_VERSION}

        search_payload = {
            "search": question,
            "searchFields": "Short_Descr, Long_Descr",
            "select": "code, mapping_id, Short_Descr, Long_Descr",
            "queryType": "simple",
            "searchMode": "any",
            "top": 10   
        }

        search_url = f"{AzureSearchConfig.ENDPOINT}/indexes/ixcombofieldprodmap/docs/search"       
        result = []

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
                    if value["Short_Descr"].lower() == question.lower() or value["Long_Descr"].lower() == question.lower():
                        temp = [{
                            "code": value["code"],
                            "type": value["mapping_id"],
                            "short_descr": value["Short_Descr"],
                            "long_descr": value["Long_Descr"]
                        }]
                        break
                    else:
                        temp.append({
                            "code": value["code"],
                            "type": value["mapping_id"],
                            "short_descr": value["Short_Descr"],
                            "long_descr": value["Long_Descr"]
                        })
                result = temp

        except Exception:
            # log this
            pass

        return result

class Code2TextTool(BaseTool):
    name = "Code2TextTool"
    args_schema : Type[BaseModel] = SearchToolInput
    description = prompts.CODE_2_TEXT_TOOL_DESCRIPTION
    return_direct:bool = False    
    
    def _run(self, question:str, run_manager:Optional[CallbackManagerForToolRun]=None) -> List[dict]:
        headers = {'Content-Type': 'application/json','api-key': AzureSearchConfig.SEARCH_KEY}
        params = {'api-version': AzureSearchConfig.API_VERSION}
                
        search_payload = {
            "search": question,
            "searchFields": "code",
            "select": "code, mapping_id, Short_Descr, Long_Descr",
            "queryType": "simple",
            "searchMode": "all",
            "top": 5   
        }

        search_url = f"{AzureSearchConfig.ENDPOINT}/indexes/ixcombofieldprodmap/docs/search" 

        result = []
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
                    if value["code"] == question:
                        temp = [{
                            "code": value["code"],
                            "type": value["mapping_id"],
                            "short_descr": value['Short_Descr'],
                            "long_descr": value['Long_Descr']
                        }]
                        break
                    else:
                        temp.append({
                            "code": value["code"],
                            "type": value["mapping_id"],
                            "short_descr": value['Short_Descr'],
                            "long_descr": value['Long_Descr']
                        })
                               
                result = temp

        except Exception:
            # log this 
            pass

        return result

class CodeTypeTool(BaseTool):
    name = "CodeTypeTool"   
    args_schema : Type[BaseModel] = SearchToolInput
    description = prompts.CODE_TYPE_TOOL_DESCRPTION
    return_direct:bool = False    
 
    @trace
    def _run(self, question:str, run_manager:Optional[CallbackManagerForToolRun]=None) -> List[str]:
        headers = {'Content-Type': 'application/json','api-key': AzureSearchConfig.SEARCH_KEY}
        params = {'api-version': AzureSearchConfig.API_VERSION}
                
        search_payload = {
            "search": question,
            "searchFields": "code",
            "select": "mapping_id",
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
                    temp.append(value["mapping_id"])                    
                         
                result = temp

        except Exception:
            # log this 
            pass

        return result

class SearchToolInput(BaseModel):
    expressions: List[str] = Field(description="The expressions to search for")

class GetProductByExpresionSearchTool(BaseTool):
    name = "GetProductByExpresionSearchTool"
    args_schema : Type[BaseModel] = SearchToolInput
    description = prompts.GET_PRODUCT_BY_EXPRESSION_SEARCH_TOOL_DESCRIPTION
    return_direct:bool = False
    
    def _run(self, expressions: List[str], run_manager:Optional[CallbackManagerForToolRun]=None) -> List[dict]:
        headers = {'Content-Type': 'application/json','api-key': AzureSearchConfig.SEARCH_KEY}
        params = {'api-version': AzureSearchConfig.API_VERSION}
                
        search_payload = {
            "search": str(expressions),
            "searchFields": "expanded_value",
            "select": "id, name",
            "queryType": "simple",
            "searchMode": "any",
            "top": 5   
        }

        search_url = f"{AzureSearchConfig.ENDPOINT}/indexes/ixenhancedproductmapping/docs/search" 

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
                        "code": value["id"],
                        "name": value["name"]
                    })                                    
                result = temp

        except Exception:
            # log this 
            pass

        return result

class GetExpressionMeaningToolInput(BaseModel):
    expression: str = Field(description="The expression to search for")

class GetExpressionMeaningTool(BaseTool):
    name = "GetExpressonMeaningTool"
    args_schema : Type[BaseModel] = GetExpressionMeaningToolInput
    description = "Returns the meaning of boolean expressions comprised of numerical operands and logical operators"
    return_direct:bool = False

    def _run(self, expression: str, run_manager:Optional[CallbackManagerForToolRun]=None) -> str:
        result = expression

        try:
            values = []
            skip = 0

            while True:
                results = self.__get_search_results__(skip)
                subset = results["value"]
                values.extend(subset)

                if len(subset) < 50:
                    break

                skip += 50

            for item in values:
                item["hash"] = self.__get_hash__(item["code"])

            affiliates = sorted([item for item in values if item["mapping_id"] == "affiliate"], key=lambda x: len(x), reverse=True)
            lobs = sorted([item for item in values if item["mapping_id"] == "lob"], key=lambda x: len(x), reverse=True)
            customfields = sorted([item for item in values if item["mapping_id"] == "customfield"], key=lambda x: len(x), reverse=True)

            for item in affiliates:
                result = result.replace(item["code"], item["hash"])

            for item in lobs:
                result = result.replace(item["code"], item["hash"])

            for item in customfields:
                result = result.replace(item["code"], item["hash"])

            for item in affiliates:
                result = result.replace(item["hash"], f"[{item['Long_Descr']}]")

            for item in lobs:
                result = result.replace(item["hash"], f"[{item['Long_Descr']}]")

            for item in customfields:
                result = result.replace(item["hash"], f"[{item['Long_Descr']}]")   

        except Exception:
            pass

        return result
    
    def __get_search_results__(self, skip):
        headers = {'Content-Type': 'application/json','api-key': AzureSearchConfig.SEARCH_KEY}
        params = {'api-version': AzureSearchConfig.API_VERSION}
                
        search_payload = {
            "search": "*",
            "select": "code, mapping_id, Short_Descr, Long_Descr",
            "queryType": "simple", 
            "top": 50,
            "skip": skip
        } 

        search_url = f"{AzureSearchConfig.ENDPOINT}/indexes/ixcombofieldprodmap/docs/search"
        response = requests.post(search_url,
            data=json.dumps(search_payload),
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

    def __get_hash__(self, input_string):
        sha1_hash = hashlib.sha1()
        sha1_hash.update(input_string.encode('utf-8'))
        hex_digest = sha1_hash.hexdigest()
        return '#'.join(hex_digest[i:i+2] for i in range(0, len(hex_digest), 2))

### Testing ###
if (__name__ == "__main__"):
    import uuid
    from callbacks import StdOutCallbackHandler

    start_trace()
    instrumentor = LangchainInstrumentor()
    if not instrumentor.is_instrumented_by_opentelemetry:
        instrumentor.instrument()

    question = None
    #user_id = "1234"
    #session_id = "5678"
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    cb_handler = StdOutCallbackHandler()

    while(question != "quit"):
        question = input("\n\nEnter a question (or \"quit\"): ")
        if (question == "quit"):
            break
        answer = asyncio.run(send_request_to_agent_async(question, user_id, session_id, cb_handler))
        ## No need to print, the handler does that
