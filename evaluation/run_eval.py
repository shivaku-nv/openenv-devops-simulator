
from data.logs_dataset import generate_dataset
from models.log_classifier import classify_log

data = generate_dataset(50)
correct = 0

for d in data:
    if classify_log(d["text"]) == d["label"]:
        correct += 1

print("Accuracy:", correct/len(data))
