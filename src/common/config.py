#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='../backend/credentials.env')

class BotConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

class CosmosConfig:
    """ Cosmos Configuration """

    ENDPOINT = os.environ.get("AZURE_COSMOSDB_ENDPOINT", "")
    CONNECTION_STRING = os.environ.get("AZURE_COMOSDB_CONNECTION_STRING", "")
    DATABASE = os.environ.get("AZURE_COSMOSDB_DATABASE_NAME", "")
    CONTAINER = os.environ.get("AZURE_COSMOSDB_CONTAINER_NAME", "")

class AzureOpenAIConfig:
    """ OpenAI Configuration """

    ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
    API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "")
    MODEL_NAME = os.environ.get("AZURE_OPENAI_MODEL_NAME", "")
