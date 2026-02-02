import pyvips
import shutil
import logging
import requests
from pathlib import Path


SIZES = [100, 500, 2000]
class ImageProcessor():

    def __init__(self, path_of_images:str = 'data/images'):
        self.target_dir = Path(path_of_images)
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__) 
        logging.getLogger('pyvips').setLevel(logging.WARNING) # Reduce log level to WARNING to avoid too many logs from pyvips
    
    def save_all_games_images(self, images_data:list[tuple[str, int]]) -> None: 
        """ Main method of the class. Downloads, resizes and saves all game images in different sizes.

        This method uses requests.Session to optimize HTTP requests for downloading images, 
        reusing HTTP connections and avoiding redundant handshakes every time an image is being downloaded.
        """
        self.logger.info("🖼️ ⏳Starting to save all game images...")
        total_images = len(images_data)

        with requests.Session() as session:
            for index, (image_url, game_id) in enumerate(images_data, start=1):

                # Log progress for every 100 images processed to give feedback to the user
                if index % 100 == 1:
                    end_range = index + 100 - 1
                    if end_range > total_images:
                        end_range = total_images
                    self.logger.info(f"📥 Downloading and saving images from range {index}-{end_range}")

                try:
                    if not self._check_valid_image_url(url=image_url):
                        self.logger.warning(f"⚠️ Game {game_id} has an invalid image URL format, can not save image. Skipping....")
                        continue

                    category_name = self._get_category_name_from_url(image_url=image_url)
                    game_path = self.target_dir / f"game_{game_id}"
                    # Check if images already exists to avoid re-downloading
                    if game_path.is_dir():
                        
                        # Check if images already match
                        images_exists = self._check_if_images_matches(category_name=category_name, game_id=game_id, game_path=game_path)
                        if images_exists:
                            continue # Skip to game if images already exists

                        else:
                            # Images exists but do not match, so we delete the old images to re-download
                            self.logger.info(f"Images for game ID {game_id} changed. Deleting old images and re-downloading.")
                            shutil.rmtree(game_path)  # Remove existing directory with old images

                    game_path.mkdir(parents=True, exist_ok=True)
                    response = session.get(image_url, timeout=10)
                    response.raise_for_status()
         
                    # Creates a pyvips image from the downloaded content
                    website_image = pyvips.Image.new_from_buffer(response.content, "")

                    for size in SIZES:
                        filename = self._create_filename(category_name=category_name, game_id=game_id, size=size)
                        resized_image = self._resize_image(image=website_image, new_size=size)
                        self._save_image(image=resized_image, path_to_save=game_path, filename=filename)

                except Exception as e:
                    self.logger.error(f"❌ Error during processing image from Game {game_id}. Error: {e}. Skipping....")
                    continue

            self.logger.info("✅ All game images have been processed and saved.")

    def _check_valid_image_url(self, url:str) -> bool:
        """ Check if the image URL has a valid image format.
        
        This method is necessary because all images URLs of the website are valid
        """

        return url.endswith(('.jpg', '.jpeg', '.png', '.svg'))
    
    def _resize_image(self, image: pyvips.Image, new_size:int) -> pyvips.Image:
        """ Resize the image to the new size."""

        resized_image = image.thumbnail_image(
            new_size,
            height=new_size,
            crop='centre'
        )
        return resized_image

    def _save_image(self, image: pyvips.Image, path_to_save:Path, filename:str) -> bool:
        """ Save the image to the specified path with the given filename."""

        image_path = path_to_save / filename
        image.write_to_file(str(image_path))
        return True

    def _get_category_name_from_url(self, image_url:str) -> str:
        """ Extract the category name from the image URL.
        
        Image URL format example:
        https://example.com/images/category_name.jpg
        """

        url_without_format = image_url[0:-4] # Remove image format (.jpg, .png, etc)
        category_name = url_without_format.split('/')[-1]
        return category_name

    def _create_filename(self, category_name:str, game_id:str, size: int) -> str:
        """Create the filename for the image based on category name, game ID, and size."""
        return f"{category_name}_{game_id}_{size}x{size}.jpg"
    
    def _check_if_images_matches(self, category_name:str, game_id: str, game_path: Path):
        """Check if the images for a specific game and category already exist.
        
        For simplicity, we only check for the existence of the smallest size image. If it exists,
        we assume the other sizes exist as well. (Because the naming convention is consistent).
        """
        filename = self._create_filename(category_name=category_name, game_id=game_id, size=SIZES[0])
        filepath = game_path / filename
        return filepath.is_file()