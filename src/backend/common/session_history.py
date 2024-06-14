from langchain_community.chat_message_histories import CosmosDBChatMessageHistory

from config import CosmosConfig

def get_session_history(session_id: str, user_id: str) -> CosmosDBChatMessageHistory:
    cosmos = CosmosDBChatMessageHistory(
        cosmos_endpoint=CosmosConfig.ENDPOINT,
        cosmos_database=CosmosConfig.DATABASE,
        cosmos_container=CosmosConfig.CONTAINER,
        connection_string=CosmosConfig.CONNECTION_STRING,
        session_id=session_id,
        user_id=user_id
    )

    # prepare the cosmosdb instance
    cosmos.prepare_cosmos()
    return cosmos
