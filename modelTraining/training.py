from torch.utils.data import Dataset, DataLoader
from model import Model
import torch
import numpy as np
from torch.nn import functional as F

class TripletDataset(Dataset):
    def __init__(self, data, size, testing=False):
        self.classes = list(data["data"].keys())
        self.data = data["data"]
        self.largness = size
        self.testing = testing

    def __len__(self):
        # number of triplets per epoch — tune this
        return self.largness

    def __getitem__(self, _):
        if self.testing:
            class_1, class_2 = np.random.choice(self.classes, 2, replace=True)
            img_1 = self.data[class_1][np.random.randint(len(self.data[class_1]))]
            img_2 = self.data[class_2][np.random.randint(len(self.data[class_2]))]
            return (
                img_1.clone().float(),
                img_2.clone().float(),
                torch.tensor([class_1, class_2])
            )
        # pick anchor class, then a different negative class
        anchor_class, negative_class = np.random.choice(self.classes, 2, replace=False)

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
        )



def train_two_electric_boggalo(epochs, model, loss_fn, train_path, save_path="model.pth"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("training on ", device)
    model.to(device)
    dataset = TripletDataset(torch.load(train_path), 10000)
    print("dataset loaded")
    dataset_loader = DataLoader(dataset, batch_size=64, shuffle=False, num_workers=4)
    testSet = TripletDataset(torch.load("trainingData/convertedDatasetTest.pkl"), 1000, testing=True)
    test_loader = DataLoader(testSet, batch_size=64, shuffle=False, num_workers=4)
    print("dataloader created")
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn.to(device)
    for epoch in range(epochs):
        total_loss = 0
        similarTrue = 0
        looseSimilarTrue = 0
        opposingTrue = 0
        looseOpposingTrue = 0
        model.train()
        for batch in dataset_loader:
            anchor, positive, negative = batch
            anchor, positive, negative = anchor.to(device), positive.to(device), negative.to(device)

            optimizer.zero_grad()
            em_anchor = model(anchor)
            em_positive = model(positive)
            em_negative = model(negative)
            loss = loss_fn(em_anchor, em_positive, em_negative)
            similarityTrue = F.cosine_similarity(em_anchor, em_positive, dim=1)
            similarityFalse1 = F.cosine_similarity(em_anchor, em_negative, dim=1)

            similarTrue += torch.sum(similarityTrue > 0.7).item()
            looseSimilarTrue += torch.sum(similarityTrue > 0.4).item()
            opposingTrue += torch.sum(similarityFalse1 < 0.4).item()
            looseOpposingTrue += torch.sum(similarityFalse1 < 0.7).item()

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


        print(f"epoch {epoch} avg loss {total_loss / 10000:.4f}")
        print("Training Metrics:")
        print(f"    similarTrue {similarTrue / 10000:.4f}")
        print(f"    looseSimilarTrue {looseSimilarTrue / 10000:.4f}")
        print(f"    opposingTrue {opposingTrue / 10000:.4f}")
        print(f"    looseOpposingTrue {looseOpposingTrue / 10000:.4f}")
        print("Testing Metrics:")
        print(f"    accuracy {total_correct / 1000:.4f}")
        print(f"    accuracy high {total_correct_high / 1000:.4f}")
        print(f"    avg similarity match {total_similarity_match / total_similar:.4f}")
        print(f"    avg similarity diff {total_similarity_diff / total_opposing:.4f}")
        print()
        torch.save(model.state_dict(), save_path)

if __name__ == "__main__":
    model = Model()
    model.load_state_dict(torch.load("models/72_77_Accuracy.pth"))
    loss_fn = torch.nn.TripletMarginLoss(margin=1)
    train_two_electric_boggalo(100, model, loss_fn, "trainingData/convertedDataset.pkl", save_path="trash_model.pth")