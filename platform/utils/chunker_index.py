import os
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchIndexer,
    IndexingParameters,
    VectorSearch,
    AzureOpenAIVectorizer,
    HnswVectorSearchAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    HnswParameters,
    ExhaustiveKnnParameters,
    VectorSearchProfile,
    AzureOpenAIParameters,
    ExhaustiveKnnVectorSearchAlgorithmConfiguration,
    SearchField,

)
import time
from .create_resources import CreateResources
from .azure_utils import AzureResourceClient
from dotenv import load_dotenv
load_dotenv()
arc = AzureResourceClient()
resource = CreateResources()


class ChunkIndexManager():

    def _create_chunk_index(self, index_prefix):
        print(f"Creating chunk index......")
        name = arc.get_index_name(f"{index_prefix}-chunk")
        vector_search = VectorSearch(
            algorithms=[
                HnswVectorSearchAlgorithmConfiguration(
                    name="myHnsw",
                    kind=VectorSearchAlgorithmKind.HNSW,
                    parameters=HnswParameters(
                        m=4,
                        ef_construction=400,
                        ef_search=500,
                        metric="cosine"
                    )
                ),
                ExhaustiveKnnVectorSearchAlgorithmConfiguration(
                    name="myExhaustiveKnn",
                    kind=VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,
                    parameters=ExhaustiveKnnParameters(
                        metric="cosine"
                    )
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="myHnswProfile",
                    algorithm="myHnsw",
                    vectorizer="myOpenAI"
                ),
                VectorSearchProfile(
                    name="myExhaustiveKnnProfile",
                    algorithm="myExhaustiveKnn",
                    vectorizer="myOpenAI"
                )
            ],
            vectorizers=[
                AzureOpenAIVectorizer(
                    name="myOpenAI",
                    kind="azureOpenAI",
                    azure_open_ai_parameters=AzureOpenAIParameters(
                        resource_uri=os.getenv("AZURE_OPENAI_ENDPOINT"),
                        deployment_id=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYED_MODEL"),
                        api_key=os.getenv("AZURE_OPENAI_API_KEY")
                    )
                )
            ]

        )

        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True,
                        key=True),
            SimpleField(name="source_document_id", type=SearchFieldDataType.String),
            SimpleField(name="source_document_filepath", type=SearchFieldDataType.String),
            SimpleField(name="source_field_name", type=SearchFieldDataType.String),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SimpleField(name="index", type=SearchFieldDataType.Int64),
            SimpleField(name="offset", type=SearchFieldDataType.Int64),
            SimpleField(name="length", type=SearchFieldDataType.Int64),
            SimpleField(name="hash", type=SearchFieldDataType.String),
            SearchableField(name="text", type=SearchFieldDataType.String),
            SearchField(name="embedding", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True, vector_search_dimensions=1536, vector_search_profile="myHnswProfile")
        ]
        print(f"Creating chunk index using embedding field details....")
        index = resource.create_index(name, fields, vector_search=vector_search, semantic_title_field_name="title",
                             semantic_content_field_names=["text"])
        print("Almost finishes chunk index creatation.....")
        return index

    def _create_chunk_datasource(self, index_prefix, storage_connection_string, container_name):
        name = arc.get_datasource_name(f"{index_prefix}-chunk")
        return resource.create_blob_datasource(name, storage_connection_string, container_name)

    def _create_chunk_indexer(self, index_prefix, data_source_name, index_name):
        name = arc.get_indexer_name(f"{index_prefix}-chunk")
        parameters = IndexingParameters(configuration={"parsing_mode": "json"})
        indexer = SearchIndexer(
            name=name,
            data_source_name=data_source_name,
            target_index_name=index_name,
            parameters=parameters
        )
        indexer_client = arc.get_indexer_client()
        return indexer_client.create_indexer(indexer)

    def create_chunk_index_resources(self, index_prefix) -> dict:
        chunk_index_storage_connection_string = arc.get_knowledge_store_connection_string()
        chunk_index_blob_container_name = arc.get_chunk_index_blob_container_name(index_prefix)

        index_name = self._create_chunk_index(index_prefix).name
        data_source_name = self._create_chunk_datasource(index_prefix, chunk_index_storage_connection_string,
                                                         chunk_index_blob_container_name).name
        time.sleep(5)
        indexer_name = self._create_chunk_indexer(index_prefix, data_source_name, index_name).name
        resource.wait_for_indexer_completion(indexer_name)
        return {"index_name": index_name, "data_source_name": data_source_name, "indexer_name": indexer_name}

    # delete all the resources
    def delete_chunk_index_resources(self, index_prefix):
        index_client = arc.get_index_client()
        indexer_client = arc.get_indexer_client()
        index_client.delete_index(index=f"{index_prefix}-chunk-index")
        indexer_client.delete_indexer(indexer=f"{index_prefix}-chunk-indexer")
        indexer_client.delete_data_source_connection(data_source_connection=f"{index_prefix}-chunk-datasource")




