import backend.backend as backend
import fastapi
import uvicorn
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import requests as http_requests


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

@app.get("/shutdown")
def shutdown():
    try:
        # Perform any necessary cleanup here
        # For example, you could close database connections or release resources
        # Then, shut down the server
        response = http_requests.get(
            f"http://localhost:8001/shutdown"
        )
        uvicorn_server = uvicorn.Server(uvicorn.Config(app))
        uvicorn_server.should_exit = True
        return fastapi.responses.JSONResponse(status_code=200, content={"status": "shutdown initiated"})
    except Exception as e:
        return fastapi.responses.JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)