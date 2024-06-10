This Azure Function requires the following configuration parameters:

```json
{
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "PYTHON_ISOLATE_WORKER_DEPENDENCIES": "1",
    "AzureWebJobsFeatureFlags": "EnableWorkerIndexing",
    "AzureWebJobsStorage": "",
    "ReferenceDataConnectionString": "",
    "RulesDataConnectionString": "",
    "AZURE_OPENAI_API_KEY": "",
    "AZURE_OPENAI_ENDPOINT": "",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "",
    "AZURE_OPENAI_API_VERSION": ""
  }
}
```