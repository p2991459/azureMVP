import os
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    InputFieldMappingEntry,
    FieldMapping,
    WebApiSkill,
    OutputFieldMappingEntry,
    SearchIndexer,
    SearchIndexerSkillset,
    IndexingParameters,
    FieldMappingFunction,



)
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from .azure_knowledge_store import CreateKnowledgeStore
import time
from .create_resources import CreateResources
from .azure_utils import AzureResourceClient
from dotenv import load_dotenv
load_dotenv()
arc = AzureResourceClient()
resource = CreateResources()

class DocumentIndexManager():
    def _create_document_index(self, index_prefix):
        name = arc.get_index_name(index_prefix)
        fields = [
            SimpleField(name="document_id", type=SearchFieldDataType.String, filterable=True, sortable=True, key=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SimpleField(name="filesize", type=SearchFieldDataType.Int64),
            SimpleField(name="filepath", type=SearchFieldDataType.String)
        ]
        return resource.create_index(name, fields, vector_search=None, semantic_title_field_name="filepath",
                            semantic_content_field_names=["content"])

    def _create_document_datasource(self, index_prefix, storage_connection_string, container_name):
        name = arc.get_datasource_name(index_prefix)
        print(f"Creating Blob storage with data: {index_prefix},{storage_connection_string},{container_name} document datasource")
        return resource.create_blob_datasource(name, storage_connection_string, container_name)

    def _create_document_skillset(self, index_prefix, content_field_name="content"):
        print(f"Creating document skillset...")
        embedding_skill_endpoint = os.getenv("AZURE_SEARCH_EMBEDDING_SKILL_ENDPOINT")

        name = arc.get_skillset_name(index_prefix)
        chunk_index_blob_container_name = arc.get_chunk_index_blob_container_name(index_prefix)
        content_context = f"/document/{content_field_name}"
        embedding_skill = WebApiSkill(
            name="chunking-embedding-skill",
            uri=embedding_skill_endpoint,
            timeout="PT3M",
            batch_size=1,
            degree_of_parallelism=1,
            context=content_context,
            inputs=[
                InputFieldMappingEntry(name="document_id", source="/document/document_id"),
                InputFieldMappingEntry(name="text", source=content_context),
                InputFieldMappingEntry(name="filepath", source="/document/filepath"),
                InputFieldMappingEntry(name="fieldname", source=f"='{content_field_name}'")],
            outputs=[OutputFieldMappingEntry(name="chunks", target_name="chunks")])
        knowledge_store = CreateKnowledgeStore(index_prefix,content_context)
        skillset = SearchIndexerSkillset(name=name, skills=[embedding_skill], description=name,
                                         knowledge_store=knowledge_store.knowledge_store())
        client = arc.get_indexer_client()
        return client.create_skillset(skillset)

    def _create_document_indexer(self, index_prefix, data_source_name, index_name, skillset_name,
                                 content_field_name="content", generate_page_images=True):
        content_context = f"/document/{content_field_name}"
        name = arc.get_indexer_name(index_prefix)
        indexer_config = {"dataToExtract": "contentAndMetadata",
                          "imageAction": "generateNormalizedImagePerPage"} if generate_page_images else {
            "dataToExtract": "contentAndMetadata"}
        parameters = IndexingParameters(max_failed_items=-1, configuration=indexer_config)
        indexer = SearchIndexer(
            name=name,
            data_source_name=data_source_name,
            target_index_name=index_name,
            skillset_name=skillset_name,
            field_mappings=[FieldMapping(source_field_name="metadata_storage_path", target_field_name="document_id",
                                         mapping_function=FieldMappingFunction(name="base64Encode", parameters=None)),
                            FieldMapping(source_field_name="metadata_storage_name", target_field_name="filepath"),
                            FieldMapping(source_field_name="metadata_storage_size", target_field_name="filesize")],
            output_field_mappings=[],
            parameters=parameters
        )
        indexer_client = arc.get_indexer_client()
        return indexer_client.create_indexer(indexer)

    def create_document_index_resources(self, index_prefix, customer_storage_connection_string,
                                        customer_container_name) -> dict:
        print(
            f"Creating index resources with index_prefix:{index_prefix} connection string: {customer_storage_connection_string} and container_name; {customer_container_name}")
        index_name = self._create_document_index(index_prefix).name
        print(f"Created document index:{index_name}")
        print(f"Creating data source")
        data_source_name = self._create_document_datasource(index_prefix, customer_storage_connection_string,
                                                            customer_container_name).name
        print(f"creating skillset:{data_source_name}")
        skillset_name = self._create_document_skillset(index_prefix).name
        time.sleep(5)
        indexer_name = self._create_document_indexer(index_prefix, data_source_name, index_name, skillset_name).name
        print(f"Creating Indexer.......")
        resource.wait_for_indexer_completion(indexer_name)
        return {"index_name": index_name, "data_source_name": data_source_name, "skillset_name": skillset_name,
                "indexer_name": indexer_name}

    def delete_document_index_resources(self, index_prefix):
        index_client = arc.get_index_client()
        indexer_client = arc.get_indexer_client()

        index_client.delete_index(index=arc.get_index_name(index_prefix))
        indexer_client.delete_indexer(indexer=arc.get_indexer_name(index_prefix))
        indexer_client.delete_data_source_connection(data_source_connection=arc.get_datasource_name(index_prefix))
        indexer_client.delete_skillset(skillset=arc.get_skillset_name(index_prefix))

        # delete the knowledge store tables and blobs
        knowledge_store_connection_string = arc.get_knowledge_store_connection_string()

        # delete the container directly from storage
        try:
            blob_service = BlobServiceClient.from_connection_string(knowledge_store_connection_string)
            blob_service.delete_container(arc.get_chunk_index_blob_container_name(index_prefix))
        # handle resource not found error
        except ResourceNotFoundError:
            pass
