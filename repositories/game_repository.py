import logging
from sqlite3 import Connection, Cursor

from models.game import Game

class GameRepository:
    def __init__(self, connection: Connection):
        self.connection = connection
        self.logger = logging.getLogger(__name__)

    def get_game_id_by_website_id(self, website_id:int) -> int|None :
        """Get game id by website id.
        
        This method is used to check if a game already exists in the database.
        """

        cursor = self.connection.cursor()

        cursor.execute(
            """
                SELECT id FROM games WHERE website_id = :id
            """, 
            {"id": website_id}
        )

        game_id = cursor.fetchone()
        if not game_id:
            return None
        return game_id[0]
    
    def create(self, game: Game) -> bool:
        """Create a new game in the database.
        
        Steps:
            - First, insert the game into the games table (using `_insert_game()` method).
            - Then, for each category of the game:
                - If it is new, insert it into the categories table (using `_insert_categories_and_get_ids()` method).
                - If already exists in the database, it will not be inserted again, but its id will be retrieved.
                - At the end, we will have a list of category ids for the game.
            - Finally, insert the game-category relationships into the game_category table (using `_insert_game_categories()` method).
        """

        cursor = self.connection.cursor()

        # Get dict for creating the game
        create_game_dict = game.to_create_db_dict()

        game_id = self._insert_game(cursor=cursor, game_dict=create_game_dict)
        categories_ids_of_game = self._insert_categories_and_get_ids(cursor=cursor, game_dict=create_game_dict)
        if categories_ids_of_game:
            self._insert_game_categories(cursor=cursor, game_id=game_id, categories_id=categories_ids_of_game)

        self.connection.commit()
        return True

    def update(self, game:Game, game_id: int) -> bool:
        """Update an existing game in the database.
        
        Steps:
            - First, update the game in the games table (using `_update_game()` method).
            - Then, delete the existing game-category relationships for the game, in case categories have changed.
            - Next, for each category of the updated game:
                - If it is new, insert it into the categories table (using `_insert_categories_and_get_ids()` method).
                - If already exists in the database, it will not be inserted again, but its id will be retrieved.
                - At the end, we will have a list of category ids for the game. 
            - Finally, insert the new game-category relationships into the game_category table (using `_insert_game_categories()` method).
        """

        cursor = self.connection.cursor()

        # Set the id of the game to be updated
        game.set_id(id=game_id)

        # Get dict for updating the game
        update_game_dict = game.to_update_db_dict()

        self._update_game(cursor=cursor, game_dict=update_game_dict)
        self._delete_game_categories_by_game_id(cursor=cursor, game_id=game_id)
        updated_categories_ids_of_game = self._insert_categories_and_get_ids(cursor=cursor, game_dict=update_game_dict)
        if updated_categories_ids_of_game:
            self._insert_game_categories(cursor=cursor, game_id=game_id, categories_id=updated_categories_ids_of_game)
        
        self.connection.commit()
        return True
    
    def get_games_by_category_name(self, category_name:str) -> list[Game] | None:
        """Get all games that belong to a specific category by category name.
        
        This method retrieves all games associated with the given category name from the database.
        It is used to write games data into category-specific CSV.
        """
        cursor = self.connection.cursor()

        games_entities = []
        cursor.execute(
            """
                SELECT
                    g.id,
                    g.website_id,
                    g.name,
                    g.description,
                    g.price,
                    g.image_url,
                    g.has_stock,
                    g.url,
                    g.sale_price
                FROM
                    categories c
                LEFT JOIN game_category gc ON
                    c.id = gc.category_id
                LEFT JOIN games g ON
                    g.id = gc.game_id
                WHERE
                    c.name = :category_name
                ORDER BY g.price DESC, g.name ASC
            """,
            {"category_name": category_name}
        )

        games = cursor.fetchall()
        if not games:
            return None
        
        for game_data in games:
            # Get categories names of the game. Necessaries to build the Game entity.
            game_id = game_data[0]
            category_names_of_game = self._get_categories_names_by_game_id(cursor=cursor, game_id=game_id)
            game = Game(
                id=game_id,
                website_id=game_data[1],
                name=game_data[2],
                description=game_data[3],
                price=game_data[4],
                image_url=game_data[5],
                has_stock=game_data[6],
                url=game_data[7],
                sale_price=game_data[8],
                categories=category_names_of_game            
            )
            games_entities.append(game)

        return games_entities

    def get_images_url_and_product_id(self) -> list[tuple[str, int]] | None:
        """ This method retrieves all games' image URLs along with their product IDs from the database.

        It returns a list of tuples, where each tuple contains the image URL and the corresponding product
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
                SELECT image_url, id FROM games
                ORDER BY id;
            """
        )  

        result = cursor.fetchall()
        if not result:
            return None

        return [image_data for image_data in result]

    def get_categories_names(self) -> list[str]| None:
        """Get all category names from the database."""

        cursor = self.connection.cursor()

        cursor.execute(
            """
                SELECT name FROM categories
                ORDER BY name ASC;
            """
        )  

        result = cursor.fetchall()
        if not result:
            return None

        return [category[0] for category in result]

    def _get_categories_names_by_game_id(self, cursor: Cursor, game_id: int) -> list[str]:
        """Get category names of a game by its id."""

        cursor.execute(
            """
                SELECT c.name
                FROM categories c
                INNER JOIN game_category gc ON c.id = gc.category_id
                WHERE gc.game_id = :game_id;
            """,
            {"game_id": game_id}
        )

        result = cursor.fetchall()
        if not result:
            return None

        return [category[0] for category in result]
    
    def _get_category_id_by_name(self, cursor: Cursor, category_name:str) -> int|None :
        """Get category id by its name."""

        cursor.execute(
            """
                SELECT id FROM categories WHERE name = :category_name
            """, 
            {"category_name": category_name}
        )

        category_id = cursor.fetchone()
        if not category_id:
            return None

        return category_id[0]

    def _insert_categories_and_get_ids(self, cursor: Cursor, game_dict: dict) -> list[int]|None:
        """This method inserts the categories of a game into the categories table and returns their ids.

        If a category already exists, it retrieves its id instead of inserting a new one.
        """

        games_categories = game_dict.get('categories')
        if not games_categories:
            return None
        
        categories_ids = []
        for category_name in games_categories:

            category_id = self._get_category_id_by_name(cursor=cursor, category_name=category_name) # Check if category already exists
            if not category_id:

                cursor.execute(
                    """
                        INSERT INTO categories (name) VALUES (:category_name)
                        RETURNING id
                    """, 
                    {"category_name": category_name}
                )
                result = cursor.fetchone()

                if not result:
                    self.logger.warning(f"⚠️ Error during inserting category: {category_name}. Skiping....")
                    continue

                category_id = result[0]
            
            categories_ids.append(category_id)
        return categories_ids

    def _insert_game(self, cursor: Cursor, game_dict: dict) -> int:
        """Insert a new game into the games table and return its id."""

        cursor.execute(
            """
                INSERT INTO games (website_id, name, description, price, sale_price, image_url, has_stock, url)
                VALUES (:website_id, :name, :description, :price, :sale_price, :image_url, :has_stock, :url)
                RETURNING id
            """, 
            game_dict
        )
        result = cursor.fetchone()

        if not result:
            self.logger.warning(f"⚠️ Error during inserting game: {game_dict.get('name')}. Skipping....")
            return None

        game_id = result[0]
        return game_id

    def _insert_game_categories(self, cursor: Cursor, game_id: int, categories_id:list[int]) -> None:
        """Insert game-category relationships into the game_category table."""

        for category_id in categories_id:

            cursor.execute(
                """
                    INSERT INTO game_category (game_id, category_id) VALUES (:game_id, :category_id)
                """, 
                {
                    "game_id": game_id,
                    "category_id": category_id
                }
            )
    
    def _update_game(self, cursor: Cursor, game_dict:dict) -> None:
        """Update an existing game in the games table.
        
        This method updates the following fields of a game:
            - description
            - price
            - sale_price
            - image_url
            - stock status
        """

        cursor.execute(
            """
                UPDATE games 
                SET description = :description,
                    price = :price,
                    sale_price = :sale_price,
                    image_url = :image_url,
                    has_stock = :has_stock
                WHERE id = :id
            """, 
            game_dict
        )
        
    def _delete_game_categories_by_game_id(self, cursor: Cursor, game_id:int) -> list[int] | None :
        """Delete game-category relationships by game id."""

        cursor.execute(
            "DELETE FROM game_category WHERE game_id = :game_id",
            {"game_id": game_id}
        ) 
                