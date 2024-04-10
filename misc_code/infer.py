import os
import csv
import torch
import argparse

from doctr.io import DocumentFile
from doctr.models import crnn_vgg16_bn
from doctr.models.predictor import OCRPredictor
from doctr.models.detection.predictor import DetectionPredictor
from doctr.models.recognition.predictor import RecognitionPredictor
from doctr.models.preprocessor import PreProcessor
from doctr.datasets.vocabs import VOCABS

# If only CPU is there use cpu instead of cuda
os.environ["USE_TORCH"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"



def get_result(args):
    input_files = [os.path.join(args.input_file,i) for i in os.listdir(args.input_file)]
    doc = DocumentFile.from_images(input_files)

    #Recognition model
    reco_model = crnn_vgg16_bn(pretrained=False, vocab=VOCABS[args.vocab])
    reco_param = torch.load(args.rec_model, map_location="cuda")
    reco_model.load_state_dict(reco_param)
    reco_predictor = RecognitionPredictor(PreProcessor((32, 128), preserve_aspect_ratio=True, batch_size=1, mean=(0.694, 0.695, 0.693), std=(0.299, 0.296, 0.301)), reco_model)        

    predictor = reco_predictor

    result = predictor(doc)
    for i in range(len(input_files)):
        result[i] = result[i] + (input_files[i],)

    with open(args.output, 'w',encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Prediction","Confidence","Source"])
        writer.writerows(result)
    
    
def parse_args():
    parser = argparse.ArgumentParser(description="Documents OCR Input Arguments", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_file", type=str, default=None, help="path to the input folder")
    parser.add_argument("-r", "--rec_model", type=str, default=None, help="Recognition Model Directory")
    parser.add_argument("-v", "--vocab", type=str, default=None, help="Vocabulary of the language")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output file name")
    
    args = parser.parse_args()
    return args
            
if __name__ == "__main__":
    args = parse_args()
    get_result(args)

