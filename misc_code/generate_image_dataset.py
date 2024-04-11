import argparse
from PIL import ImageFont, Image, ImageDraw, ImageFilter
import random
import os
import numpy as np
import json

class DataImage:
    def __init__(self, image, background_color, color):
        self.image = image
        self.backgroung_color = background_color
        self.color = color
    def new_from_properties(self,image):
        return DataImage(image,self.backgroung_color,self.color)

class Generator:
    def __init__(self, word_file, font_dir, out_dir):
        if os.path.isfile(word_file):
            self.word_file = word_file
        else:
            raise FileNotFoundError(f"{word_file} does not exist")
        
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        if not os.path.exists(os.path.join(out_dir,"images")):
            os.mkdir(os.path.join(out_dir,"images"))
        
        self.out_dir = out_dir

        if os.path.isdir(font_dir):
            self.fonts = [os.path.join(font_dir,i) for i in os.listdir(font_dir)]
        else:
            raise FileNotFoundError(f"The directory {font_dir} does not exist.")
        if len(self.fonts)==0:
            raise Exception("Font Directory Empty")

    def generate(
            self, 
            font_sample_rate = 0.2, 
            font_size_range = [24,32],
            random_color_rate = 0.5, 
            random_rotation_rate = 0.5,
            angle_deviation = 10,
            random_blur_rate = 0.5,
            blur_radius = 0,
            blur_deviation = 1,
            random_noise_rate = 0.2,
            noise_level = 1
            ):
        
        labels = {}
        with open(self.word_file,encoding="utf-8") as f:
            for i,word in enumerate(f):
                word = word.strip()
                fonts = self.sample_fonts(font_sample_rate)
                if len(fonts)==0:
                    raise Exception("Check fonts and font_sample_rate. Resultant Sample is Empty")
                for f,font in enumerate(fonts):

                    # Sampling Color
                    if self.doSample(random_color_rate):
                        bg,fg = self.generate_color()
                    else:
                        bg,fg = (0,0,0), (255,255,255)
                    
                    # Sampling Size
                    size = random.randint(*font_size_range)

                    image = self.generate_base_image(word,font,size,bg,fg,5,ImageFont.Layout.RAQM)

                    # Sampling Rotation
                    if self.doSample(random_rotation_rate):
                        image = self.rotate_image(image, angle_deviation)

                    # Sampling Blur
                    if self.doSample(random_blur_rate):
                        image = self.add_blur(image, blur_radius, blur_deviation)
                    
                    # Sampling Noise
                    if self.doSample(random_noise_rate):
                        image = self.add_noise(image, noise_level)
                    img_path = f"img_{i}_{f}_{font.split('.')[0][-1]}.png"
                    image.image.save(os.path.join(self.out_dir,"images",img_path))
                    labels[img_path] = word
                
                if i % 20:
                    with open(os.path.join(self.out_dir,"labels.json"), "w", encoding='utf-8') as label_file:
                        json.dump(labels,label_file)

        with open(os.path.join(self.out_dir,"labels.json"), "w", encoding='utf-8') as label_file:
            json.dump(labels,label_file)
    
    def doSample(self,rate):
        return random.random() <= rate

    def generate_base_image(
            self,
            text,
            font_family,
            font_size = 24,
            background_color = (0,0,0),
            text_color = (255,255,255),
            padding = 5,
            layout_engine = ImageFont.Layout.BASIC
    ):

        font = font = ImageFont.truetype(font_family, font_size, layout_engine= layout_engine)
        left, top, right, bottom = font.getbbox(text)
        text_w, text_h = right - left, bottom - top

        h, w = text_h + padding * 2, text_w + padding * 2
        img_size = (h, w) if len(text) > 1 else (max(h, w), max(h, w))

        img = Image.new("RGB", img_size[::-1], color=background_color)
        d = ImageDraw.Draw(img)

        text_pos = (-left + padding, -top + padding)
        d.text(text_pos, text, font=font, fill=text_color)

        return DataImage(img, background_color, text_color)
    
    def rotate_image(self, image: DataImage, angle_deviation = 10):
        angle = random.gauss(0, angle_deviation)
        return image.new_from_properties(image.image.rotate(angle, expand=True, fillcolor=image.backgroung_color))
    
    def add_blur(self, image: DataImage, blur_radius = 0, blur_deviation = 1):
        """
        Add blur to the image.
        """
        blur = abs(random.gauss(blur_radius, blur_deviation))
        blurred_image = image.image.filter(ImageFilter.GaussianBlur(radius=blur))
        return image.new_from_properties(blurred_image)

    def add_noise(self,image: DataImage, noise_level = 1):
        """
        Add random noise to the image.
        """
        img_array = np.array(image.image)
        noise = np.random.randint(0, noise_level + 1, img_array.shape, dtype=np.uint8)
        noisy_img_array = np.clip(img_array + noise, 0, 255)
        noisy_image = Image.fromarray(noisy_img_array)
        return image.new_from_properties(noisy_image)
    
    def generate_color(self):
        bg = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        fg = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        while True:
            if bg == fg:
                bg = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                fg = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            else:
                break
        return bg, fg

    def sample_fonts(self, font_sample_rate):
        return random.sample(self.fonts, int(len(self.fonts) * font_sample_rate))
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate Image Data")
    parser.add_argument("--word_file", type=str, help="Path to input data")
    parser.add_argument("--font_dir", type=str, help="Path to fonts")
    parser.add_argument("--out_dir", type=str, help="Path to output directory")

    parser.add_argument("--font_sample_rate", type=float, default= 0.2, help="Subset of Font to pick for each word")
    parser.add_argument("--font_size_start", type=int, default=24, help="Start of font size range")
    parser.add_argument("--font_size_end", type=int, default=32, help="End of font size range")

    parser.add_argument("--random_color_rate", type=float, default=0.5, help="Rate to apply random color")
    
    parser.add_argument("--random_rotation_rate", type=float, default=0.5, help="Rate to apply random rotation")
    parser.add_argument("--angle_deviation", type=float, default=10, help="Rotaion angle deviation")

    parser.add_argument("--random_blur_rate", type=float, default=0.5, help="Rate to apply random blur")
    parser.add_argument("--blur_radius", type=float, default=0, help="Blur Radius Mean")
    parser.add_argument("--blur_deviation", type=float, default=1, help="Blur Radius std")

    parser.add_argument("--random_noise_rate", type=float, default=0.2, help="Rate to apply random noise")
    parser.add_argument("--noise_level", type=float, default=1, help="Noise Level")


    # parser.add_argument("--weighted",action='store_true',help="Specify weight breakpoints")
    args = parser.parse_args()
    
    g = Generator(args.word_file, args.font_dir, args.out_dir)
    g.generate(
        font_sample_rate= args.font_sample_rate,
        font_size_range= (args.font_size_start,  args.font_size_end),
        random_color_rate= args.random_color_rate,
        random_rotation_rate= args.random_rotation_rate,
        angle_deviation = args.angle_deviation,
        random_blur_rate = args.random_blur_rate,
        blur_radius = args.blur_radius,
        blur_deviation = args.blur_deviation,
        random_noise_rate = args.random_noise_rate,
        noise_level = args.noise_level
    )

    print("Data Generated Successfully")
