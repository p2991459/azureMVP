import os
from utils.crud_indexs import create_indexes,delete_indexes
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import (
    RawVectorQuery,
    VectorizableTextQuery,
)
from fastapi import FastAPI, UploadFile
from typing import List
app = FastAPI()
from dotenv import load_dotenv
load_dotenv()
tenant = 'pythonsample'
index_name = ''
@app.post("/upload_pdf")
async def upload_pdf(files: List[UploadFile]):
    tenant = 'pythonsample'

    customer_storage_connection_string = os.getenv("DOCUMENT_AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("DOCUMENT_AZURE_STORAGE_CONTAINER_NAME")

    prefix = f"{tenant}-{container_name}"
    print(prefix)

    # Delete any existing Azure Cognitive Search resources
    delete_indexes(prefix)

    blob_service_client = BlobServiceClient.from_connection_string(customer_storage_connection_string)
    container_client = blob_service_client.get_container_client(container=container_name)

    if not container_client.exists():
        container_client.create_container()
        print(f"Deleted containers")
    for root, dirs, files in os.walk("./documents/"):
        for file in files:
            print(f"Getting file name: {file}")
            with open(os.path.join(root, file), "rb") as data:
                container_client.upload_blob(file, data, overwrite=True)
                print("Successfully uploaded file to blob storage")

    # ensure indexes
    index_resources = create_indexes(prefix, customer_storage_connection_string, container_name)
    global index_name
    index_name = index_resources["chunk_index_resources"]["index_name"]
    print(f"This is index name: {index_name}")
    return "File uploaded successfully"

@app.get("/search")
async def search(query: str):
    chunk_index_name = index_name
    search_client = SearchClient(os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT"), chunk_index_name,
                                 AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMIN_KEY")))
    vector_query = VectorizableTextQuery(text=query, k=3, fields="embedding")

    results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        select=["title", "text"],
        top=3
    )

    for result in results:
        print(f"Title: {result['title']}")
        print(f"Score: {result['@search.score']}")
        print(f"Content: {result['text']}")
    return "ok"



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)