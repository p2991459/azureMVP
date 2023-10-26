from azure.search.documents.indexes.models import (
SearchIndexerKnowledgeStore,
InputFieldMappingEntry,
SearchIndexerKnowledgeStoreProjection,
SearchIndexerKnowledgeStoreFileProjectionSelector
)

from .azure_utils import AzureResourceClient

arc = AzureResourceClient()
class CreateKnowledgeStore:
    def __init__(self,index_prefix,content_context):
        self.content_context = content_context
        self.index_prefix = index_prefix
    storage_connection_string = arc.get_knowledge_store_connection_string()

    def knowledge_store(self):
        content_context = self.content_context
        projection_inputs = [
                        InputFieldMappingEntry(name="source_document_id",
                                               source="/document/document_id"),
                        InputFieldMappingEntry(name="source_document_filepath",
                                               source="/document/filepath"),
                        InputFieldMappingEntry(name="source_field_name",
                                               source=f"{content_context}/chunks/*/embedding_metadata/fieldname"),
                        InputFieldMappingEntry(name="title",
                                               source=f"{content_context}/chunks/*/title"),
                        InputFieldMappingEntry(name="text",
                                               source=f"{content_context}/chunks/*/content"),
                        InputFieldMappingEntry(name="embedding",
                                               source=f"{content_context}/chunks/*/embedding_metadata/embedding"),
                        InputFieldMappingEntry(name="index",
                                               source=f"{content_context}/chunks/*/embedding_metadata/index"),
                        InputFieldMappingEntry(name="offset",
                                               source=f"{content_context}/chunks/*/embedding_metadata/offset"),
                        InputFieldMappingEntry(name="length",
                                               source=f"{content_context}/chunks/*/embedding_metadata/length")
                    ]
        projections = [SearchIndexerKnowledgeStoreProjection(objects=[SearchIndexerKnowledgeStoreFileProjectionSelector(
                    storage_container=arc.get_chunk_index_blob_container_name(self.index_prefix),
                    generated_key_name="id",
                    source_context=f"{content_context}/chunks/*",
                    inputs = projection_inputs,)]),
            SearchIndexerKnowledgeStoreProjection(
                files=[SearchIndexerKnowledgeStoreFileProjectionSelector(
                    storage_container=f"{arc.get_chunk_index_blob_container_name(self.index_prefix)}images",
                    generated_key_name="imagepath",
                    source="/document/normalized_images/*",
                    inputs=[]
                )
                ])
        ]
        return SearchIndexerKnowledgeStore(storage_connection_string=self.storage_connection_string,
                                                  projections=projections)




