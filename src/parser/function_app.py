import datetime, json, hashlib, logging, os
import azure.functions as func
import azure.durable_functions as df

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.rule import Rule
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
    
    retry_options = df.RetryOptions(
        first_retry_interval=datetime.timedelta(seconds=5), 
        max_number_of_attempts=5,
        backoff_coefficient=2)
    
    maps = yield context.call_activity_with_retry("get_maps", retry_options, "get_maps_input")

    for change in changes_obj:
        if ((change["Operation"] == constants.SQL_INSERT) or (change["Operation"] == constants.SQL_UPDATE)):
            enriched_changes = yield context.call_activity("enrich_changes", { "Map1": maps[0], "Map2": maps[1], "Map3": maps[2], "Item": change["Item"] })
            translated_changes = yield context.call_activity_with_retry("translate_changes", retry_options, enriched_changes)
            yield context.call_activity_with_retry("process_upsert", retry_options, translated_changes)

            yield context.call_activity_with_retry("clean_rules_data", retry_options, change["Item"]["id"]) # clean rules database
            yield context.call_activity_with_retry("process_workflow", retry_options, "Eligibility") # make sure we have a default workflow in place
            yield context.call_activity_with_retry("process_rules", retry_options, change["Item"]) # convert expression into a database compatible structure and insert into database
        elif (change["Operation"] == constants.SQL_DELETE):
            yield context.call_activity_with_retry("process_delete", retry_options, change["Item"]["id"])
            yield context.call_activity_with_retry("clean_rules_data", retry_options, change["Item"]["id"]) 
        else:
            logging.warning("process_changes_orchestrator received an unsupported change type")

@app.activity_trigger(input_name="param")
@app.sql_input(arg_name="map1", command_text=constants.GET_MAPS_TYPE_1_COMMAND_TEXT, command_type="Text", connection_string_setting="ReferenceDataConnectionString")
@app.sql_input(arg_name="map2", command_text=constants.GET_MAPS_TYPE_2_COMMAND_TEXT, command_type="Text", connection_string_setting="ReferenceDataConnectionString")
@app.sql_input(arg_name="map3", command_text=constants.GET_MAPS_TYPE_3_COMMAND_TEXT, command_type="Text", connection_string_setting="ReferenceDataConnectionString")
def get_maps(param, map1, map2, map3):
    """
    Retrieve the three mapping tables from the database

    Parameters:
    param: a dummy parameter to trigger the activity

    Returns:
    A list of three lists, each containing the rows of a mapping table
    """
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
    """
    Encrich a product mapping value by replacing codes with their descriptions.
    Include lists of codes that were replaced in the output.

    Parameters:
    params: a dictionary containing the item to enrich and the maps to use for replacement

    Returns:
    The item with the enhaced value and lists of codes that were replaced in the output
    """ 
    
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
    """
    Convert the input item into plain english using the Azure OpenAI model

    Parameters:
    params: a dictionary containing the item to translate

    Returns:
    The params dictionay with a new key, "translated_value", containing the translated value
    """
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
    """
    Insert/update the specified item in the enhancedProductMapping table

    Parameters:
    item: the item to insert/update; a dictionary that must conform to the enhacedProductMapping table schema
    row: the item to insert/update

    """
    row.set(func.SqlRow.from_dict(item))

@app.activity_trigger(input_name="id")
@app.sql_input(arg_name="row", command_text=constants.PROCESS_DELETE_COMMAND_TEXT, command_type="Text", parameters="@id={id}", connection_string_setting="ReferenceDataConnectionString")
def process_delete(id, row: func.SqlRowList): 
    """
    delete the specified item from the enahcedProductMapping table

    Parameters:
    id: the id of the item to delete
    row: the item(s) to delete

    Returns:
    Nothing

    Commment:
    This method uses a SQL input binding to execute a DELETE statement against the enhancedProductMapping table.
    """   
    pass

@app.activity_trigger(input_name="name")
@app.sql_output(arg_name="row", command_text="[dbo].[Workflows]", connection_string_setting="RulesDataConnectionString")
def process_workflow(name, row: func.Out[func.SqlRowList]):
    """
    Upsert a new workflow into the database - rules have to be associated with a workflow
    """
    row.set(func.SqlRow.from_dict({
        "WorkflowName": name,
        "RuleExpressionType": 0
    }))

@app.activity_trigger(input_name="ruleName")
@app.sql_input(arg_name="row", command_text=constants.CLEAN_RULES_DATA_COMMAND_TEXT, command_type="Text", parameters="@RuleName={ruleName}", connection_string_setting="RulesDataConnectionString")
def clean_rules_data(ruleName, row: func.SqlRowList):
    """
    Delete all rules that reference the specified root rule name.
    Use this in order to clean the rules table before inserting new rules.
    """
    pass

@app.activity_trigger(input_name="params")
@app.sql_output(arg_name="rows", command_text="[dbo].[rules]", connection_string_setting="RulesDataConnectionString")
def process_rules(params, rows: func.Out[func.SqlRowList]):
    """
    Convert expressions into a rules engine compatible data structure and store in database
    """
    rule = Rule.parse_expression(params["value"])
    rule.name = params["id"]
    table = rule.get_table("Eligibility")
    rows.set(func.SqlRowList(table))