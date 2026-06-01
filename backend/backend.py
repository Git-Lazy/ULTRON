import json
import traceback
import imageio.v3 as iio
from pathlib import Path
import shutil
# import piexif
import requests as http_requests
# import torch

old_path = Path("dataset/")
new_path = Path("sorted_images/")


class_names = []

def set_class_names(class_names_list):
    global class_names
    class_names = class_names_list


def load_class_names_from_json():
    json_path = "examples/class_names.json"
    if Path(json_path).exists():
        class_names_list = json.loads(Path(json_path).read_text())
        set_class_names(class_names_list)
    else:
        print(f"No JSON file found for class names. Starting with an empty list.")
        set_class_names([])

load_class_names_from_json()


    
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

def add_example_image(example_path, class_name, vector=None):
    
    if class_name not in class_names:
        class_names.append(class_name)
    copy_image(example_path, f"examples/{class_name}")
    dest_path = f"examples/{class_name}/{Path(example_path).name}"
    
    if vector is None:
        vector = get_prediction_from_model(example_path)
    json_path = dest_path + ".json"
    Path(json_path).write_text(json.dumps(vector))
    


def save_class_names_to_json(class_names):
    json_path = "examples/class_names.json"
    Path(json_path).write_text(json.dumps(class_names))

def get_example_images(class_name):
    example_images = []
    example_images_folder = Path(f"examples/{class_name}")
    if example_images_folder.exists() and example_images_folder.is_dir():
        for image in example_images_folder.iterdir():
            if not image.is_file():
                continue
            if is_image_file(image):
                example_images.append(str(image))
    return example_images

def get_example_image_data(example_path):
    json_path = example_path + ".json"
    if Path(json_path).exists():
        vector = json.loads(Path(json_path).read_text())
        return vector
    print(f"No JSON file found for example image '{example_path}'. Returning None.")
    exit(42)
    return None

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
    json_path = str(image_path) + ".json"
    if Path(json_path).exists():
        json_tags = Path(json_path).read_text()
        tags = json.loads(json_tags)
        return tags
    return None

def set_image_tags(image_path, vector):
    weighted_cosine_similarity_scores = {}
    for class_name in class_names:
        weighted_cosine_similarity_scores[f'{class_name}'] = weighted_cosine_similarity(vector, [get_example_image_data(f"examples/{class_name}/{image.name}") for image in Path(f"examples/{class_name}").iterdir() if (image.is_file() and is_image_file(image))])
    for class_name in class_names:
        if class_name is max(weighted_cosine_similarity_scores, key=weighted_cosine_similarity_scores.get):
            continue
        elif weighted_cosine_similarity_scores[class_name] < 0.5:  # threshold for considering an image as belonging to a class
            weighted_cosine_similarity_scores.pop(class_name)
    json_tags = json.dumps(weighted_cosine_similarity_scores)
    json_path = str(image_path) + ".json"
    Path(json_path).write_text(json_tags)
    
def is_image_file(file_path):
    return file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']


def get_image_class_name(image_path):
    json_path = str(image_path) + ".json"
    if Path(json_path).exists():
        json_tags = Path(json_path).read_text()
        tags = json.loads(json_tags)
    if tags is not None:
        return max(tags, key=tags.get)  # return the class name with the highest weighted cosine similarity score
    return None

def get_prediction_from_model(image_path):
    if not Path(image_path).is_file():
        raise ValueError(f"Image path '{image_path}' does not exist or is not a file.")
    elif not is_image_file(Path(image_path)):
        print(f"File '{image_path}' is not a supported image format. Skipping prediction.")
        return None
    else:
        try:
            with open(image_path, "rb") as f:
                response = http_requests.post(
                    "http://localhost:8001/predict_one",
                    files={"file": (Path(image_path).name, f, f"image/{Path(image_path).suffix[1:]}")}
                )
            # print(response.json())
            return response.json()
        except Exception as e:
            print(f"Error calling model: {str(e)}")

def get_predictions_plural_from_model(unsorted_folder_path, example_size=20, example=False):
    # TODO: fix this function to get the class names from the model prediction through the api call to the model server
    all_predictions = []
    opened_files = 0
    while True:
        indexF = 0
        response = None
        startBatch = True
        try:
            forModel = list()
            folderNames = [f.name for f in Path(unsorted_folder_path).iterdir() if f.is_dir()]
            foldersOpend = 0
            for file in Path(unsorted_folder_path).iterdir():
                if not file.is_file():
                    if file.is_dir():
                        indexE = 0
                        for image in file.iterdir():
                            if example and indexE >= example_size:
                                break
                            if opened_files % 1000 == 0 and not startBatch:  # limit the number of opened files to avoid hitting the system limit
                                break
                            if indexF != opened_files:
                                indexF += 1
                                continue
                            if not image.is_file():
                                continue
                            if is_image_file(image):
                                with open(image, "rb") as f:
                                    forModel.append((Path(image).name, f, f"image/{Path(image).suffix[1:]}"))
                                    f.close = lambda: None
                                    opened_files += 1
                                    indexF += 1
                                    indexE += 1
                                    startBatch = False
                                    print(f"number of opened files: {opened_files}")
                        foldersOpend += 1
                        if foldersOpend >= len(folderNames):
                            break
                    continue
            # for image in forModel:
            #     with open(image[1].name, "rb") as f:
            #         print(f"Processing file {image[0]}")
            filesBefore = [("files", (img[0], img[1], img[2])) for img in forModel]
            response = http_requests.post(
                "http://localhost:8001/predict_many",
                files=filesBefore
            )
            # print(response.text)
            # print(response.json())
            all_predictions.append(response.json())
            if foldersOpend >= len(folderNames) and opened_files % 1000 != 0:
                break
        except Exception as e:
            print(f"model response: {response.text if response is not None else 'No response'}")
            print(f"Error calling model: {str(e)}")
            print(f"stack trace: {traceback.format_exc()}")
    print(f"Total number of predictions: {len(all_predictions)}")
    print(f"Total number of opened files: {len(all_predictions[len(all_predictions) - 1]) + (len(all_predictions)-1)*1000 if all_predictions else 0}")
    return all_predictions


def create_sorted_images_folder():
    create_folder(str(new_path))
    for folderName in class_names:
        create_folder(f"{new_path}/{folderName}")
        
def move_images_to_sorted_folder(images, old_path, new_path):
    predictions = get_predictions_plural_from_model(str(old_path), example=False)
    indexF = 0
    indexi = 0
    totalPredictions = sum(len(batch) for batch in predictions)
    print(f"predictions length: {len(predictions)}")
    print(f"total predictions: {totalPredictions}")
    for image, folderName in images:
        if is_image_file(image):
            indexi += 1
            if indexi > 1000:
                indexi = 0
                indexF += 1
            if indexF >= len(predictions):
                print(f"No more predictions available for file '{image}'. Skipping.")
                break
            if indexi >= len(predictions[indexF]):
                indexi = 0
                indexF += 1
                # print(f"No more predictions available in batch {indexF} for file '{image}'. Skipping.")
                # continue
            # add_example_image(image, folderName, predictions[indexF][indexi])
            set_image_tags(image, predictions[indexF][indexi])
            most_likely_class_name = get_image_class_name(image)
            if most_likely_class_name is not None:
                move_image(image, f"{new_path}/{most_likely_class_name}")
                move_image(str(image) + ".json", f"{new_path}/{most_likely_class_name}")
            else:
                move_image(image, f"{new_path}/{folderName}")
                move_image(str(image) + ".json", f"{new_path}/{folderName}")
        else:
            print(f"File '{image}' is not a supported image format. Skipping.")
            i-=1

def get_cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude_vec1 = sum(a ** 2 for a in vec1) ** 0.5
    magnitude_vec2 = sum(b ** 2 for b in vec2) ** 0.5
    if magnitude_vec1 == 0 or magnitude_vec2 == 0:
        return 0.0
    return dot_product / (magnitude_vec1 * magnitude_vec2)

def weighted_cosine_similarity(vec, vec_list): #(vec, vec_list): # (vec_list, exampleEmbeddings): # this is here because I am making changes
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # exampleEmbeddings = exampleEmbeddings.to(device)
    # example_norm = torch.nn.functional.normalize(exampleEmbeddings, p=2, dim=1).to(device)
    # embeddings = vec_list.to(device)
    # batch_norm = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    # similarities = batch_norm @ example_norm.T
    # weights = torch.nn.functional.softmax(similarities, dim=1)
    # weighted_similarities = (weights * similarities).sum(dim=1)
    similarities = [get_cosine_similarity(vec, v) for v in vec_list]
    total_similarity = sum(similarities)
    if total_similarity == 0:
        return [0] * len(vec_list)
    weights = [s / total_similarity for s in similarities]
    average_weighted_similarity = total_similarity*sum(weights) / len(vec_list)
    return average_weighted_similarity
    # return weighted_similarities.cpu().tolist()
    # average_similarity = total_similarity / len(vec_list)
    # return average_similarity

# will delete this once connected to the model api
images = list()
if not Path("dataset/").exists():
    old_path = Path("sorted_images/")
    new_path = Path("dataset/")

def list_images_in_folder(folder_path):
    if not Path(folder_path).exists():
        print(f"Folder '{folder_path}' does not exist.")
        exit(42)
    folderNames = [f.name for f in old_path.iterdir() if f.is_dir()]
    lastImageIndexes = {folderName: -1 for folderName in folderNames}
    for file in old_path.iterdir():
        if not file.is_file():
            indexNO = 0
            if file.is_dir():
                # if indexNO > folderNames.index(folderNames[len(folderNames) - 1]):
                #     break
                currentFolderName = file.name
                # set last index to the last index of the previous folder
                lastImageIndexes[currentFolderName] = lastImageIndexes[folderNames[folderNames.index(currentFolderName) - 1]]
                # indexF = 0
                for image in file.iterdir():
                    # if indexF > 20:
                    #     break
                    if not image.is_file():
                        continue
                    if is_image_file(image):
                        images.append((image, currentFolderName))
                        lastImageIndexes[currentFolderName] += 1
                        # indexF += 1
                # indexNO += 1
            continue

def sort_images(folder_path):
    list_images_in_folder(folder_path)
    new_folder_path = f"{Path(folder_path).parent}/sorted_images/"
    move_images_to_sorted_folder(images, folder_path, new_folder_path)
    delete_folder(folder_path)

# get_predictions_plural_from_model(str(old_path))

# list_images_in_folder(str(old_path))
# move_images_to_sorted_folder(images, str(old_path), str(new_path))
# save_class_names_to_json(class_names)
# delete_folder(str(old_path))






