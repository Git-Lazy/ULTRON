import fastapi
from fastapi import UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import requests as http_requests
import sys
from pathlib import Path

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
async def create_class(name: str = Form(...), examples: list[UploadFile] | None = File(None)):
    try:
        # register class name
        backend.add_class_name(name)

        # determine repository-root examples folder based on backend module location
        base_dir = Path(backend.__file__).parent
        examples_dir = base_dir / "examples" / name
        examples_dir.mkdir(parents=True, exist_ok=True)

        saved = []
        if examples:
            for upload in examples:
                dest = examples_dir / upload.filename
                with dest.open("wb") as f:
                    content = await upload.read()
                    f.write(content)
                saved.append(str(dest))

        return fastapi.responses.JSONResponse(status_code=201, content={"name": name, "saved": saved})
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


@app.get("/api/examples/{class_name}/{filename}")
def get_example_image(class_name: str, filename: str):
    """Serve example images for custom classes."""
    try:
        base_dir = Path(backend.__file__).parent
        file_path = base_dir / "examples" / class_name / filename
        
        # Security: prevent directory traversal
        examples_base = (base_dir / "examples").resolve()
        if not str(file_path.resolve()).startswith(str(examples_base)):
            return JSONResponse(status_code=403, content={"error": "Access denied"})
        
        if not file_path.exists():
            return JSONResponse(status_code=404, content={"error": "File not found"})
        
        return FileResponse(file_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/predict")
def predict(req: PredictionRequest):
    try:
        model_url = os.getenv('MODEL_SERVICE_URL', 'http://localhost:8001')
        response = http_requests.post(
            f"{model_url}/predict",
            json={"features": req.features}
        )
        return response.json()
    except Exception as e:
        return fastapi.responses.JSONResponse(
            status_code=500,
            content={"error": f"Model service error: {str(e)}"}
        )



# @app.on_event("shutdown")
# def shutdown_event():


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)