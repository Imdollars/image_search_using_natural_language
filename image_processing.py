from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from PIL.ExifTags import TAGS
import torch


class ImageProcessor:
    def __init__(self, model_id="openai/clip-vit-base-patch16"):
        self.model = CLIPModel.from_pretrained(model_id)
        self.processor = CLIPProcessor.from_pretrained(model_id)

    def input_image(self, image_path):
        image = Image.open(image_path)
        inputs = self.processor(images=image, return_tensors="pt")
        return inputs

    def input_text(self, text):
        inputs = self.processor(text=text, return_tensors="pt")
        return inputs

    def image_get_feature(self, image_path):
        inputs = self.input_image(image_path)
        with torch.no_grad():
            image_feature = self.model.get_image_features(**inputs)
        image_feature = image_feature / image_feature.norm(p=2, dim=-1, keepdim=True)
        return image_feature

    def query_get_feature(self, query):
        inputs = self.input_text(query)
        with torch.no_grad():
            query_features = self.model.get_text_features(**inputs)
        query_features = query_features / query_features.norm(p=2, dim=-1, keepdim=True)
        return query_features

    @staticmethod
    def get_image_capture_time(image_path):
        image = Image.open(image_path)

        exif_data = image.getexif()
        if not exif_data:
            print("No EXIF metadata found")
            return None

        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == "DateTimeOriginal":
                return value

        print("No capture time found in EXIF metadata")
        return None
