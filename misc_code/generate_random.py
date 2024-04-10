import argparse
import random
import os
from PIL import ImageFont, Image, ImageDraw
import cv2
import numpy as np
from doctr.datasets.vocabs import VOCABS
import json

def generate_image(text, font,font_size=32, padding=5, save_path = "test.png", layout = "basic"):
    background_color = (0, 0, 0)
    text_color = (255, 255, 255)

    if layout == "basic":
        font = ImageFont.truetype(font, font_size, layout_engine= ImageFont.Layout.BASIC)
    else:
        font = ImageFont.truetype(font, font_size, layout_engine= ImageFont.Layout.RAQM)
    left, top, right, bottom = font.getbbox(text)
    text_w, text_h = right - left, bottom - top

    img_size = text_h + padding * 2, text_w + padding * 2
    img = Image.new("RGB", img_size[::-1], color=background_color)
    text_pos = (-left + padding, -top + padding)
    ImageDraw.Draw(img).text(text_pos, text, font=font, fill=text_color)

    res_img = np.array(img)
    cv2.imwrite(save_path, res_img)

def get_random_word(length,vocab):
    word = ""
    while len(word)<length:
        word += random.choice(vocab)
    return word

def get_random_length(start,end):
    return random.randint(start,end)

def get_random(vocab):
    l = get_random_length(3,7)
    word = get_random_word(l,vocab)
    return word

def generate_images(word_id,word,fonts,img_dir):
    labels = {}
    for i, font in enumerate(fonts):
        try:
            generate_image(word,font,random.randint(32,40),save_path=os.path.join(img_dir,f"image_{word_id}_{i}.png"),layout="raqm")
            labels[f"image_{word_id}_{i}.png"] = word
        except:
            pass
    return labels
    

def main(args):
    fonts = [os.path.join(args.fonts_path,i) for i in os.listdir(args.fonts_path)][:20]
    if not os.path.exists(args.output_path):
        os.mkdir(args.output_path)
    img_dir = os.path.join(args.output_path,'images')
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    labels = {}
    vocab = VOCABS[args.vocab]
    for i in range(args.size):
        word = get_random(vocab)
        l = generate_images(i, word, fonts, img_dir)
        labels.update(l)
        print(f"Generated {len(l)} images for {word}")
        if i%100==0:
            with open(os.path.join(args.output_path,"labels.json"), "w", encoding='utf-8') as f:
                json.dump(labels,f)
    with open(os.path.join(args.output_path,"labels.json"), "w", encoding='utf-8') as f:
        json.dump(labels,f)

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Generate Random Data")
    parser.add_argument("--output_path", type=str, help="Path to output data")
    parser.add_argument("--fonts_path", type=str, help="Path to fonts")
    parser.add_argument("--size", type=int, help="Number of random words")
    parser.add_argument("--vocab",type=str,help="Vocab to use")

    # parser.add_argument("--weighted",action='store_true',help="Specify weight breakpoints")
    args = parser.parse_args()
    main(args)