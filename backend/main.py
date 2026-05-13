import imageio.v3 as iio
from pathlib import Path
from torchvision.utils import save_image
from torchvision import transforms
import pyexiv2
import shutil

from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader

class_names = []

def set_class_names(class_names_list):
    global class_names
    class_names = class_names_list

def delete_folder(folder_path):
    shutil.rmtree(folder_path)

def create_folder(folder_path):
    if not Path(folder_path).exists():
        Path(folder_path).mkdir(parents=True, exist_ok=True)

def move_image(source_file_path, destination_path):
    source_file = Path(source_file_path)
    if source_file.is_file():
        shutil.move(str(source_file), str(Path(destination_path) / source_file.name))

def get_image_tags(image_path):
    metadata = pyexiv2.ImageMetadata(image_path)
    metadata.read()
    return metadata

def set_image_tags(image_path, tags):
    metadata = pyexiv2.ImageMetadata(image_path)
    metadata.read()
    metadata['Iptc.Application2.Keywords'] = tags
    metadata.write()
    
def get_image_class_name(image_path):
    metadata = get_image_tags(image_path)
    keywords = metadata.get('Iptc.Application2.Keywords')
    if keywords is not None:
        return keywords.value[0]
    return None

def get_class_name_from_model(image_path):
    # TODO: implement this function to get the class name and tags from the model prediction through the api call to the model server
    pass

def get_class_names_from_model(unsorted_folder_path):
    # TODO: fix this function to get the class names from the model prediction through the api call to the model server
    images = list()
    for file in Path(unsorted_folder_path).iterdir():
        if not file.is_file():
            if file.is_dir():
                for image in file.iterdir():
                    if not image.is_file():
                        continue
                    images.append((image, get_class_name_from_model(image)))
            continue
    return images


# will delete this once connected to the model api
images = list()
folderNames = [f.name for f in Path("dataset/").iterdir() if f.is_dir()]
lastImageIndexes = {folderName: -1 for folderName in folderNames}
for file in Path("dataset/").iterdir():
    if not file.is_file():
        if file.is_dir():
            currentFolderName = file.name
            # set last index to the last index of the previous folder
            lastImageIndexes[currentFolderName] = lastImageIndexes[folderNames[folderNames.index(currentFolderName) - 1]]
            for image in file.iterdir():
                if not image.is_file():
                    continue
                images.append((image, currentFolderName))
                lastImageIndexes[currentFolderName] += 1
        continue
    
    

create_folder("sorted_images")
for folderName in folderNames:
    create_folder(f"sorted_images/{folderName}")

for image, folderName in images:
    move_image(image, f"sorted_images/{folderName}")


