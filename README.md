# README.md

## Recipe Parser

This repository contains a Python code that fetches and parses recipes from various websites. The fetched data is then stored in an SQLite database. Below is an example and usage guide for the `RecipeParser` class.

### Features

- **Fetching**: Fetches the HTML content of a given recipe URL.
- **Parsing**: Parses the fetched HTML content to extract recipe details.
- **Database**: Stores the parsed data in an SQLite database.
- **Image Saving**: Saves the recipe's image to a specified folder.

### Requirements

- Python 3.x
- `sqlite3`
- `requests`
- `re`
- `os`
- `json`
- `pprint`
- `bs4` (BeautifulSoup)

### Usage Example

Below is an example demonstrating how to use the `RecipeParser` class:

```python
from recipe_parser import RecipeParser, ConfigLoader

# Create an instance of ConfigLoader
config_loader = ConfigLoader()

# Prompt user for recipe URL and site name
user_url = input("Enter the URL of the recipe: ")
recipe_site = input("Enter the name of the recipe site: ")

# Create an instance of RecipeParser
recipe = RecipeParser(url=user_url, config_loader=config_loader, recipe_source=recipe_site)

# Parse recipe information
recipe.parse_recipe_info()
recipe.parse_ingredients()
recipe.parse_preparation_steps()

# Store parsed data in SQLite database
recipe.data_to_database()

# Save recipe image
recipe.save_recipe_image()

# Get recipe information
recipe_info = recipe.get_recipe_info()

# Print recipe information
print("\nRecipe Information:")
print(f"Recipe ID: {recipe_info['id']}")
print(f"Recipe Name: {recipe_info['recipe_name']}")
print(f"Number of Persons: {recipe_info['number_of_persons']}")
print(f"Time Duration: {recipe_info['time_duration']}")
print(f"Source URL: {recipe_info['source_url']}")
print(f"Ingredients: {recipe_info['ingredients']}")
print(f"Preparation Steps: {recipe_info['preparation_steps']}")
```

### Configuration

The code uses a `config.json` file to store configurations for different websites. You can add configurations for additional websites by updating this file.

### Contributing

If you have any suggestions, improvements, or issues, please feel free to open an issue or create a pull request.

### License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
