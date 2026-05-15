import torch
from torch.nn import functional as F
from model import Model



# def showExample():
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     model = Model().to(device)
#     model.load_state_dict(torch.load("models/72_77_Accuracy.pth", map_location=device))
#     model.eval()
#     dataset = torch.load("trainingData/demoDataset.pkl")
#     cloudyExamples = dataset["data"][0][:5].to(device)
#     cloudy_dataloader = torch.utils.data.DataLoader(dataset["data"][0][5:], batch_size=64, shuffle=False)
#     desertExamples = dataset["data"][1][:5].to(device)
#     desert_dataloader = torch.utils.data.DataLoader(dataset["data"][1][5:], batch_size=64, shuffle=False)
#     greenExamples = dataset["data"][2][:5].to(device)
#     green_dataloader = torch.utils.data.DataLoader(dataset["data"][2][5:], batch_size=64, shuffle=False)
#     waterExamples = dataset["data"][3][:5].to(device)
#     water_dataloader = torch.utils.data.DataLoader(dataset["data"][3][5:], batch_size=64, shuffle=False)
#     with torch.no_grad():
#         cloudy_em = model(cloudyExamples)
#         desert_em = model(desertExamples)
#         green_em = model(greenExamples)
#         water_em = model(waterExamples)
#         exampleEmbeddings = (cloudy_em, desert_em, green_em, water_em)
#         total = 0
#         correct_weighted = 0
#         correct_mean = 0
#
#         for batch in cloudy_dataloader:
#             batch = batch.to(device)
#             total += len(batch)
#             embeddings = model(batch)
#             similarities_avg_all = torch.zeros((len(batch), len(exampleEmbeddings))).to(device)
#             similarities_weighted_all = torch.zeros((len(batch), len(exampleEmbeddings))).to(device)
#             for i, example in enumerate(exampleEmbeddings):
#                 norm_embeddings = F.normalize(embeddings, dim=1)
#                 norm_examples = F.normalize(example, dim=1)
#                 similarities = norm_embeddings @ norm_examples.T
#
#                 avg_similarities = similarities.mean(dim=1)
#                 weights = F.softmax(similarities, dim=1)
#                 weighted_similarities = (weights * similarities).sum(dim=1)
#
#                 similarities_avg_all[:, i] = avg_similarities
#                 similarities_weighted_all[:, i] = weighted_similarities
#             avg_predictions = torch.argmax(similarities_avg_all, dim=1)
#             weighted_predictions = torch.argmax(similarities_weighted_all, dim=1)
#
#             avg_correct = avg_predictions == 0
#             weighted_correct = weighted_predictions == 0
#
#             correct_mean += avg_correct.sum()
#             correct_weighted += weighted_correct.sum()
#
#         for batch in desert_dataloader:
#             batch = batch.to(device)
#             total += len(batch)
#             embeddings = model(batch)
#             similarities_avg_all = torch.zeros((len(batch), len(exampleEmbeddings))).to(device)
#             similarities_weighted_all = torch.zeros((len(batch), len(exampleEmbeddings))).to(device)
#             for i, example in enumerate(exampleEmbeddings):
#                 norm_embeddings = F.normalize(embeddings, dim=1)
#                 norm_examples = F.normalize(example, dim=1)
#                 similarities = norm_embeddings @ norm_examples.T
#
#                 avg_similarities = similarities.mean(dim=1)
#                 weights = F.softmax(similarities, dim=1)
#                 weighted_similarities = (weights * similarities).sum(dim=1)
#
#                 similarities_avg_all[:, i] = avg_similarities
#                 similarities_weighted_all[:, i] = weighted_similarities
#             avg_predictions = torch.argmax(similarities_avg_all, dim=1)
#             weighted_predictions = torch.argmax(similarities_weighted_all, dim=1)
#
#             avg_correct = avg_predictions == 1
#             weighted_correct = weighted_predictions == 1
#
#             correct_mean += avg_correct.sum()
#             correct_weighted += weighted_correct.sum()
#
#         for batch in green_dataloader:
#             batch = batch.to(device)
#             total += len(batch)
#             embeddings = model(batch)
#             similarities_avg_all = torch.zeros((len(batch), len(exampleEmbeddings))).to(device)
#             similarities_weighted_all = torch.zeros((len(batch), len(exampleEmbeddings))).to(device)
#             for i, example in enumerate(exampleEmbeddings):
#                 norm_embeddings = F.normalize(embeddings, dim=1)
#                 norm_examples = F.normalize(example, dim=1)
#                 similarities = norm_embeddings @ norm_examples.T
#
#                 avg_similarities = similarities.mean(dim=1)
#                 weights = F.softmax(similarities, dim=1)
#                 weighted_similarities = (weights * similarities).sum(dim=1)
#
#                 similarities_avg_all[:, i] = avg_similarities
#                 similarities_weighted_all[:, i] = weighted_similarities
#             avg_predictions = torch.argmax(similarities_avg_all, dim=1)
#             weighted_predictions = torch.argmax(similarities_weighted_all, dim=1)
#
#             avg_correct = avg_predictions == 2
#             weighted_correct = weighted_predictions == 2
#
#             correct_mean += avg_correct.sum()
#             correct_weighted += weighted_correct.sum()
#
#         for batch in water_dataloader:
#             batch = batch.to(device)
#             total += len(batch)
#             embeddings = model(batch)
#             similarities_avg_all = torch.zeros((len(batch), len(exampleEmbeddings))).to(device)
#             similarities_weighted_all = torch.zeros((len(batch), len(exampleEmbeddings))).to(device)
#             for i, example in enumerate(exampleEmbeddings):
#                 norm_embeddings = F.normalize(embeddings, dim=1)
#                 norm_examples = F.normalize(example, dim=1)
#                 similarities = norm_embeddings @ norm_examples.T
#
#                 avg_similarities = similarities.mean(dim=1)
#                 weights = F.softmax(similarities, dim=1)
#                 weighted_similarities = (weights * similarities).sum(dim=1)
#
#                 similarities_avg_all[:, i] = avg_similarities
#                 similarities_weighted_all[:, i] = weighted_similarities
#             avg_predictions = torch.argmax(similarities_avg_all, dim=1)
#             weighted_predictions = torch.argmax(similarities_weighted_all, dim=1)
#
#             avg_correct = avg_predictions == 3
#             weighted_correct = weighted_predictions == 3
#
#             correct_mean += avg_correct.sum()
#             correct_weighted += weighted_correct.sum()
#         print(f"Accuracy Mean: {correct_mean / total:.4f}: ")
#         print(f"Accuracy Weighted: {correct_weighted / total:.4f}")


def showExample():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = Model().to(device)
    model.load_state_dict(torch.load("models/high_gap_model_83_40.pth", map_location=device))
    model.eval()
    dataset = torch.load("trainingData/demoDataset.pkl")

    n_examples = 5
    class_keys = [0, 1, 2, 3]
    class_names = ["cloudy", "desert", "green", "water"]

    example_embeddings = []
    dataloaders = []

    with torch.no_grad():
        for key in class_keys:
            examples = dataset["data"][key][:n_examples].to(device)
            example_embeddings.append(model(examples))
            rest = dataset["data"][key][n_examples:]
            dataloaders.append(torch.utils.data.DataLoader(rest, batch_size=64, shuffle=False))

        total = 0
        correct_mean = 0
        correct_weighted = 0
        total_similar_similarity = 0
        total_similar_count = 0
        total_dissimilar_similarity = 0
        total_dissimilar_count = 0

        for true_class, dataloader in enumerate(dataloaders):
            for batch in dataloader:
                batch = batch.to(device)
                total += len(batch)
                embeddings = model(batch)
                norm_embeddings = F.normalize(embeddings, dim=1)

                similarities_avg_all = torch.zeros((len(batch), len(example_embeddings))).to(device)
                similarities_weighted_all = torch.zeros((len(batch), len(example_embeddings))).to(device)

                for i, example in enumerate(example_embeddings):
                    norm_examples = F.normalize(example, dim=1)
                    similarities = norm_embeddings @ norm_examples.T  # (batch, n_examples)

                    avg_similarities = similarities.mean(dim=1)
                    weights = F.softmax(similarities, dim=1)
                    weighted_similarities = (weights * similarities).sum(dim=1)

                    similarities_avg_all[:, i] = avg_similarities
                    similarities_weighted_all[:, i] = weighted_similarities

                    # track cosine similarity stats
                    avg_sim_per_sample = similarities.mean(dim=1)
                    if i == true_class:
                        total_similar_similarity += avg_sim_per_sample.sum().item()
                        total_similar_count += len(batch)
                    else:
                        total_dissimilar_similarity += avg_sim_per_sample.sum().item()
                        total_dissimilar_count += len(batch)

                avg_predictions = torch.argmax(similarities_avg_all, dim=1)
                weighted_predictions = torch.argmax(similarities_weighted_all, dim=1)

                correct_mean += (avg_predictions == true_class).sum().item()
                correct_weighted += (weighted_predictions == true_class).sum().item()

        print(f"Accuracy Mean:     {correct_mean / total:.4f}")
        print(f"Accuracy Weighted: {correct_weighted / total:.4f}")
        print(f"Avg similarity (same class):  {total_similar_similarity / total_similar_count:.4f}")
        print(f"Avg similarity (diff class):  {total_dissimilar_similarity / total_dissimilar_count:.4f}")
        print(f"Separation gap: {(total_similar_similarity / total_similar_count) - (total_dissimilar_similarity / total_dissimilar_count):.4f}")



showExample()