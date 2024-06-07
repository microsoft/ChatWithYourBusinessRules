SQL_INSERT = 0
SQL_UPDATE = 1
SQL_DELETE = 2

GET_MAPS_TYPE_1_COMMAND_TEXT = "SELECT [Code], [Mapping_ID], [Short_Descr], [Long_Descr] FROM [dbo].[fieldMapping] WHERE [Mapping_ID] LIKE 'Affiliate' ORDER BY LEN([Code]) DESC"
GET_MAPS_TYPE_2_COMMAND_TEXT = "SELECT [Code], [Mapping_ID], [Short_Descr], [Long_Descr] FROM [dbo].[fieldMapping] WHERE [Mapping_ID] LIKE 'LOB' ORDER BY LEN([Code]) DESC"
GET_MAPS_TYPE_3_COMMAND_TEXT = "SELECT [Code], [Mapping_ID], [Short_Descr], [Long_Descr] FROM [dbo].[fieldMapping] WHERE [Mapping_ID] LIKE 'CustomField' ORDER BY LEN([Code]) DESC"
PROCESS_DELETE_COMMAND_TEXT = "DELETE FROM [dbo].[enhancedProductMapping] WHERE [id] = @id"

TRANSLATE_TEMPLATE = """
You are an assistance for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know. 
Use three sentences maximum and keep the answer concise.

Context:

Affiliates:
{cat1_codes}

Line of Business:
{cat2_codes}

Attributes
{cat3_codes}

Question:
What does this mean, "{expression}"?

Helpful Answer:
"""