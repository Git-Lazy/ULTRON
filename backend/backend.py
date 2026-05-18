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
    
def add_class_name(class_name):
    global class_names
    if class_name not in class_names:
        class_names.append(class_name)

def delete_class_name(class_name):
    global class_names
    if class_name in class_names:
        class_names.remove(class_name)
    delete_example_images_for_class(class_name)
    
def delete_example_images_for_class(class_name):
    example_images_folder = Path(f"examples/{class_name}")
    if example_images_folder.exists() and example_images_folder.is_dir():
        delete_folder(example_images_folder)

def add_example_image(example_path, class_name):
    if class_name not in class_names:
        raise ValueError(f"Class name '{class_name}' does not exist.")
    else:
        copy_image(example_path, f"examples/{class_name}")
        metadata = pyexiv2.ImageMetadata(f"examples/{class_name}/{Path(example_path).name}")
        metadata.read()
        # TODO: set the class name and tags from the model prediction through the api call to the model server
        metadata['Iptc.Application2.vector'] = "example"
        metadata.write()

def get_example_image_data(example_path):
    metadata = pyexiv2.ImageMetadata(example_path)
    vector = metadata.get('Iptc.Application2.vector')
    return vector.value if vector is not None else []

def search_images(query):
    found_images_paths = []
    for folderName in class_names:
        if query.lower() in folderName.lower():
            for image in Path(f"sorted_images/{folderName}").iterdir():
                if not image.is_file():
                    continue
                found_images_paths.append(str(image))
        else:
            for image in Path(f"sorted_images/{folderName}").iterdir():
                if not image.is_file():
                    continue
                tags = get_image_tags(image)
                if query.lower() in image.name.lower() or query.lower() in str(tags).lower():
                    found_images_paths.append(str(image))
    return found_images_paths

def delete_folder(folder_path):
    shutil.rmtree(folder_path)

def create_folder(folder_path):
    if not Path(folder_path).exists():
        Path(folder_path).mkdir(parents=True, exist_ok=True)

def move_image(source_file_path, destination_path):
    source_file = Path(source_file_path)
    if source_file.is_file():
        if not Path(destination_path).exists():
            Path(destination_path).mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(Path(destination_path) / source_file.name))
        
def copy_image(source_file_path, destination_path):
    source_file = Path(source_file_path)
    if source_file.is_file():
        if not Path(destination_path).exists():
            Path(destination_path).mkdir(parents=True, exist_ok=True)
        shutil.copy(str(source_file), str(Path(destination_path) / source_file.name))

def get_image_tags(image_path):
    metadata = pyexiv2.ImageMetadata(image_path)
    keywords = metadata.get('Iptc.Application2.Keywords')
    return keywords.value if keywords is not None else []

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

def create_sorted_images_folder():
    create_folder("sorted_images")
    for folderName in class_names:
        create_folder(f"sorted_images/{folderName}")
        
def move_images_to_sorted_folder(images):
    for image, folderName in images:
        move_image(image, f"sorted_images/{folderName}")

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
    
move_images_to_sorted_folder(images)
delete_folder("dataset")






