
import random

DATA = [
("No space left on device","disk_full"),
("Out of memory error","memory_leak"),
("Segmentation fault","crash"),
("Connection timeout","network_issue")
]

def generate_dataset(n=100):
    return [{"text":t,"label":l} for t,l in (random.choice(DATA) for _ in range(n))]
