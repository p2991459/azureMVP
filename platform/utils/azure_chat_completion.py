import openai, os, requests


class AzureOpenAI:
    openai.api_version = "2023-08-01-preview"
    openai.api_type = "azure"
    openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment_id = os.getenv("AZURE_OPENAI_CHAT_DEPLOYED_MODEL")
    search_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
    def __init__(self,search_index_name):
        self.search_index_name = search_index_name
    def _setup_byod(self) -> None:
        """Sets up the OpenAI Python SDK to use your own data for the chat endpoint.
        :param deployment_id: The deployment ID for the model to use with your own data.

        To remove this configuration, simply set openai.requestssession to None.
        """

        class BringYourOwnDataAdapter(requests.adapters.HTTPAdapter):

            def send(self, request, **kwargs):
                request.url = f"{openai.api_base}/openai/deployments/{AzureOpenAI.deployment_id}/extensions/chat/completions?api-version={openai.api_version}"
                print(request.url)
                return super().send(request, **kwargs)

        session = requests.Session()

        # Mount a custom adapter which will use the extensions endpoint for any call using the given `deployment_id`
        session.mount(
            prefix=f"{openai.api_base}/openai/deployments/{self.deployment_id}",
            adapter=BringYourOwnDataAdapter()
        )

        openai.requestssession = session

    def chat_query(self,query):
        self._setup_byod()
        completion = openai.ChatCompletion.create(
            messages=[{"role": "user", "content": query}],
            deployment_id=self.deployment_id,
            dataSources=[  # camelCase is intentional, as this is the format the API expects
                {
                    "type": "AzureCognitiveSearch",
                    "parameters": {
                        "endpoint": self.search_endpoint,
                        "key": self.search_key,
                        "indexName": self.search_index_name,
                    }
                }
            ]
        )
        return completion

