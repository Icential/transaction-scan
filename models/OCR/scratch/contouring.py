import cv2
import torch
import matplotlib.pyplot as plt
from torch import nn
from safetensors.torch import load_model
import time

start_time = time.time()

# ### Image Processing
sample = cv2.imread("data/digits/389.png")
sample = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(sample, 125, 255, cv2.THRESH_BINARY_INV)


# ### Contouring

# dilation parameter; bigger tuple = smaller rectangle
rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))

# apply dilation to the thresholded monochrome image
dilation = cv2.dilate(thresh, rect_kernel, iterations=1)

# find contours and rectangles
contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

copy = sample.copy()

crops = []
bboxs = []
for cnt in contours:
    # get coordinates of contours
    x, y, w, h = cv2.boundingRect(cnt)

    # create crops per contour
    crop = thresh[y:y+h, x:x+w]

    crops.append(crop)
    bboxs.append((x, y, w , h))


# ### Model Insertion
device = "cuda" if torch.cuda.is_available() else "cpu"


class TinyVGG(nn.Module):

    def __init__(self):
        super().__init__()

        self.block_1 = nn.Sequential(
            nn.Conv2d(1, 10, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(10, 10, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

        self.block_2 = nn.Sequential(
            nn.Conv2d(10, 10, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(10, 10, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(10*7*7, 10+1) # 7 * 7 because maxpool has been done twice which divides the shape of image by 2 twice
        )

    def forward(self, x):
        x = self.block_1(x)
        x = self.block_2(x)
        x = self.classifier(x)
        return x

model = TinyVGG().to(device)
load_model(model, "tinyvgg.safetensors")


for i in range(len(crops)):

    # Resizing
    linear_resize = cv2.resize(crops[i], (28, 28), cv2.INTER_LINEAR)

    pic = torch.from_numpy(linear_resize).unsqueeze(dim=0).unsqueeze(dim=0).type(torch.float32).to(device)

    model.eval()
    with torch.inference_mode():
        results = model(pic)
        pred = results.argmax(dim=1)
        conf = torch.softmax(results, dim=1)[0][pred] * 100
        digit = str(pred.item())

    cv2.rectangle(copy, (bboxs[i][0], bboxs[i][1]), (bboxs[i][0] + bboxs[i][2], bboxs[i][1] + bboxs[i][3]), (0, 255, 0), 2)
    cv2.putText(copy, digit, (bboxs[i][0], bboxs[i][1]-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)

print(f"\nTime Elapsed: {time.time() - start_time}s")

plt.imshow(copy, cmap="gray")
plt.show()