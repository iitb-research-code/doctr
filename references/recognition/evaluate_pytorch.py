# Copyright (C) 2021-2023, Mindee.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import os

os.environ["USE_TORCH"] = "1"

import multiprocessing as mp
import time
import hashlib
from pathlib import Path

import torch
from torch.utils.data import DataLoader, SequentialSampler
from torchvision.transforms import Normalize
from tqdm import tqdm

import pandas as pd

from doctr import datasets
from doctr import transforms as T
from doctr.datasets import VOCABS
from doctr.models import recognition
from doctr.utils.metrics import TextMatch

from torchvision.transforms import (
    Compose,
    GaussianBlur,
    Normalize,
    RandomGrayscale,
    RandomPerspective,
    #RandomPhotometricDistort,
)
from tqdm.auto import tqdm

from doctr import transforms as T
from doctr.datasets import VOCABS, RecognitionDataset, WordGenerator
from doctr.models import login_to_hub, push_to_hf_hub, recognition
from doctr.utils.metrics import TextMatch


@torch.inference_mode()
def evaluate(model, file_name, val_loader, batch_transforms, val_metric, output_path, amp=False):
    # Model in eval mode
    model.eval()
    # Reset val metric
    val_metric.reset()
    # Validation loop
    val_loss, batch_cnt = 0, 0
    
    gts = []
    predictions = []
    names = []
    for images, targets, name in tqdm(val_loader):
        try:
            if torch.cuda.is_available():
                images = images.cuda()
            images = batch_transforms(images)
            if amp:
                with torch.cuda.amp.autocast():
                    out = model(images, None, return_preds=True)
            else:
                out = model(images, None, return_preds=True)
            # Compute metric
            if len(out["preds"]):
                words, _ = zip(*out["preds"])
            else:
                words = []
            val_metric.update(targets, words)
            gts += targets
            predictions += words
            names += name
            # val_loss += out["loss"].item()
            batch_cnt += 1
        except ValueError:
            print(f"unexpected symbol/s in targets:\n{targets} \n--> skip batch")
            continue
    
    df = pd.DataFrame(list(zip(names,gts, predictions)), columns=['names', 'gt', 'pred'])
    df.to_csv(f'{output_path}{file_name}.csv', index=False, header=False, sep='\t')
    
        
    val_loss /= batch_cnt
    result = val_metric.summary()
    return val_loss, result["raw"], result["unicase"]


def main(args):
    print(args)

    torch.backends.cudnn.benchmark = True

    if not isinstance(args.workers, int):
        args.workers = min(16, mp.cpu_count())

    # Load doctr model
    model = recognition.__dict__[args.arch](
        pretrained=True if args.resume is None else False,
        input_shape=(3, args.input_size, 4 * args.input_size),
        vocab=VOCABS[args.vocab],
    ).eval()

    # Resume weights
    if isinstance(args.resume, str):
        print(f"Resuming {args.resume}")
        checkpoint = torch.load(args.resume, map_location="cpu")
        model.load_state_dict(checkpoint)

    st = time.time()
    
    base_path = Path(args.dataset)
    print(base_path.joinpath("test.json").is_file())
    parts = (
        [base_path]
        if base_path.joinpath("test.json").is_file()
        else [base_path.joinpath(sub) for sub in os.listdir(base_path)]
    )
    
    
    with open(parts[0].joinpath("test.json"), "rb") as f:
        train_hash = hashlib.sha256(f.read()).hexdigest()

    test_set = RecognitionDataset(
        parts[0].joinpath("images"),
        parts[0].joinpath("test.json"),
        img_transforms=Compose(
            [
                T.Resize((args.input_size, 4 * args.input_size), preserve_aspect_ratio=True),
                # Augmentations
                T.RandomApply(T.ColorInversion(), 0.1),
                RandomGrayscale(p=0.1),
                #RandomPhotometricDistort(p=0.1),
                T.RandomApply(T.RandomShadow(), p=0.4),
                T.RandomApply(T.GaussianNoise(mean=0, std=0.1), 0.1),
                T.RandomApply(GaussianBlur(3), 0.3),
                RandomPerspective(distortion_scale=0.2, p=0.3),
            ]
        ),
    )
    if len(parts) > 1:
        for subfolder in parts[1:]:
            train_set.merge_dataset(
                RecognitionDataset(subfolder.joinpath("images"), subfolder.joinpath("test.json"))
            )
    

    test_loader = DataLoader(
        test_set,
        batch_size=args.batch_size,
        drop_last=False,
        num_workers=args.workers,
        sampler=SequentialSampler(test_set),
        pin_memory=torch.cuda.is_available(),
        collate_fn=test_set.collate_fn,
    )
    print(f"Test set loaded in {time.time() - st:.4}s ({len(test_set)} samples in " f"{len(test_loader)} batches)")

    mean, std = model.cfg["mean"], model.cfg["std"]
    batch_transforms = Normalize(mean=mean, std=std)

    # Metrics
    val_metric = TextMatch()

    # GPU
    if isinstance(args.device, int):
        if not torch.cuda.is_available():
            raise AssertionError("PyTorch cannot access your GPU. Please investigate!")
        if args.device >= torch.cuda.device_count():
            raise ValueError("Invalid device index")
    # Silent default switch to GPU if available
    elif torch.cuda.is_available():
        args.device = 0
    else:
        print("No accessible GPU, targe device set to CPU.")
    if torch.cuda.is_available():
        torch.cuda.set_device(args.device)
        model = model.cuda()
        
    output_path = f'/raid/ganesh/badri/RECOGNITION/DOCTR/results/{args.arch}/' + args.vocab + '/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    print("Running evaluation")
    val_loss, exact_match, partial_match = evaluate(model, args.name, test_loader, batch_transforms, val_metric, output_path, amp=args.amp)
    print(f"Validation loss: {val_loss:.6} (Exact: {exact_match:.2%} | Partial: {partial_match:.2%})")


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="docTR evaluation script for text recognition (PyTorch)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("arch", type=str, help="text-recognition model to evaluate")
    parser.add_argument("--vocab", type=str, default="french", help="Vocab to be used for evaluation")
    parser.add_argument("--dataset", type=str, default="FUNSD", help="Dataset to evaluate on")
    parser.add_argument("--name", type=str, default="crnn", help="Dataset to evaluate on")
    parser.add_argument("--device", default=None, type=int, help="device")
    parser.add_argument("-b", "--batch_size", type=int, default=1, help="batch size for evaluation")
    parser.add_argument("--input_size", type=int, default=32, help="input size H for the model, W = 4*H")
    parser.add_argument("-j", "--workers", type=int, default=None, help="number of workers used for dataloading")
    parser.add_argument(
        "--only_regular", dest="regular", action="store_true", help="test set contains only regular text"
    )
    parser.add_argument("--resume", type=str, default=None, help="Checkpoint to resume")
    parser.add_argument("--amp", dest="amp", help="Use Automatic Mixed Precision", action="store_true")
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = parse_args()
    main(args)
