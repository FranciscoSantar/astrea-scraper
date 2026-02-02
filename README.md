# Games Scraper

## Summary

A Python-based web scraper designed to extract game data from this (website)[https://sandbox.oxylabs.io/], process and store it in a SQLite database, download and save game images, and display in the terminal the game data in CSV format for each category. 

The scraper provides an interactive menu system to run single operations, including 
  - Web scraping
  - Image processing
  - Data export 

The menu also includes an option to run all operations sequentially.

## Technologies Used

- **Python 3.14** - Core programming language
- **Playwright** - Browser automation for web scraping
- **BeautifulSoup4** - HTML parsing and data extraction
- **SQLite** - Local database for storing game data
- **pyvips** - Image processing library
- **Requests** - HTTP library for downloading resources
- **Docker** - Containerization for easy deployment

## Requirements to Run the Script

### Without Docker

- **[Python 3.14](https://www.python.org/downloads/release/python-3140/)**
- **pip**
- System dependencies for Playwright

### With Docker

- **[Docker](https://docs.docker.com/get-started/get-docker/)**
- **[Docker Compose](https://docs.docker.com/compose/install/)**

## Installation and Setup

### Without Docker

1. **Clone the repository:**
   ```bash
   git clone https://github.com/FranciscoSantar/astrea-scraper.git
   cd astrea-scraper
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv-scraper

   # Once created, activate it

   source venv-scraper/bin/activate  # On macOS/Linux
   # or
   venv-scraper\Scripts\activate  # On Windows
   ```

3. **Install Python dependencies:**
   ```bash
   pip install --no-cache-dir -r requirements.txt
   ```

4. **Install Playwright browser (Chromium):**
   ```bash
   playwright install chromium chromium-headless-shell
   ```

5. **Run the scraper:**
   ```bash
   python3 main.py
   ```

### With Docker

1. **Clone the repository:**
   ```bash
   git clone https://github.com/FranciscoSantar/astrea-scraper.git
   cd games-scraper
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose build
   ```

   Or run in detached mode:
   ```bash
   docker-compose run --rm astrea-scraper
   ```

## Usage

Once the application starts, you'll see an interactive menu with the following options:

1. **Run Scraper** - Start the web scraping process to collect game data
2. **Download and Save Images** - Download game images and store them locally
3. **Write Games Data to CSV per Category** - Display game data in CSV format in the terminal, grouped and ordered by category
4. **Run All Steps** - Execute all operations sequentially
5. **Exit** - Close the application

