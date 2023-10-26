from .indexdoc import DocumentIndexManager
from .chunker_index import ChunkIndexManager
import time
def create_indexes(prefix, customer_storage_connection_string, container_name):
    index_manager = DocumentIndexManager()
    doc_index_resources = index_manager.create_document_index_resources(prefix, customer_storage_connection_string, container_name)

    time.sleep(5)

    chunk_index_manager = ChunkIndexManager()
    chunk_index_resources = chunk_index_manager.create_chunk_index_resources(prefix)
    return {"doc_index_resources": doc_index_resources, "chunk_index_resources": chunk_index_resources}

def delete_indexes(prefix):
    index_manager = DocumentIndexManager()
    index_manager.delete_document_index_resources(prefix)
    chunk_index_manager = ChunkIndexManager()
    chunk_index_manager.delete_chunk_index_resources(prefix)
