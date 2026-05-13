import backend
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
            f"{os.getenv('MODEL_SERVICE_URL')}/predict",
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