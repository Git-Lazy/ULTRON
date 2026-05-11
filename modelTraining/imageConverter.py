from torch import tensor, zeros, save
from torchvision import transforms
import numpy
from PIL import Image
import torchvision.transforms.functional as F
import os



class ResizeWithPad:
    def __init__(self, target_size):
        self.target_size = target_size  # e.g. 224

    def __call__(self, img):
        _, w, h = img.shape  # PIL uses (width, height)
        scale = self.target_size / max(w, h)

        # Resize proportionally
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = F.resize(img, (new_h, new_w))

        # Calculate padding to reach target_size x target_size
        pad_left   = (self.target_size - new_w) // 2
        pad_right  = self.target_size - new_w - pad_left
        pad_top    = (self.target_size - new_h) // 2
        pad_bottom = self.target_size - new_h - pad_top

        img = F.pad(img, (pad_left, pad_top, pad_right, pad_bottom), fill=0)
        return img

# Usage
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ResizeWithPad(128),
])




def convert_imageset(path="trainingData/initialTraining", output_path="trainingData/convertedDataset.pkl"):
    classes = os.listdir(path)
    data = {
        "classes": classes,
        "data": {}
    }
    for i in range(len(classes)):
        image_count = len(os.listdir(os.path.join(path, classes[i])))
        data["data"][i] = zeros(image_count, 3, 128, 128)
    for class_name in classes:
        class_path = os.path.join(path, class_name)
        images = os.listdir(class_path)
        for image_name in images:
            try:
                image_path = os.path.join(class_path, image_name)
                image = Image.open(image_path).convert("RGB")
                image = transform(image)
                data["data"][classes.index(class_name)][images.index(image_name)] = image
            except:
                print(f"Error converting {image_name}")
                print(f"Error converting {class_name}")
                print()
        print(f"Converted {class_name} images")
    save(data, output_path)



convert_imageset()
#convert_imageset_test()

# image = Image.open("trainingData/initialTraining/chole_bhature/006.jpg").convert("RGB")
#
# image.save("fixedImage.jpg")
#
# tensor_image = transforms.ToTensor()(image)
# print(tensor_image.shape)
# tensor_normalized = transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])(tensor_image)
# print(tensor_normalized.shape)
# tensor_resized = ResizeWithPad(128)(tensor_normalized)
# print(tensor_resized.shape)


