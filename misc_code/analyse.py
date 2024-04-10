from collections import Counter
import csv
from doctr.datasets import VOCABS

train = "data/large_data/train.txt"
val = "data/large_data/val.txt"

with open(train,encoding="utf-8") as f:
    train = f.read()
with open(val,encoding="utf-8") as f:
    val = f.read()

train_counts = Counter(train)
val_counts = Counter(val)

with open('data/large_data/report.csv','w') as f:
    writer = csv.writer(f)
    writer.writerow(["Character","Train Count","Val Count"])

    for char in VOCABS['tamil']:
        tc,vc = 0,0
        if char in train_counts:
            tc = train_counts[char]
        if char in val_counts:
            vc = val_counts[char]
        writer.writerow((char,tc,vc))
