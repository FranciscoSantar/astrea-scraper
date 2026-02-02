import logging
import time

from models.game import Game
from csv_writer.csv_writer import CSVWriter
from scraper.scraper import WebScraper
from logger.setup_logger import setup_logger
from database.database_controller import DatabaseController
from image_processor.image_procesor import ImageProcessor
from repositories.game_repository import GameRepository


def show_menu():
    print("-"*40)
    print("1. Run Scraper")
    print("2. Download and Save Images")
    print("3. Write Games Data to CSV per Category")
    print("4. Run All Steps")
    print("5. Exit")
    print("-"*40)

if __name__ == "__main__":
        
    try: 
        # Setup logger
        conn = None
        setup_logger()
        logger = logging.getLogger(__name__)

        logger.info("🚀 Starting the Games Scraper...")


        # Initialze database connection
        database_controller = DatabaseController()
        conn = database_controller.connect()
        database_controller.database_initialization()

        # Initialize components
        csv_writer = CSVWriter()
        image_processor = ImageProcessor()
        game_repository = GameRepository(connection=conn)
        scraper = WebScraper(game_repository=game_repository)

        while True:
            show_menu()
            choice = input("\nOption: ").strip()

            if choice == '1':
                # Start web scraping
                logger.info("Starting scraper...")
                scraper.scrape_web()

            elif choice == '2':
                # Save images
                logger.info("Starting the image saving process...")
                games_images_urls_and_id = game_repository.get_images_url_and_product_id()

                if not games_images_urls_and_id:
                    logger.warning("No images found to download. Please, first run the scraper to populate the database.")

                else:
                    image_processor.save_all_games_images(images_data=games_images_urls_and_id)

            # Write in CSV format
            elif choice == '3':
                logger.info("Starting the CSV writing process...")
                all_categories_names = game_repository.get_categories_names()
                if not all_categories_names:
                    logger.warning("No categories found. Please, first run the scraper to populate the database.")

                else:
                    csv_writer.write_headers(Game.get_fields_name()) # Write headers

                    for category_name in all_categories_names:
                        games = game_repository.get_games_by_category_name(category_name=category_name)
                        csv_writer.write_games_by_category(category_name=category_name, games_entities=games)
                        time.sleep(0.1)  # Sleep for 0.1 second between categories

                    csv_writer.flush()  # Ensure all data is written to output
                    logger.info("✅ All steps completed successfully!")

            elif choice == "4":
                logger.info("Starting the full process: Scraper, Image Saving, and CSV Writing...")
                
                # Step 1: Scrape the web
                scraper.scrape_web()

                # Step 2: Save images
                games_images_urls_and_id = game_repository.get_images_url_and_product_id()
                image_processor.save_all_games_images(images_data=games_images_urls_and_id)

                # Step 3: Write CSV
                all_categories_names = game_repository.get_categories_names()
                csv_writer.write_headers(Game.get_fields_name())
                for category_name in all_categories_names:
                    games = game_repository.get_games_by_category_name(category_name=category_name)
                    csv_writer.write_games_by_category(category_name=category_name, games_entities=games)
                    time.sleep(0.1)

                csv_writer.flush()
                logger.info("✅ All steps completed successfully!")

            elif choice == "5":
                print("Exiting the program")
                break
            else:
                print("Invalid option. Please, try again.")
                


    except Exception as e:
        logger.error(f"❌ An error occurred during scraping: {e}")
        raise

    finally:
        if conn:
            database_controller.disconnect()
