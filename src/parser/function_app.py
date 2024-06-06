import json, logging
import azure.functions as func

import utils.constants as constants

app = func.FunctionApp()

@app.function_name(name="ProcessChanges")
@app.sql_trigger(
    arg_name="changes",
    table_name="productMapping",
    connection_string_setting="ReferenceDataConnectionString"
)
@app.sql_output(
    arg_name="enhancements",
    command_text="enhancedProductMapping",
    connection_string_setting="ReferenceDataConnectionString"
)
def process_changes(changes: str, enhancements: func.Out[func.SqlRowList]):
    changes_obj = json.loads(changes)
    data = [func.SqlRow.from_dict(change["Item"]) for change in changes_obj if change["Operation"] != constants.SQL_DELETE]
    enhancements.set(data)

    # data_to_upsert = [
    #     func.SqlRow.from_dict(
    #         {
    #             "name": "offer",
    #             "id": 1,
    #             "state": "active",
    #             "value": "offer x"
    #         }),
    #     func.SqlRow.from_dict(
    #         {
    #             "name": "offer",
    #             "id": 2,
    #             "state": "active",
    #             "value": "offer"
    #         }
    #     )
    # ]
