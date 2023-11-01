from platform.apis.upload_pdf import upload_pdf
from platform.settings import BASE_DIR
import os

def test_upload_pdf():
    static_path = os.path.join(BASE_DIR,"static")
    upload_pdf(static_path)

