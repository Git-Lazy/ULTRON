from contextlib import nullcontext

from torch.utils.data import Dataset, DataLoader
from model import Model
import torch
import numpy as np
from torch.nn import functional as F


distributionSimilar = None
distributionOpposing = None

useCount = 0



class TripletDataset(Dataset):
    def __init__(self, data, size, testing=False):
        self.classes = list(data["data"].keys())
        print(self.classes)
        self.data = data["data"]
        self.largness = size
        self.testing = testing
        self.switchState = False

    def __len__(self):
        # number of triplets per epoch — tune this
        return self.largness

    def __getitem__(self, _):
        if self.testing:
            same_class = np.random.random() > 0.5
            if same_class:
                class_1 = np.random.choice(self.classes)
                class_2 = class_1
            else:
                class_1, class_2 = np.random.choice(self.classes, 2, replace=False)

            img_1 = self.data[class_1][np.random.randint(len(self.data[class_1]))]
            img_2 = self.data[class_2][np.random.randint(len(self.data[class_2]))]
            return (
                img_1.clone().float(),
                img_2.clone().float(),
                torch.tensor([class_1, class_2])
            )


        anchor_class, negative_class = None, None
        # pick anchor class, then a different negative class
        if distributionSimilar is None:
            anchor_class, negative_class = np.random.choice(self.classes, 2, replace=False)
        elif self.switchState:
            anchor_class = torch.multinomial(distributionSimilar, 1)[0].item()
            negative_class = np.random.choice(self.classes, 1)[0]
            while negative_class == anchor_class:
                negative_class = np.random.choice(self.classes, 1)[0]
        else:
            idx_flat = torch.multinomial(distributionOpposing.flatten(), 1)[0].item()
            anchor_class = idx_flat // len(self.classes)
            negative_class = idx_flat % len(self.classes)
            while negative_class == anchor_class:
                idx_flat = torch.multinomial(distributionOpposing.flatten(), 1)[0].item()
                anchor_class = idx_flat // len(self.classes)
                negative_class = idx_flat % len(self.classes)

        self.switchState = not self.switchState

        class_data = self.data[anchor_class]
        n = len(class_data)

        # pick two distinct samples from anchor class
        idx_a, idx_p = np.random.choice(n, 2, replace=False)

        anchor   = class_data[idx_a]
        positive = class_data[idx_p]
        negative = self.data[negative_class][np.random.randint(len(self.data[negative_class]))]

        return (
            anchor.clone().float(),
            positive.clone().float(),
            negative.clone().float(),
            torch.tensor([anchor_class, negative_class])
        )





def train_two_electric_boggalo(epochs, model, loss_fn, train_path, test_path, save_path="model.pth"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("training on ", device)
    model.to(device)
    dataset = TripletDataset(torch.load(train_path), 10000)
    num_classes = len(dataset.classes)
    print("dataset loaded")
    dataset_loader = DataLoader(dataset, batch_size=64, shuffle=False, num_workers=0)
    testSet = TripletDataset(torch.load(test_path), 1000, testing=True)
    test_loader = DataLoader(testSet, batch_size=64, shuffle=False, num_workers=4)
    print("dataloader created")
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    loss_fn.to(device)
    print("optimizer created")
    global distributionSimilar, distributionOpposing
    for epoch in range(epochs):
        total_loss = 0
        avgSimilarityTrue = 0
        avgSimilarityFalse = 0
        total_correct_similar = 0
        total_correct_opposing = 0
        count_similar_per_class = torch.zeros(num_classes).to(device)
        count_similar_correct_per_class = torch.zeros(num_classes).to(device)
        count_opposing_per_class = torch.zeros((num_classes, num_classes)).to(device)
        count_opposing_correct_per_class = torch.zeros((num_classes, num_classes)).to(device)
        model.train()
        for batch in dataset_loader:
            anchor, positive, negative, selected_classes = batch
            anchor, positive, negative, selected_classes = anchor.to(device), positive.to(device), negative.to(device), selected_classes.to(device)

            optimizer.zero_grad()
            em_anchor = model(anchor)
            em_positive = model(positive)
            em_negative = model(negative)
            loss = loss_fn(em_anchor, em_positive, em_negative)
            similarityTrue = F.cosine_similarity(em_anchor, em_positive, dim=1)
            similarityFalse1 = F.cosine_similarity(em_anchor, em_negative, dim=1)

            avgSimilarityTrue += similarityTrue.sum().item()
            avgSimilarityFalse += similarityFalse1.sum().item()

            predicted_similar = similarityTrue > 0.75
            predicted_opposing = similarityFalse1 < 0.75

            count_similar_per_class += torch.bincount(selected_classes[:, 0], minlength=num_classes).float()
            for i in range(len(selected_classes)):
                count_opposing_per_class[selected_classes[i, 0], selected_classes[i, 1]] += 1

            for i in range(len(predicted_similar)):
                if predicted_similar[i].item() == 1:
                    count_similar_correct_per_class[selected_classes[i, 0]] += 1
                if predicted_opposing[i].item() == 1:
                    count_opposing_correct_per_class[selected_classes[i, 0], selected_classes[i, 1]] += 1

            total_correct_similar += predicted_similar.sum().item()
            total_correct_opposing += predicted_opposing.sum().item()

            loss.backward()
            optimizer.step()

            total_loss += loss.item()
        total_correct = 0
        total_correct_high = 0
        total_similarity_match = 0
        total_similar = 0
        total_similarity_diff = 0
        total_opposing = 0
        model.eval()
        with torch.no_grad():
            for batch in test_loader:
                first, second, classes = batch
                first, second, classes = first.to(device), second.to(device), classes.to(device)
                em_first = model(first)
                em_second = model(second)
                similarity = F.cosine_similarity(em_first, em_second, dim=1)
                isMatch = classes[:, 0] == classes[:, 1]

                predictions = similarity > 0.7
                predictions_high = similarity > 0.8
                total_correct += torch.sum(predictions == isMatch).item()
                total_correct_high += torch.sum(predictions_high == isMatch).item()

                total_similar += torch.sum(isMatch).item()
                total_opposing += torch.sum(~isMatch).item()

                total_similarity_match += torch.sum(similarity[isMatch]).item()
                total_similarity_diff += torch.sum(similarity[~isMatch]).item()

        training_distribution_similar = count_similar_correct_per_class / count_similar_per_class
        training_distribution_opposing = count_opposing_correct_per_class / count_opposing_per_class

        reversed_training_distribution_similar = 1 - training_distribution_similar
        reversed_training_distribution_opposing = 1 - training_distribution_opposing

        reversed_training_distribution_similar = torch.nan_to_num(reversed_training_distribution_similar.cpu(), 0.5)
        reversed_training_distribution_opposing = torch.nan_to_num(reversed_training_distribution_opposing.cpu().fill_diagonal_(0), 0.5)

        probability_distribution_similar = torch.softmax(reversed_training_distribution_similar * 5, dim=0)
        probability_distribution_opposing = torch.softmax(reversed_training_distribution_opposing.flatten() * 5, dim=0).reshape(num_classes, num_classes)


        distributionSimilar = probability_distribution_similar
        distributionOpposing = probability_distribution_opposing
        print(distributionSimilar)
        print(distributionOpposing)

        print(f"epoch {epoch} avg loss {total_loss / 10000:.4f}")
        print("Training Metrics:")
        print(f"    avg similarity true {avgSimilarityTrue / 10000:.4f}")
        print(f"    avg similarity false {avgSimilarityFalse / 10000:.4f}")
        print(f"    avg similarity match {total_correct_similar / 10000:.4f}")
        print(f"    avg similarity diff {total_correct_opposing / 10000:.4f}")
        print("Testing Metrics:")
        print(f"    accuracy {total_correct / 1000:.4f}")
        print(f"    accuracy high {total_correct_high / 1000:.4f}")
        print(f"    avg similarity match {total_similarity_match / total_similar:.4f}")
        print(f"    avg similarity diff {total_similarity_diff / total_opposing:.4f}")
        print(useCount)
        print()
        torch.save(model.state_dict(), save_path)

if __name__ == "__main__":
    model = Model()
    model.load_state_dict(torch.load("models/gen2/model_continued_new_new.pth"))
    loss_fn = torch.nn.TripletMarginLoss(margin=0.2)
    train_two_electric_boggalo(100, model, loss_fn, "trainingData/convertedDataset.pkl", "trainingData/convertedDatasetTest.pkl", save_path="models/gen2/model_continued_new_new.pth")