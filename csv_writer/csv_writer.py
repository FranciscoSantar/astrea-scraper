import csv
import sys
from models.game import Game
class CSVWriter():
    def __init__(self):
        self.writer = csv.writer(sys.stdout) # Initialize CSV writer to write to standard output (terminal)
    
    def write(self, data:list[str]) -> None:
        """Write a row of data to the CSV output."""
        self.writer.writerow(data)
    
    def write_headers(self, headers:list[str]) -> None:
        """Write the header row to the CSV output."""
        self.writer.writerow(headers)
    
    def flush(self) -> None:
        """Flush the CSV output to ensure all data is written."""
        sys.stdout.flush()

    def write_games_by_category(self, category_name:str, games_entities:list[Game]) -> None:
        """Write all games data for a specific category to the CSV output."""
        for game in games_entities:
            game_data = game.to_row()
            game_data.insert(0, category_name)  # Insert category name at the beginning
            self.writer.writerow(game_data)