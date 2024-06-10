SQL_INSERT = 0
SQL_UPDATE = 1
SQL_DELETE = 2

GET_MAPS_TYPE_1_COMMAND_TEXT = "SELECT [Code], [Mapping_ID], [Short_Descr], [Long_Descr] FROM [dbo].[fieldMapping] WHERE [Mapping_ID] LIKE 'Affiliate' ORDER BY LEN([Code]) DESC"
GET_MAPS_TYPE_2_COMMAND_TEXT = "SELECT [Code], [Mapping_ID], [Short_Descr], [Long_Descr] FROM [dbo].[fieldMapping] WHERE [Mapping_ID] LIKE 'LOB' ORDER BY LEN([Code]) DESC"
GET_MAPS_TYPE_3_COMMAND_TEXT = "SELECT [Code], [Mapping_ID], [Short_Descr], [Long_Descr] FROM [dbo].[fieldMapping] WHERE [Mapping_ID] LIKE 'CustomField' ORDER BY LEN([Code]) DESC"
PROCESS_DELETE_COMMAND_TEXT = "DELETE FROM [dbo].[enhancedProductMapping] WHERE [id] = @id"

CLEAN_RULES_DATA_COMMAND_TEXT = "WITH RecursiveDelete AS (SELECT [RuleName] FROM [dbo].[Rules] WHERE [RuleName] = @RuleName UNION ALL SELECT r.[RuleName] from [dbo].[Rules] r INNER JOIN RecursiveDelete rd ON r.[RuleNameFK] = rd.[RuleName]) DELETE FROM [dbo].[Rules] WHERE [RuleName] IN (SELECT [RuleName] FROM RecursiveDelete);"

TRANSLATE_TEMPLATE = """
You will receive logical expressions that describe customer eligibility criteria for select products. 
Your mission is to translate these expressions into plain English.

Example Input:

((("General Market" AND ("Internet Essentials " OR "Xfinity Home Only" OR "Choice & Internet (TV,Internet) at $70" OR "Choice & Internet (TV,Internet) at $80" OR "Choice TP (TV,Internet,Phone) at $90" OR "Select TP (TV,Internet,Phone) at Everyday Pricing" OR "Sig Plus More (TV, Internet, Phone) at $165" OR "Standard Plus More (TV, Internet, Phone) at Every Day Price" OR "Basic TV & Fast at $90")) OR (((97028 OR 97029 OR 97170 OR 97172) AND (NOT 97180)) AND ("Select Plus More (TV, Internet, Phone) at Every Day Price" OR "Sig Plus (TV & Internet) at Every Day Price" OR "Sig Plus More (TV, Internet, Phone) at $175" OR "Super Plus More (TV, Internet, Phone) at $185" OR "Basic TV & SuperFast at $90" OR "Basic TV & GIG at $90" OR "Basic TV & Gig Extra at $90")) OR ("Dot Com" AND ("Choice & Internet (TV,Internet) at $70" OR "Choice & Internet (TV,Internet) at $80" OR "Choice TP (TV,Internet,Phone) at $90" OR "Standard Plus More (TV, Internet, Phone) at Every Day Price" OR "Select Plus More (TV, Internet, Phone) at Every Day Price" OR "Select TP (TV,Internet,Phone) at Everyday Pricing"))) AND (NOT 82118) AND (NOT 103086))

Example Output:

This offer is available through the General Market to Internet Essentials, Xfinity Home Only, Choice & Internet, Choice TP, Select TP, Sig Plus More, Standard Plus More and Basic TV & Fast customers.  It is also available through Dot Com to Choice & Internet, Choice TP, Standard Plus More, Select Plus More, and Select TP customers.

User:
{expression}
"""