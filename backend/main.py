import fastapi
import uvicorn
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import requests as http_requests
import backend
from fastapi import FastAPI, File, UploadFile, responses
import time


load_dotenv()


app = fastapi.FastAPI()


class PredictionRequest(BaseModel):
    features: list[float]


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
        examples = backend.get_example_images()
        return fastapi.responses.JSONResponse(status_code=200, content={"examples": examples})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})

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



@app.post("/predict")
def predict(file: UploadFile = File(...)):
    try:
        response = http_requests.post(
            f"http://localhost:8001/predict_one",
            json={"file": file.filename}
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