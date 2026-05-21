import numpy
from model import Model
import torch
from PIL import Image
import os
from imageConverter import transform
import shutil

class ImageDataset(torch.utils.data.Dataset):
    def __init__(self, rootDirectory, imageDirs):
        self.data = torch.zeros((len(imageDirs), 3, 128, 128))
        self.names = imageDirs
        for i, image in enumerate(imageDirs):
            imagePath = os.path.join(rootDirectory, image)
            image = Image.open(imagePath).convert("RGB")
            image = transform(image)
            self.data[i] = image

    def __getitem__(self, index):
        return self.data[index], self.names[index]

    def __len__(self):
        return len(self.data)


def filterDirectory(directory, outputDirectory, model):
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    with torch.no_grad():
        exampleImages = os.listdir(os.path.join(directory, "examples"))
        exampleEmbeddings = torch.zeros((len(exampleImages), 256))
        for i, image in enumerate(exampleImages):
            imagePath = os.path.join(directory, "examples",  image)
            image = Image.open(imagePath).convert("RGB")
            image = transform(image)
            input_tensor = torch.zeros(1, 3, 128, 128)
            input_tensor[0] = image
            exampleEmbeddings[i] = model(input_tensor)[0]
        example_norm = torch.nn.functional.normalize(exampleEmbeddings, p=2, dim=1).to(device)
        #example_avg = exampleEmbeddings.mean(dim=0).to(device)
        model.to(device)
        images = os.listdir(directory)
        images.remove("examples")
        dataset = ImageDataset(directory, images)
        dataset_loader = torch.utils.data.DataLoader(dataset, batch_size=64, shuffle=False, num_workers=4)
        os.makedirs(outputDirectory, exist_ok=True)
        for batch, name in dataset_loader:
            batch = batch.to(device)
            embeddings = model(batch)
            #similarities = torch.nn.functional.cosine_similarity(embeddings, example_avg, dim=1)

            batch_norm = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            similarities = batch_norm @ example_norm.T
            weights = torch.nn.functional.softmax(similarities, dim=1)
            weighted_similarities = (weights * similarities).sum(dim=1)
            # weighted_similarities = similarities.mean(dim=1)
            for i, similarity in enumerate(weighted_similarities):
                old_path = str(os.path.join(directory, name[i]))
                sim_str = f"{similarity.item():.8f}"
                new_filename = f"{sim_str}_.jpg"  # e.g. "0.8342_original_name.jpg"
                shutil.move(old_path, os.path.join(outputDirectory, new_filename))
            print(f"Processed {i+1} images")



def filterImages(classes_dir, source_dir, output_dir):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = Model()
    model.load_state_dict(torch.load("new_data_new_new.pth"))
    classes = os.listdir(classes_dir)
    classExamples = {}
    os.makedirs(output_dir, exist_ok=True)
    for class_name in classes:
        os.makedirs(os.path.join(output_dir, class_name), exist_ok=True)
        class_path = os.path.join(classes_dir, class_name)
        images = os.listdir(class_path)[:50]
        classExamples[class_name] = torch.zeros(50, 256)
        for image_name in images:
            image_path = os.path.join(class_path, image_name)
            image = Image.open(image_path).convert("RGB")
            image = transform(image)
            input_tensor = torch.zeros(1, 3, 128, 128)
            input_tensor[0] = image
            embedding = model(input_tensor)[0]
            classExamples[class_name][images.index(image_name)] = embedding
        classExamples[class_name].to(device)
        classExamples[class_name] = torch.nn.functional.normalize(classExamples[class_name], p=2, dim=1).to(device)
    unclassified_images = os.listdir(source_dir)
    image_dataset = ImageDataset(source_dir, unclassified_images)
    image_loader = torch.utils.data.DataLoader(image_dataset, batch_size=64, shuffle=False, num_workers=4)
    model.to(device)
    for batch, name in image_loader:
        batch = batch.to(device)
        embeddings = model(batch)
        batch_norm = torch.nn.functional.normalize(embeddings, p=2, dim=1).to(device)
        by_class_similarities = {}
        for i, class_name in enumerate(classes):
            similarities = batch_norm @ classExamples[class_name].T
            weights = torch.nn.functional.softmax(similarities, dim=1)
            weighted_similarities = (weights * similarities).sum(dim=1)
            #weighted_similarities = similarities.mean(dim=1)
            by_class_similarities[class_name] = weighted_similarities
        for i in range(len(name)):
            predicted_class = ""
            highest_similarity = -100
            for class_name, similarities in by_class_similarities.items():
                if similarities[i] > highest_similarity:
                    highest_similarity = similarities[i]
                    predicted_class = class_name
            class_output_dir = os.path.join(output_dir, predicted_class)
            shutil.move(os.path.join(source_dir, name[i]), os.path.join(class_output_dir,  f"{highest_similarity:.4f}_{name[i]}"))



if __name__ == "__main__":
    print("Starting filtering...")
    model = Model()
    model.load_state_dict(torch.load("new_data_new_new.pth"))
    # filterDirectory("trainingData/Glacier/actuallySorted", "trainingData/Glacier/actuallySortedForReal", model)
    filterImages("trainingData/recovered/seg_train/seg_train", "trainingData/recovered/seg_pred/seg_pred", "trainingData/sortedData")