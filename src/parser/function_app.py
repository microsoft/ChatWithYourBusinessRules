import json, hashlib, logging, os
import azure.functions as func
import azure.durable_functions as df

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.data import get_conn
import utils.constants as constants

os.environ["OPEN_API_VERSION"] = os.environ["AZURE_OPENAI_API_VERSION"]
app = df.DFApp()

@app.sql_trigger(arg_name="changes", table_name="productMapping", connection_string_setting="ReferenceDataConnectionString")
@app.durable_client_input(client_name="client")
async def process_changes(changes, client):
    instance_id = await client.start_new("process_changes_orchestrator", None, changes)

@app.orchestration_trigger(context_name="context")
def process_changes_orchestrator(context):
    changes = context.get_input()
    changes_obj = json.loads(changes)
    
    maps = yield context.call_activity("get_maps", "get_maps_input")
    for change in changes_obj:
        if ((change["Operation"] == constants.SQL_INSERT) or (change["Operation"] == constants.SQL_UPDATE)):
            enriched_changes = yield context.call_activity("enrich_changes", { "Map1": maps[0], "Map2": maps[1], "Map3": maps[2], "Item": change["Item"] })
            translated_changes = yield context.call_activity("translate_changes", enriched_changes)
            result = yield context.call_activity("process_upsert", translated_changes)
        elif (change["Operation"] == constants.SQL_DELETE):
            result = yield context.call_activity("process_delete", change["Item"]["id"])
        else:
            logging.warning("process_changes_orchestrator received an unsupported change type")

@app.activity_trigger(input_name="item")
@app.sql_input(arg_name="map1", command_text=constants.GET_MAPS_TYPE_1_COMMAND_TEXT, command_type="Text", connection_string_setting="ReferenceDataConnectionString")
@app.sql_input(arg_name="map2", command_text=constants.GET_MAPS_TYPE_2_COMMAND_TEXT, command_type="Text", connection_string_setting="ReferenceDataConnectionString")
@app.sql_input(arg_name="map3", command_text=constants.GET_MAPS_TYPE_3_COMMAND_TEXT, command_type="Text", connection_string_setting="ReferenceDataConnectionString")
def get_maps(item, map1, map2, map3):

    map1_rows = list(map(lambda r: json.loads(r.to_json()), map1))
    for row in map1_rows:
        hash = hashlib.sha1(str(row["Code"]).encode('utf-8')).hexdigest()
        row["Hash"] = ''.join(char + '#' for char in hash)

    map2_rows = list(map(lambda r: json.loads(r.to_json()), map2))
    for row in map2_rows:
        hash = hashlib.sha1(str(row["Code"]).encode('utf-8')).hexdigest()
        row["Hash"] = ''.join(char + '#' for char in hash)

    map3_rows = list(map(lambda r: json.loads(r.to_json()), map3))
    for row in map3_rows:
        hash = hashlib.sha1(str(row["Code"]).encode('utf-8')).hexdigest()
        row["Hash"] = ''.join(char + '#' for char in hash)

    return [map1_rows, map2_rows, map3_rows]

@app.activity_trigger(input_name="params")
def enrich_changes(params: dict):   
    
    item = params["Item"]       
    expression = item["value"]

    map1 = params["Map1"]
    map2 = params["Map2"]
    map3 = params["Map3"]

    map1_matches = []
    for val in map1:
        if val["Code"] in expression:
            map1_matches.append({
                "Code": val["Code"],
                "Short_Descr": val["Short_Descr"],
                "Long_Descr": val["Long_Descr"]
            })
            expression = expression.replace(val["Code"], val["Hash"])
    
    map2_matches = []
    for val in map2:
        if val["Code"] in expression:
            map2_matches.append({
                "Code": val["Code"],
                "Short_Descr": val["Short_Descr"],
                "Long_Descr": val["Long_Descr"]
            })
            expression = expression.replace(val["Code"], val["Hash"])

    map3_matches = []
    for val in map3:
        if val["Code"] in expression:
            map3_matches.append({
                "Code": val["Code"],
                "Short_Descr": val["Short_Descr"],
                "Long_Descr": val["Long_Descr"]
            })
            expression = expression.replace(val["Code"], val["Hash"])

    for val in map1:
        expression = expression.replace(val["Hash"], "\"" + val["Long_Descr"] + "\"" if val["Long_Descr"] else "\"" + val["Short_Descr"] + "\"")

    for val in map2:
        expresison = expression.replace(val["Hash"], "\"" + val["Long_Descr"] + "\"" if val["Long_Descr"] else "\"" + val["Short_Descr"] + "\"")

    for val in map3:
        expression = expression.replace(val["Hash"], "\"" + val["Long_Descr"] + "\"" if val["Long_Descr"] else "\"" + val["Short_Descr"] + "\"")

    item["cat1_codes"] = json.dumps(map1_matches)
    item["cat2_codes"] = json.dumps(map2_matches)
    item["cat3_codes"] = json.dumps(map3_matches)
    item["enhanced_value"] = expression

    return item

@app.activity_trigger(input_name="params")
def translate_changes(params: dict):
    model = AzureChatOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        temperature=0.5,
        max_tokens = 2048
    )

    prompt = PromptTemplate(
        input_variables=["cat1_codes", "cat2_codes", "cat3_codes", "expression"],
        template = constants.TRANSLATE_TEMPLATE
    )
    
    parser = StrOutputParser()
    chain = prompt | model | parser
    translation = chain.invoke({
        "cat1_codes": params["cat1_codes"],
        "cat2_codes": params["cat2_codes"],
        "cat3_codes": params["cat3_codes"],
        "expression": params["enhanced_value"]
    })

    params["translated_value"] = translation
    return params

@app.activity_trigger(input_name="item")
@app.sql_output(arg_name="row", command_text="[dbo].[enhancedProductMapping]", connection_string_setting="ReferenceDataConnectionString")
def process_upsert(item, row: func.Out[func.SqlRow]):
    row.set(func.SqlRow.from_dict(item))

@app.activity_trigger(input_name="id")
@app.sql_input(arg_name="row", command_text=constants.PROCESS_DELETE_COMMAND_TEXT, command_type="Text", parameters="@id={id}", connection_string_setting="ReferenceDataConnectionString")
def process_delete(id, row: func.SqlRowList):
    pass