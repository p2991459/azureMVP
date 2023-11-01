import os
import time

from settings import BASE_DIR
from utils.crud_indexs import create_indexes,delete_indexes
from azure.storage.blob import BlobServiceClient
from utils.azure_chat_completion import AzureOpenAI
from fastapi import FastAPI, UploadFile
from fastapi.responses import RedirectResponse
from typing import List
from gradio_routes.pdf_interface import pdf_interface,progress1
import starlette.status as status
import gradio as gr
import pickle
app = FastAPI()
from dotenv import load_dotenv
load_dotenv()
tenant = 'pythonsample'
index_name = ''

app = gr.mount_gradio_app(app, pdf_interface, path="/home/main")

@app.get("/")
async def home():
    return RedirectResponse(url="/home/main", status_code=status.HTTP_302_FOUND)


@app.post("/upload_pdf")
async def upload_pdf(files: List[UploadFile]):
    print(files)
    print(type(files))
    tenant = 'pythonsample'
    customer_storage_connection_string = os.getenv("DOCUMENT_AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("DOCUMENT_AZURE_STORAGE_CONTAINER_NAME")
    print(f"THIS IS PROGRESS:{progress1}")
    print(f"This is type of progress: {type(progress1)}")
    print(f"This is dict of progress: {dir(progress1)}")
    time.sleep(5)
    progress1(0, desc="Starting...")
    time.sleep(5)
    progress1(0.3, desc="ffgafadf...")
    progress1(.7, desc="You I loaded it...")
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
    return "Your files has been up"

@app.get("/search")
async def search(query: str):
    chunk_index_name = "pythonsample-pdf-data-chunk-index"
    llm = AzureOpenAI(chunk_index_name)
    response = llm.chat_query(query)
    print(response)
    return "ok"



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)