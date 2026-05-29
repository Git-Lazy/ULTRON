import fastapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import requests as http_requests
import sys
from pathlib import Path
import time

# Add parent directory to path to import backend module
sys.path.insert(0, str(Path(__file__).parent.parent))
import backend

load_dotenv()


app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    features: list[float]


@app.get("/api-key")
def get_api_key():
    api_key = os.getenv("API_KEY")
    if not api_key:
        return fastapi.responses.JSONResponse(status_code=404, content={"error": "API_KEY not set"})
    return {"api_key": api_key}

@app.get("/api/classes")
def read_items():
    try:
        class_names = backend.class_names
        return fastapi.responses.JSONResponse(status_code=200, content={"classes": class_names})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})
    
@app.get("/api/examples")
def read_examples():
    try:
        examples = backend.get_example_images()
        return fastapi.responses.JSONResponse(status_code=200, content={"examples": examples})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/search")
def search_items(query: str):
    try:
        results = backend.search_images(query)
        return fastapi.responses.JSONResponse(status_code=200, content={"results": results})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/classes")
def create_class(class_name: str):
    try:
        backend.add_class_name(class_name)
        return fastapi.responses.JSONResponse(status_code=201, content={"name": class_name})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})
    
@app.post("/api/examples")
def create_example(example_path: str, class_name: str):
    try:
        backend.add_example_image(example_path, class_name)
        return fastapi.responses.JSONResponse(status_code=201, content={"path": example_path, "class_name": class_name})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})

@app.delete("/api/classes/{class_name}")
def delete_class(class_name: str):
    try:
        backend.delete_class_name(class_name)
        return fastapi.responses.JSONResponse(status_code=200, content={"class_name": class_name, "status": "deleted"})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/predict")
def predict(req: PredictionRequest):
    try:
        response = http_requests.post(
            f"http://localhost:8001/predict",
            json={"features": req.features}
        )
        return response.json()
    except Exception as e:
        return fastapi.responses.JSONResponse(
            status_code=500,
            content={"error": f"Model service error: {str(e)}"}
        )
        

@app.post("/sort")
def sort_images(folder_path: str):
    try:
        backend.sort_images(folder_path)
        return fastapi.responses.JSONResponse(status_code=200, content={"status": "sorting started"})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
def health_check():
    return fastapi.responses.JSONResponse(status_code=200, content={"status": "healthy"})

# @app.on_event("shutdown")
# def shutdown_event():

server: uvicorn.Server = None  # will hold the real running instance

@app.get("/shutdown")
async def shutdown():
    try:
        response = http_requests.get("http://localhost:8001/shutdown")
        while response.status_code != 200:
            print("Failed to shutdown model server, retrying...")
            time.sleep(1)
            response = http_requests.get("http://localhost:8001/shutdown")
        print("model server shutdown initiated")
        server.should_exit = True
        return fastapi.responses.JSONResponse(status_code=200, content={"status": "shutdown initiated"})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    server.run()