import requests
import sys

def test_upload():
    url = "http://127.0.0.1:8000/rag/documents/upload"
    headers = {"X-Description": "test description"}
    files = {"file": ("test.pdf", b"%PDF-1.4 dummy content", "application/pdf")}
    
    try:
        response = requests.post(url, headers=headers, files=files)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_upload()
