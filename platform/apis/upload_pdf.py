import os
import requests

def upload_pdf(static_dir_path):
    url = "http://127.0.0.1:8000/upload_pdf"
    payload = {}
    file_names = os.listdir(static_dir_path)
    files = [
        ('files', ('file', open(os.path.join(static_dir_path,file_path), 'rb'), 'application/octet-stream')) for file_path in file_names
    ]
    headers = {
        'accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    if response.status_code == 200:
        print("Files uploaded successfully!")
    else:
        print("Error uploading files:", response.status_code)
    return response


