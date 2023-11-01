import gradio as gr
import shutil
import os
from apis.upload_pdf import upload_pdf
from settings import BASE_DIR
import pickle
import time
def save_uploaded_file(temp_file,static_dir):
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    file_name = os.path.basename(temp_file.name)
    file_path = os.path.join(static_dir, file_name)
    with open(file_path, 'wb') as f:
        shutil.copyfileobj(temp_file, f)
    temp_file.close()
    return file_path

progress1 = ""

def upload_docs(files,progress=gr.Progress()):
    static_dir = os.path.join(BASE_DIR, 'static')
    global progress1
    progress1 = progress
    print(f"THIS IS PROGRESS:{progress1}")
    print(f"This is type of progress: {type(progress1)}")
    print(f"This is dict of progress: {dir(progress1)}")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    else:
        shutil.rmtree(static_dir)
        os.makedirs(static_dir)
    for idx, file in enumerate(files):
        save_uploaded_file(file,static_dir)
    response = upload_pdf(static_dir)
    return response.text


pdf_interface = gr.Interface(
    upload_docs,
    gr.File(file_count="multiple", file_types=[".docx", ".pdf"]),
    gr.Textbox(),
).queue()