
from typing import Dict, Any
import torch
import logging
from sqlalchemy.exc import InvalidRequestError
from torch import Tensor
from image_processing import ImageProcessor
from database import Image_data

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
DEFAULT_SIMILARITY_APPROACH = "cosine_similarity"


class ImageDescriptionGenerator:
    def __init__(self, model_id, session):
        self.processor = ImageProcessor(model_id=model_id)
        self.Session = session

    def batch_image_get_features(self):
        session = self.Session()
        images = session.query(Image_data).all()
        if not images:
            logger.info("No images to process.")
            return

        for image in images:
            try:
                if not session.is_active:
                    session = self.Session()
                features = self.processor.image_get_feature(image.image_path)
                image.image_feature = ",".join(map(str, features.squeeze().tolist()))
                session.merge(image)
                session.commit()
                logger.info(f"Successfully updated image with PATH {image.image_path}.")
            except InvalidRequestError as e:
                logger.error(f"Invalid request error with image PATH {image.image_path}: {e}")
                session.rollback()
            except Exception as e:
                session.rollback()
                logger.error(f"Error processing image with PATH {image.image_path}: {e}")
        session.close()

    def compare_query_to_images(self, image_paths, query) -> dict[str, Tensor]:
        approach = DEFAULT_SIMILARITY_APPROACH
        while True:
            print("\n***********************************************************************************************\n")
            approach_id = input("Please choose the approach you would like to use:\n1.cosine_similarity\n2.euclidean\n")
            if approach_id not in ["1", "2"]:
                print("Invalid choice. Please enter a valid option.")
                continue
            else:
                break
        if approach_id == "1":
            approach = 'cosine_similarity'
        elif approach_id == "2":
            approach = 'euclidean'

        dic_image_features = {}
        for image_path in image_paths:
            dic_image_features.update({image_path: self.processor.image_get_feature(image_path)})
        query_feature = self.processor.query_get_feature(query)

        similarities = {}
        for image_path in image_paths:
            if approach == 'cosine_similarity':
                image_feature = dic_image_features[image_path]
                similarity = torch.nn.functional.cosine_similarity(image_feature, query_feature, dim=-1)
                similarities.update({image_path: similarity})
            elif approach == 'euclidean':
                image_feature = dic_image_features[image_path]
                similarity = torch.norm(image_feature - query_feature, p=2)
                similarities.update({image_path: similarity})

        return similarities  # {image_path: similarity}

    def batch_insert_image_by_mysql(self, *args):
        image_path_to_add = []

        # add image path
        for arg in args:
            image_path_to_add.append(Image_data(image_path=arg))

        session = self.Session()
        try:
            session.add_all(image_path_to_add)
            session.commit()
            logger.info(f"Successfully inserted {len(image_path_to_add)} images.")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert images: {e}")
        finally:
            session.close()

    def batch_insert_image_capture_data(self):
        session = self.Session()
        images = session.query(Image_data).all()
        if not images:
            logger.info("No images to process.")
            return

        for image in images:
            try:
                if not session.is_active:
                    session = self.Session()
                date = ImageProcessor.get_image_capture_time(image.image_path)
                if date:
                    image.data = date
                    session.merge(image)
                    session.commit()
                    logger.info(f"Successfully updated image_data with PATH {image.image_path}.")
            except InvalidRequestError as e:
                logger.error(f"Invalid request error with image_data PATH {image.image_path}: {e}")
                session.rollback()
            except Exception as e:
                session.rollback()
                logger.error(f"Error processing image_data with PATH {image.image_path}: {e}")
