import sys
import logging
from itertools import islice
from config import config_ini, ConfigFileNotFoundError
from generator import ImageDescriptionGenerator
from database import create_db_session, Image_data
from utilities import install_missing_package
from sqlalchemy.exc import OperationalError
import pymysql
import os


logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
image_file = "./image_file"


def main():
    # Load or create configuration
    try:
        config = config_ini()
    except ConfigFileNotFoundError as e:
        logger.error(e)
        sys.exit(1)

    # Create database session
    try:
        connection_string = f'mysql+pymysql://{config["database"]["user"]}:{config["database"]["password"]}@{config["database"]["host"]}/{config["database"]["name"]}'
        Session = create_db_session(connection_string)
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        logger.error("Please ensure that the database user has the necessary privileges to access the database.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        sys.exit(1)

    # Instantiate ImageDescriptionGenerator
    try:
        image_description_generator = ImageDescriptionGenerator(
            model_id="openai/clip-vit-base-patch16",
            session=Session
        )
    except ImportError as e:
        if "cryptography" in str(e):
            logger.error("Failed to initialize ImageDescriptionGenerator: 'cryptography' package is required for sha256_password or caching_sha2_password auth methods.")
            logger.info("Attempting to install 'cryptography' package...")
            install_missing_package("cryptography")
            logger.info("'cryptography' package installed. Please restart the program.")
        else:
            logger.error(f"Failed to initialize ImageDescriptionGenerator: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize ImageDescriptionGenerator: {e}")
        sys.exit(1)

    # Prompt user for operation choice
    while True:
        print("\nSelect an operation:")
        print("1. Insert New Images into Database")
        print("2. Batch Process Images to Generate Features")
        print("3. Compare Query to Existing Images")
        print("4. Batch Compare Queries to Existing Images")
        print("5. Exit")

        user_choice = input("Enter choice (1/2/3/4/5): ").strip()
        if user_choice not in ["1", "2", "3", "4", "5"]:
            print("Invalid choice. Please enter a valid option.")
            continue

        # 1. Insert New Images into Database
        elif user_choice == "1":
            image_paths = []
            print("Do you want to use Auto-insert?(y/n): ")
            auto_insert = input("Auto Insert: ").strip().lower()
            if auto_insert not in ["y", "n"]:
                print("Invalid choice. Please enter a valid option.")
                continue
            if auto_insert == "n":
                image_paths = input("Enter image paths separated by commas: ").strip().split(',')
            else:
                if not os.path.exists(image_file):
                    os.makedirs(image_file)
                for root, dirs, files in os.walk(image_file):
                    for file in files:
                        if file.lower().endswith(('.jpeg', '.tiff', '.jpg', '.png', '.gif')):
                            image_path = os.path.join(root, file)
                            image_paths.append(image_path)

            if not image_paths:
                print("No valid image paths provided.")
                continue
            image_description_generator.batch_insert_image_by_mysql(*image_paths)
            image_description_generator.batch_insert_image_capture_data()

        # 2. Batch Process Images to Generate Features
        if user_choice == "2":
            image_description_generator.batch_image_get_features()

        # 3. Compare Query to Existing Images
        elif user_choice == "3":
            query = input("Enter the query text: ").strip()
            session = Session()
            image_records = session.query(Image_data).all()
            image_paths = [image.image_path for image in image_records]
            if not image_paths:
                print("No images found in the database.")
                continue
            dic_similarities = image_description_generator.compare_query_to_images(image_paths, query)
            print(f"\n******************************************************************\n")
            for image_path in dic_similarities:
                print(f"Similarity with {image_path}: {dic_similarities[image_path].item():.4f}")

            print(f"\n******************************************************************\n")
            sorted(dic_similarities, reverse=True)
            n = int(input("Press input the top number that you want to show:"))
            if n < len(dic_similarities):
                first_n_items = dict(islice(dic_similarities.items(), n))
            else:
                first_n_items = dict(islice(dic_similarities.items(), len(dic_similarities)))
            print(first_n_items)
            input("\nPress Enter to continue...")

        # 4. Batch Compare Queries to Existing Images
        elif user_choice == "4":
            queries = [query.strip() for query in input("Enter queries separated by commas: ").split(',') if query.strip()]
            with Session() as session:
                image_records = session.query(Image_data).all()

            image_paths = [image.image_path for image in image_records]
            if not image_paths or not queries:
                print("No valid queries or images found in the database.")
                continue
            for query in queries:
                dic_similarities = image_description_generator.compare_query_to_images(image_paths, query)
                print(f"\n******************************************************************\n")
                print(f"Results for query '{query}':")
                for image_path in dic_similarities:
                    print(f"Similarity with {image_path}: {dic_similarities[image_path].item():.4f}")

                sorted_dic_similarities = dict(sorted(dic_similarities.items(), reverse=True, key=lambda item: item[1]))
                n = int(input("\nPress input the top number that you want to show:"))
                first_n_items = dict(islice(sorted_dic_similarities.items(), n))
                print(first_n_items)
            input("\nPress Enter to continue...")

        # 5. Exit
        elif user_choice == "5":
            print("Exiting the program. Goodbye!")
            break


if __name__ == "__main__":
    main()
