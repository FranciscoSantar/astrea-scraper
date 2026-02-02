def parse_price(price_to_parse: str) -> float|None:
    """Parse a price string and return its float representation.

    Prices are expected to be in the format 'XX,XX €'.
    """

    try:
        price_without_currency = price_to_parse[0:-2].replace(',', '.') # Remove currency symbol and replace comma with dot
        parsed_price = float(price_without_currency)
        return parsed_price
    except ValueError as e:
        return None