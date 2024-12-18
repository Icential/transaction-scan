import cv2
import torch
import matplotlib.pyplot as plt
from torch import nn
from safetensors.torch import load_model
from torchvision import transforms
from PIL import Image
import time

device = "cuda" if torch.cuda.is_available() else "cpu"

start_time = time.time()

# ### Image Processing
sample = cv2.imread("data/digits/len50.png")
sample = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(sample, 125, 255, cv2.THRESH_BINARY_INV)


# ### Contouring

# dilation parameter; bigger tuple = smaller rectangle
rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 1))

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
resnet = torch.hub.load('pytorch/vision:v0.10.0', "resnet18", pretrained=False)

transformation = transforms.Compose([
    transforms.Resize((28, 28)),
    transforms.Grayscale(3),
    transforms.ToTensor(),
])

class ModifiedModel(nn.Module):
    def __init__(self, pretrained):
        super().__init__()
        self.pretrained = pretrained
        self.output = nn.Linear(1000, 10) # output only 10 classifications

    def forward(self, x):
        x = self.pretrained(x)
        return self.output(x)

model = ModifiedModel(resnet).to(device)
load_model(model, "resnet_mnist.safetensors")

for i in range(len(crops)):

    # Transforms
    pil_img = Image.fromarray(crops[i])
    post = transformation(pil_img)
    pic = post.unsqueeze(dim=0).to(device)

    model.eval()
    with torch.inference_mode():
        results = model(pic)
        results = results[:, :10]
        pred = results.argmax(dim=1)
        conf = torch.softmax(results, dim=1)[0][pred] * 100
        digit = pred.item()

    cv2.rectangle(copy, (bboxs[i][0], bboxs[i][1]), (bboxs[i][0] + bboxs[i][2], bboxs[i][1] + bboxs[i][3]), (0, 255, 0), 2)
    cv2.putText(copy, f"{digit}", (bboxs[i][0], bboxs[i][1]-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)

print(f"\nTime Elapsed: {time.time() - start_time}s")

plt.imshow(copy, cmap="gray")
plt.show()