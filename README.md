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

## Website Configuration Template

The following template outlines the structure for configuring website-specific settings for recipe parsing.

```json
{
    "websitename": {
        "recipe_info_config": {
            "recipe_name": "html locator for recipe name",
            "recipe_description": "html locator for recipe description",
            "recipe_persons": "html locator for recipe persons",
            "recipe_time": "html locator for recipe time"
        },
        "preparation_config": {
            "recipe_preparation": "html locator for recipe preparation"
        },
        "ingredients_config": {
            "recipe_ingredients": "html locator for recipe ingredients"
        },
        "image_config": {
            "image_folder": "folder path to store images",
            "image_container_selector": "html locator for image container",
            "image_tag_selector": "html locator for image tag",
            "image_name_attribute": "attribute to extract image name"
        }
    }
}
```
### Explanation:

- **websitename**: Replace this with the name of the website you are configuring.
  
- **recipe_info_config**: Contains locators for various recipe information such as name, description, persons, and time.
  
- **preparation_config**: Contains the locator for the recipe preparation steps.
  
- **ingredients_config**: Contains the locator for the recipe ingredients.
  
- **image_config**: Contains settings related to image storage and retrieval.
  
- **html_locator**: is the argument to use with soup.select_one().

---

You can use this Markdown section as a reference or documentation for setting up configurations for different websites.

### Contributing

If you have any suggestions, improvements, or issues, please feel free to open an issue or create a pull request.

### License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
