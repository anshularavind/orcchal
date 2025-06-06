from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse
import os
from app.llmresponse import llm_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/input_url")
def read_input_url(input_url: str, topic: str):
    llm_response(input_url, topic)

    try:
        parsed_url = urlparse(input_url)
        domain = parsed_url.netloc  
        
        expected_filename = f"{domain}_.html" 
        file_path = os.path.join("final_html", expected_filename)
        
        if os.path.exists(file_path):
            return FileResponse(
                path=file_path,
                filename=expected_filename,
                media_type='text/html'
            )
        else:
            return {"success": False, "error": f"File not found: {expected_filename}"}
            
    except Exception as e:
        return {"success": False, "error": f"Error processing URL: {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
