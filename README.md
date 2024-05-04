# Synthesis DocTR


## Installation

```
1. git clone https://github.com/iitb-research-code/doctr.git
2. cd doctr
3. git checkout synthesis
4. pip install -e .
5. pip install -e .[torch]
6. pip install -e . --upgrade
7. pip install -r references/requirements.txt
8. pip install -r requirements.txt
```

## Dataset Creation/Usage


### Tamil Text Corpus

1. Download the data using the command
```sh
curl https://objectstore.e2enetworks.net/ai4b-public-nlu-nlg/v1-indiccorp/te.txt >> te.txt
``` 
2. Specify the vocabulary as a dictonary element in ```doctr/datasets/vocabs.py```

3. Run the preprocess code in preprocess.py to generate dataset of valid words from the text file.

```sh
python misc_code/preprocess.py --input_path data/corpus/te.txt --output_path data/trial --vocab telugu --sample 0.5 --unique --continue_check
```

4. Download the fonts from [here](https://github.com/iitb-research-code/indic-fonts/tree/main/telugu) whose directory path must be passed during training

## Changes Made

1) Included preprocess.py [Preprocess data], infer.py [To make inference], analyse.py[To get character counts in data]

2) In references/train_pytorch made finding text length general to all os (previously only for linux)

3) In doctr/utils/fonts.py added support for RAQM layout engine (needed for tamil)

4) In doctr/datasets/generator/base.py modified synthesize_text_img function to use RAQM layout engine and made the images centered with padding provided as pixels. 

    The old one provided inconistent placing of text - It was not intensional - It was random inconsistency due to font property - Some fonts where always overflowing the image boundaries more than 80%, some fonts where always perfectly fit
    
    Rather than having the random offest due to font's property it would be better to have a centered image for every font and then randomly offset it (yet to be implemented) so that he offset doesnt overfit to font style.

## Training Details

```
python references/recognition/train_pytorch.py crnn_vgg16_bn --train_txt_path TRAIN_TXT_PATH --val_txt_path VAL_TXT_PATH --vocab VOCAB_NAME --name NAME_OF_EXP --epochs 10 --font FONTS_PATH
```

The resulting models is saved in *models* dir in the repository (ensure the directory is is actually present)

## Vocab - Extra

In the vocab_builder directory there is source vocab for bengali, gujarati, gurumukhi, devnagiri(hindi), kannada, malayalam, oriya and telugu.

