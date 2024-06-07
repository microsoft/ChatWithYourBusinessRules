SQL_INSERT = 0
SQL_UPDATE = 1
SQL_DELETE = 2

GET_MAPS_TYPE_1_COMMAND_TEXT = "SELECT [Code], [Mapping_ID], [Short_Descr], [Long_Descr] FROM [dbo].[fieldMapping] WHERE [Mapping_ID] LIKE 'Affiliate' ORDER BY LEN([Code]) DESC"
GET_MAPS_TYPE_2_COMMAND_TEXT = "SELECT [Code], [Mapping_ID], [Short_Descr], [Long_Descr] FROM [dbo].[fieldMapping] WHERE [Mapping_ID] LIKE 'LOB' ORDER BY LEN([Code]) DESC"
GET_MAPS_TYPE_3_COMMAND_TEXT = "SELECT [Code], [Mapping_ID], [Short_Descr], [Long_Descr] FROM [dbo].[fieldMapping] WHERE [Mapping_ID] LIKE 'CustomField' ORDER BY LEN([Code]) DESC"
PROCESS_DELETE_COMMAND_TEXT = "DELETE FROM [dbo].[enhancedProductMapping] WHERE [id] = @id"