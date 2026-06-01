import numpy
from PIL import Image
import os
from fastapi import FastAPI, File, UploadFile, responses
import io
from typing import List
import uvicorn
import sys
import onnxruntime as onnx


def resource_path(relative_path):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)





session = onnx.InferenceSession(resource_path("model.onnx"))
class Model:
    def __init__(self, session: onnx.InferenceSession):
        self.session = session
    def __call__(self, x: numpy.ndarray):
        input_name = self.session.get_inputs()[0].name
        output = self.session.run(None, {input_name: x})[0]
        return output


app = FastAPI()
model = Model(session)


class ResizeWithPad:
    def __init__(self, target_size):
        self.target_size = target_size

    def __call__(self, img: numpy.ndarray):
        _, w, h = img.shape
        print("widtht and height:", w, h)
        scale = self.target_size / max(w, h)
        print("scale:", scale)

        new_w = int(w * scale)
        print("new width:", new_w)
        new_h = int(h * scale)
        print("new height:", new_h)

        # Convert to PIL for resizing
        pil = Image.fromarray((img.transpose(1, 2, 0) * 255).astype(numpy.uint8))
        pil = pil.resize((new_h, new_w), Image.BILINEAR)
        img = numpy.array(pil).astype(numpy.float32).transpose(2, 0, 1) / 255.0

        pad_left = (self.target_size - new_w) // 2
        print("pad left:", pad_left)
        pad_right = self.target_size - new_w - pad_left
        print("pad right:", pad_right)
        pad_top = (self.target_size - new_h) // 2
        print("pad top:", pad_top)
        pad_bottom = self.target_size - new_h - pad_top
        print("pad bottom:", pad_bottom)

        print("img shape before padding:")
        print(img.shape)
        img = numpy.pad(img, ((0, 0), (pad_left, pad_right), (pad_top, pad_bottom)), constant_values=0)
        print("img shape after padding:")

        return img


def transform(img: Image.Image) -> numpy.ndarray:
    # ToTensor: HWC -> CHW, scale to [0, 1]
    arr = numpy.array(img).astype(numpy.float32) / 255.0
    arr = arr.transpose(2, 0, 1)
    # Normalize mean=0.5, std=0.5
    arr = (arr - 0.5) / 0.5
    # ResizeWithPad
    print("pre resize")
    print(arr.shape)
    arr = ResizeWithPad(128)(arr)
    print("post resize")
    print(arr.shape)
    return arr

@app.post("/predict_one")
async def predict(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith("image/"):
            raise ValueError("Invalid file type")
        print("file content type: ", file.content_type)
        content = await file.read()
        print("got content:")
        image = Image.open(io.BytesIO(content)).convert("RGB")
        print("opened image:")
        image = transform(image)
        print("transformed image:")
        print(image.shape)
        input_tensor = numpy.zeros((1, 3, 128, 128), dtype=numpy.float32)
        input_tensor[0] = image
        input_tensor = input_tensor
        embedding = model(input_tensor)[0]
        print("got embedding:")
        return embedding.tolist()
    except Exception as e:
        return responses.JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/predict_many")
async def predict(files: List[UploadFile] = File(...)):
    try:
        input_vectors = numpy.zeros((len(files), 3, 128, 128), dtype=numpy.float32)
        for i, file in enumerate(files):
            if not file.content_type.startswith("image/"):
                raise ValueError("Invalid file type")
            content = await file.read()
            image = Image.open(io.BytesIO(content)).convert("RGB")
            image = transform(image)
            input_vectors[i] = image
        print("input shape: ", input_vectors.shape)
        embedding = model(input_vectors)
        print("got embedding:")
        return embedding.tolist()
    except Exception as e:
        print(e)
        return responses.JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
async def health():
    return {"status": "ok"}

server: uvicorn.Server = None  # will hold the real running instance

@app.get("/shutdown")
async def shutdown():
    try:
        server.should_exit = True
        return responses.JSONResponse(status_code=200, content={"status": "shutdown initiated"})
    except Exception as e:
        return responses.JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    config = uvicorn.Config(app, host="0.0.0.0", port=8001)
    server = uvicorn.Server(config)
    server.run()