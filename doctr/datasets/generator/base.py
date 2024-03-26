import random
from typing import Any, Callable, List, Optional, Tuple, Union

from PIL import Image, ImageDraw
import os
from doctr.io.image import tensor_from_pil
from doctr.utils.fonts import get_font

from ..datasets import AbstractDataset

def synthesize_text_img(
    text: str,
    font_size: int = 32,
    font_family: Optional[str] = None,
    background_color: Optional[Tuple[int, int, int]] = None,
    text_color: Optional[Tuple[int, int, int]] = None,
    padding: int = 5
) -> Image:
    """Generate a synthetic text image

    Args:
        text: the text to render as an image
        font_size: the size of the font
        font_family: the font family (has to be installed on your system)
        background_color: background color of the final image
        text_color: text color on the final image
        padding: padding of blank space around the word in image

    Returns:
        PIL image of the text
    """

    background_color = (0, 0, 0) if background_color is None else background_color
    text_color = (255, 255, 255) if text_color is None else text_color

    font = get_font(font_family, font_size, layout_engine= "raqm")
    left, top, right, bottom = font.getbbox(text)
    text_w, text_h = right - left, bottom - top
    # text_w, text_h = font.getsize(text)

    h, w = text_h + padding * 2, text_w + padding * 2
    # If single letter, make the image square, otherwise expand to meet the text size
    img_size = (h, w) if len(text) > 1 else (max(h, w), max(h, w))

    img = Image.new("RGB", img_size[::-1], color=background_color)
    d = ImageDraw.Draw(img)

    # Offset so that the text is centered
    # text_pos = (int(round((img_size[1] - text_w) / 2)), int(round((img_size[0] - text_h) / 2)))
    text_pos = (-left + padding, -top + padding)
    # Draw the text
    d.text(text_pos, text, font=font, fill=text_color)
    #Save 5 images with little randomisation
    if random.random()<0.5 and len(os.listdir("samples"))<5:
        img.save(f"samples/{text}.jpg")
        # print(f"Saving image {text}.jpg as sample")
    return img


class _CharacterGenerator(AbstractDataset):
    def __init__(
        self,
        vocab: str,
        num_samples: int,
        cache_samples: bool = False,
        font_family: Optional[Union[str, List[str]]] = None,
        img_transforms: Optional[Callable[[Any], Any]] = None,
        sample_transforms: Optional[Callable[[Any, Any], Tuple[Any, Any]]] = None,
    ) -> None:
        self.vocab = vocab
        self._num_samples = num_samples
        self.font_family = font_family if isinstance(font_family, list) else [font_family]  # type: ignore[list-item]
        # Validate fonts
        if isinstance(font_family, list):
            for font in self.font_family:
                try:
                    _ = get_font(font, 10)
                except OSError:
                    raise ValueError(f"unable to locate font: {font}")
        self.img_transforms = img_transforms
        self.sample_transforms = sample_transforms

        self._data: List[Image.Image] = []
        if cache_samples:
            self._data = [
                (synthesize_text_img(char, font_family=font), idx)
                for idx, char in enumerate(self.vocab)
                for font in self.font_family
            ]

    def __len__(self) -> int:
        return self._num_samples

    def _read_sample(self, index: int) -> Tuple[Any, int]:
        # Samples are already cached
        if len(self._data) > 0:
            idx = index % len(self._data)
            pil_img, target = self._data[idx]
        else:
            target = index % len(self.vocab)
            pil_img = synthesize_text_img(self.vocab[target], font_family=random.choice(self.font_family))
        img = tensor_from_pil(pil_img)

        return img, target


class _WordGenerator(AbstractDataset):
    def __init__(
        self,
        vocab: str,
        min_chars: int,
        max_chars: int,
        num_samples: int,
        words_txt_path: Optional[str] = None,
        cache_samples: bool = False,
        font_family: Optional[Union[str, List[str]]] = None,
        img_transforms: Optional[Callable[[Any], Any]] = None,
        sample_transforms: Optional[Callable[[Any, Any], Tuple[Any, Any]]] = None,
        random_flag: bool = True
    ) -> None:
        self.vocab = vocab
        self.wordlen_range = (min_chars, max_chars)
        self._num_samples = num_samples
        self.font_family = font_family if isinstance(font_family, list) else [font_family]  # type: ignore[list-item]
        # Validate fonts
        if isinstance(font_family, list):
            for font in self.font_family:
                try:
                    _ = get_font(font, 10)
                except OSError:
                    raise ValueError(f"unable to locate font: {font}")
        self.img_transforms = img_transforms
        self.sample_transforms = sample_transforms
        self.words_txt_path = words_txt_path
        self.random_flag = random_flag
        self.word_index = 0
        self.font_index = 0
        with open(self.words_txt_path, "r", encoding="utf-8") as f:
            self.total_words = len(f.readlines()) 

        self._data: List[Image.Image] = []
        if cache_samples:
            _words = [self._generate_string(*self.wordlen_range) for _ in range(num_samples)]
            self._data = [
                (synthesize_text_img(text, font_family=random.choice(self.font_family)), text) for text in _words
            ]
        self.counter=0       #count number of images generated; for saving appropriate number of samples

    def _generate_string(self, min_chars: int, max_chars: int) -> str:
        # num_chars = random.randint(min_chars, max_chars)
        # return "".join(random.choice(self.vocab) for _ in range(num_chars))
        if self.words_txt_path:
            words_list = open(self.words_txt_path, "r", encoding="utf-8").readlines()  
            word=""
            while True:
                if self.random_flag:
                    word = random.choice(words_list).rstrip("\n")
                else:
                    word = words_list[self.word_index].rstrip("\n")
                    self.word_index+=1
                    if self.word_index==self.total_words:
                        self.word_index=0
                if(len(word)<max_chars):
                    break
            return word

    def __len__(self) -> int:
        return self._num_samples

    def _read_sample(self, index: int) -> Tuple[Any, str]:
        # Samples are already cached
        if len(self._data) > 0:
            pil_img, target = self._data[index]
        else:
            target = self._generate_string(*self.wordlen_range)
            pil_img = None
            while not pil_img:
                if self.random_flag:
                    font = random.choice(self.font_family)
                else:
                    font = self.font_family[self.font_index]
                    self.font_index+=1
                    if self.font_index==len(self.font_family):
                        self.font_index=0
                try:
                    pil_img = synthesize_text_img(target, font_family=font)
                except:
                    with open("invalid.txt","a") as f:
                        f.write("\n"+font)
                    print(f"Invalid font {font}.. Retrying")

        self.counter+=1      #increment counter
        #if counter is divisible by number of samples divided by 5, save the image
        img = tensor_from_pil(pil_img)
        return img, target, ""
