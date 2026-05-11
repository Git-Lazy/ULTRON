import imageio.v3 as iio
from pathlib import Path
from torchvision.utils import save_image
from torchvision import transforms

from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader

transformer = transforms.Compose(
    [
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ]
)

dataset = ImageFolder(root="dataset/", transform=transformer)
loader = DataLoader(dataset, batch_size=32, shuffle=True)

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
                images.append(iio.imread(image))
                lastImageIndexes[currentFolderName] += 1
        continue
    images.append(iio.imread(file))
for idx, image in enumerate(images):
    if not Path(f"./dataset_images/").exists():
        Path("./dataset_images/").mkdir(parents=True, exist_ok=True)
        for folderName in folderNames:
            if not Path(f"./dataset_images/{folderName}").exists():
                Path(f"./dataset_images/{folderName}").mkdir(parents=True, exist_ok=True)
    for folderName in folderNames:
        if idx <= lastImageIndexes[folderName]:
            save_image(transforms.ToTensor()(image), f"dataset_images/{folderName}/image_{idx}.png")


# delete the original dataset
for file in Path("dataset/").iterdir():
    if not file.is_file():
        if file.is_dir():
            for image in file.iterdir():
                if not image.is_file():
                    continue
                image.unlink()
            file.rmdir()
        continue
    file.unlink()
Path("dataset/").rmdir()