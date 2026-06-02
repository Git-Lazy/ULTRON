import fastapi
import mimetypes
import uvicorn

#tbd
from pathlib import Path

from dotenv import load_dotenv
import os
from pydantic import BaseModel
import requests as http_requests
import backend
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Body, responses
import time


load_dotenv()


app = fastapi.FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/classes/")
def read_items():
    try:
        class_names = backend.class_names
        return fastapi.responses.JSONResponse(status_code=200, content={"classes": class_names})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})
    
@app.get("/examples/")
def read_items():
    try:
        examples = {}
        for cls in backend.class_names:
            examples[cls] = backend.get_example_images(cls)
        return fastapi.responses.JSONResponse(status_code=200, content={"examples": examples})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/examples/{class_name}/{filename}")
def read_example_image(class_name: str, filename: str):
    file_path = os.path.join("examples", class_name, filename)
    if not os.path.isfile(file_path):
        return fastapi.responses.JSONResponse(status_code=404, content={"error": "File not found"})
    media_type, _ = mimetypes.guess_type(file_path)
    return responses.FileResponse(file_path, media_type=media_type or "application/octet-stream")

@app.get("/search/")
def search_items(query: str):
    try:
        results = backend.search_images(query)
        return fastapi.responses.JSONResponse(status_code=200, content={"results": results})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/classes/")
def create_item(class_name: str):
    try:
        backend.add_class_name(class_name)
        return fastapi.responses.JSONResponse(status_code=201, content={"name": class_name})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})
    
@app.post("/examples/")
def create_item(example_path: str, class_name: str):
    try:
        backend.add_example_image(example_path, class_name)
        return fastapi.responses.JSONResponse(status_code=201, content={"path": example_path, "class_name": class_name})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})

@app.delete("/classes/{class_name}")
def delete_item(class_name: str):
    try:
        backend.delete_class_name(class_name)
        return fastapi.responses.JSONResponse(status_code=200, content={"class_name": class_name, "status": "deleted"})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})


class PredictRequest(BaseModel):
    file_path: Optional[str] = None


@app.post("/predict")
async def predict(image_path: str):
    try:
        if payload and payload.file_path:
            file_path = payload.file_path
            if not Path(file_path).is_file():
                return fastapi.responses.JSONResponse(status_code=400, content={"error": f"File path not found: {file_path}"})
            response = backend.get_prediction_from_model(file_path)
            if response is None:
                return fastapi.responses.JSONResponse(status_code=500, content={"error": "Model returned no prediction"})
            return response

        if file is None:
            return fastapi.responses.JSONResponse(status_code=400, content={"error": "file or file_path is required"})

        # Create temp directory if it doesn't exist
        # Path("temp").mkdir(exist_ok=True)
        
        # # temp saving file
        # file_path = f"temp/{file.filename}"
        # with open(file_path, "wb") as temp_f:
        #     temp_f.write(await file.read())
        
            # original
            # with open(file_path, "rb") as f:
            #     response = http_requests.post(
            #         "http://localhost:8001/predict_one",
            #         files={"file": (Path(file_path).name, f, f"image/{Path(file_path).suffix[1:]}")}
            #     )
        if backend.get_image_class_name(image_path) is not None:
            return fastapi.responses.JSONResponse(status_code=200, content={"class": backend.get_image_class_name(image_path)})
        else:
            vector = backend.get_prediction_from_model(image_path)
            backend.set_image_tags(image_path, vector)
            return fastapi.responses.JSONResponse(status_code=200, content={"class": backend.get_image_class_name(image_path)})
            
            # Check if model returned an error
            # if response.status_code != 200:
            #     return fastapi.responses.JSONResponse(
            #         status_code=response.status_code,
            #         content=response.json()
            #     )
            
            # return response.json()
        # finally:
        #     # Clean up temp file
        #     if Path(file_path).exists():
        #         os.remove(file_path)
                
    except Exception as e:
        return fastapi.responses.JSONResponse(
            status_code=500,
            content={"error": f"Model service error: {str(e)}"}
        )

@app.post("/sort")
def sort_images(folder_path: str = Body(...)):
    try:
        backend.sort_images(folder_path)
        return fastapi.responses.JSONResponse(status_code=200, content={"status": "sorting started"})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
def health_check():
    return fastapi.responses.JSONResponse(status_code=200, content={"status": "healthy"})


server: uvicorn.Server = None  # will hold the real running instance

@app.get("/shutdown")
async def shutdown():
    try:
        backend.save_class_names_to_json()
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