
import logging
from bs4.element import Tag
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page

from models.game import Game
from parsers.price_parser import parse_price
from repositories.game_repository import GameRepository



class WebScraper: 
    def __init__(self, game_repository: GameRepository):
        self.main_url="https://sandbox.oxylabs.io"
        self.is_last_page = False
        self.page_number = 1
        self.game_repository = game_repository
        self.logger = logging.getLogger(__name__)

    def scrape_web(self) -> None:
        """ Main method of the WebScraper class. Scrape the website and store the data in the database.
        
        This method uses Playwright to navigate through the website.

        It scrapes game data from each page.

        For each game, it checks if it already exists in the database. If it does, it updates the existing record; if not, it creates a new record.

        The method continues to the next page until there are no more pages left to scrape.
        """
        self.logger.info("🔍 ⏳ Starting web scraping...")
        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            while not self.is_last_page:

                self.logger.info(f"🌐 Scraping and saving games to the database for page {self.page_number}...")
                url = f"{self.main_url}/products?page={self.page_number}"
                page.goto(url)

                # Scroll to the bottom to load all products data
                self._scroll_down_page(page=page)

                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                # Extract all games data from the page
                games_html = soup.find_all("div", class_="product-card")
                for game_data in games_html:

                    game_entity = self._scrape_game(game_data=game_data) 
                    if not game_entity:
                        continue

                    # Check if the game already exists in the database
                    existing_game_id = self.game_repository.get_game_id_by_website_id(website_id=game_entity.website_id)
                    if existing_game_id:
                        self.game_repository.update(game=game_entity, game_id=existing_game_id)
                    else:
                        self.game_repository.create(game=game_entity)
                    
                # Check if there is a next page available
                self.is_last_page = self._check_next_page_exists(soup=soup)
                if not self.is_last_page:
                    self.page_number+=1

            browser.close()
            self.logger.info("✅ Web scraping completed successfully.")

    def _check_next_page_exists(self, soup: BeautifulSoup) -> bool :
        """ Check if there is a next page available in the pagination."""
        pagination_object = soup.find("ul", class_ = "pagination")
        next_button_object = pagination_object.find("li", class_="next disabled")
        return bool(next_button_object)
    
    def _scroll_down_page(self, page:Page) -> None:
        """ Scroll down the page."""
        page.evaluate("""
        async () => {
            const step = 500;
            for (let pos = 0; pos < document.body.scrollHeight; pos += step) {
                window.scrollTo(0, pos);
                await new Promise(r => setTimeout(r, 100)); // esperar 100ms entre pasos
            }
        }
        """)
    
    def _scrape_game(self, game_data: Tag) -> Game:
        """ Scrape data for a single game and return a Game entity.
        
        For each game, it extracts:
        - URL and ID
        - Name
        - Description
        - Price
        - Stock availability
        - Categories
        - Highest resolution image URL
        """
        try:
            game_url, game_id = self._get_id_and_url(game_object=game_data)
            game_name = self._get_name(game_object=game_data)
            if not game_name:
                raise Exception("Game without name detected.")
            game_price = self._get_price(game_object=game_data)
            if game_price is None:
                raise Exception("Game without price detected.")
            game_description = self._get_description(game_object=game_data)
            game_stock = self._has_stock(game_object=game_data)
            game_categories = self._get_categories_name(game_object=game_data)
            game_highest_resolution_image_url = self._get_highest_resolution_image_url(game_object=game_data)

            game_entity = Game(
                website_id=game_id,
                name=game_name,
                description=game_description,
                price=game_price,
                categories=game_categories,
                image_url=game_highest_resolution_image_url,
                has_stock=game_stock,
                url=game_url
            )
            return game_entity

        except Exception as e:
            self.logger.error(f"❌ Error during scraping game data: {e}. Skipping....")
            return None
    
    def _get_id_and_url(self, game_object: Tag) -> tuple[str|None, int|None]:
        """ Extract the URL and ID of the game from the game data object."""
        try:
            header_object = game_object.find("a", class_="card-header")

            product_path = header_object.get('href')
            game_url = self.main_url + product_path
            game_id = product_path.split("/")[-1]
            return game_url, int(game_id)
        except Exception as e:
            self.logger.warning(f"⚠️ Error extracting name: {e}")
            return None, None
    
    def _get_name(self, game_object: Tag) -> str|None:
        """Extract the name of the game from the game data object."""
        try:
            title_object = game_object.find("h4", class_="title")
            return title_object.text
        except Exception as e:
            self.logger.warning(f"⚠️ Error extracting name: {e}")
            return None
    
    def _get_description(self, game_object: Tag) -> str|None:
        """ Extract the description of the game from the game data object."""
        try:
            description_object = game_object.find("p", class_="description")
            return description_object.text
        except Exception as e:
            self.logger.warning(f"⚠️ Error extracting description: {e}")
            return None

    def _get_price(self, game_object: Tag) -> float|None:
        """ Extract the price of the game from the game data object."""
        try:
            price_object = game_object.find("div", class_="price-wrapper")
            price_str = price_object.text
            return parse_price(price_str)
        except Exception as e:
            self.logger.warning(f"⚠️ Error extracting price: {e}")
            return None
    
    def _has_stock(self, game_object: Tag) -> bool:
        """ Check if the game is in stock from the game data object."""
        has_stock_object = game_object.find("p", class_="out-of-stock")
        return has_stock_object is None
    
    def _get_categories_name(self, game_object: Tag) -> list[str|None]:
        """ Extract the categories names of the game from the game data object."""
        categories_object = game_object.find("p", class_="category")

        if categories_object:
            category_list = [category.text.strip().replace('"', '') for category in categories_object.find_all("span") if category.text.strip()]
            return category_list
        return []
    
    def _get_highest_resolution_image_url(self, game_object: Tag) -> str|None:
        """ Extract the highest resolution image URL of the game from the game data object.
        
        It parses the 'srcset' attribute of the image tag to get all available image URLs and their widths,
        then selects the one with the highest width.
        """
        try:
            product_images_attributes = game_object.find("img", class_="image")

            all_images_links = product_images_attributes.get("srcset").split(", ")
            ordered_images_link = self._order_list_of_images_url(all_images_links)
            highest_resolution_image_path = ordered_images_link[0][0]
            highest_resolution_image_url = self.main_url + highest_resolution_image_path
            return highest_resolution_image_url
        except Exception as e:
            self.logger.warning(f"⚠️ Error extracting highest resolution image URL: {e}")
            return None
    
    def _order_list_of_images_url(self, images_list:str) -> list[tuple[str, int]]:
        """ Order the list of image URLs by their width in descending order.
        
        The input is a list of strings in the format "url widthw", e.g., "https://example.com/image1.jpg 300w".
        """
        list_of_images_urls = []
        for image_url_data in images_list:
            image_url, image_width = image_url_data.split(" ")
            image_width = int(image_width[0:-1])
            list_of_images_urls.append((image_url, image_width))
        
        # Sort images by width to get the highest resolution first
        ordered_list_of_images_urls = sorted(list_of_images_urls, key=lambda image_url_data: image_url_data[1], reverse=True)
        return ordered_list_of_images_urls
        