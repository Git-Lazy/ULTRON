import requests
from pathlib import Path
with open("test.jpg", "rb") as f:
    response = requests.post("http://localhost:8001/predict_one",
                             files={"file": (Path("test.jpg").name, f, "image/jpeg")})
    print(response.json())
# import torchvision.transforms.functional as F
# print(F._interpolation_modes_from_int(2))


