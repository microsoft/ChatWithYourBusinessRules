import azure.functions as func
import logging

# https://github.com/Azure/azure-functions-sql-extension/tree/main/samples/samples-python-v2
# https://github.com/Azure/azure-functions-python-worker/blob/dev/tests/endtoend/sql_functions/sql_functions_stein/function_app.py
# Learn more at https://aka.ms/pythonprogrammingmodel 

app = func.FunctionApp()
    
@app.function_name(name="ProcessChanges")
@app.sql_trigger(
    arg_name="changes",
    table_name="Table",
    connection_string_setting="SourceConnectionString"
)
@app.sql_output(
    arg_name="o",
    command_text="[dbo].[Table]",
    connection_string_setting="DestinationConnectionString"
)
@app.sql_output(
    arg_name="bo",
    command_text="[dbo].[Table]",
    connection_string_settings="BREConnectionString"
)
def process_changes(
    changes: str,
    o: func.Out[func.SqlRow],
    bo: func.Out[func.SqlRow]
) -> None:
    pass