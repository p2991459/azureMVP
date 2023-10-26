import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from dotenv import load_dotenv
load_dotenv()
AZURE_SEARCH_SERVICE_ENDPOINT = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
print(AZURE_SEARCH_SERVICE_ENDPOINT,"************************")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
AZURE_SEARCH_KNOWLEDGE_STORE_CONNECTION_STRING = os.getenv("AZURE_KNOWLEDGE_STORE_STORAGE_CONNECTION_STRING")


class AzureResourceClient:
    def get_index_client(self) -> SearchIndexClient:
        return SearchIndexClient(AZURE_SEARCH_SERVICE_ENDPOINT, AzureKeyCredential(AZURE_SEARCH_KEY))

    def get_indexer_client(self) -> SearchIndexerClient:
        return SearchIndexerClient(AZURE_SEARCH_SERVICE_ENDPOINT, AzureKeyCredential(AZURE_SEARCH_KEY))

    def get_index_name(self,index_prefix):
        return f"{index_prefix}-index"

    def get_datasource_name(self,index_prefix):
        return f"{index_prefix}-datasource"

    def get_skillset_name(self,index_prefix):
        return f"{index_prefix}-skillset"

    def get_indexer_name(self,index_prefix):
        return f"{index_prefix}-indexer"

    def get_chunk_index_blob_container_name(self,index_prefix):
        return f"{index_prefix}ChunkIndex".replace('-', '').lower()

    def get_knowledge_store_connection_string(self,):
        return AZURE_SEARCH_KNOWLEDGE_STORE_CONNECTION_STRING