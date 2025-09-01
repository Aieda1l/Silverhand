import os
from ultralytics import YOLO

# load a nano model
model = YOLO("yolo11n.pt")
results = model.train(data='dataset/data.yaml', epochs=100)