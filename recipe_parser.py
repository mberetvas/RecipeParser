import sqlite3
import requests
import re
import os
import json
from pprint import pprint
from bs4 import BeautifulSoup


class RecipeParser:
    def __init__(self, url, config_loader, recipe_source):
        """
        RecipeParser() is used to get the data of the recipe from an URL.
        Provide the URL and the config_loader to get the data.
        The json config file is prepared to work with 15gram and Dagelijkse Kost.
        If you want to use it for another website, you need to add the info to the config file.

        Parameters:
        - url (str): The URL of the recipe page.
        - config_loader (ConfigLoader): An instance of ConfigLoader for loading configuration data.
        """
        self.recipe_source = "".join(recipe_source.lower().split())
        self.config_loader = config_loader
        self.recipe_id = None
        self.recipe_name = None
        self.recipe_description = None
        self._number_of_persons = None
        self.time_duration = None
        self.source_url = url
        self.ingredients_source = []
        self.preparation_steps = []
        self.html_content = self.get_html_content()
        self.soup = BeautifulSoup(self.html_content, 'html.parser')
        self._configurations = {}
    
    def __str__(self):
        return f"{self.recipe_name} from {self.recipe_source}"

    @property
    def configurations(self):
        """
        Get the configurations for parsing recipe information, ingredients and preparation steps.
        """
        self.configurations = self.config_loader.get_configurations()

    @configurations.setter
    def configurations(self):

        self._configurations = {}

    @property
    def number_of_persons(self):
        """
        Get the number of persons for the recipe.
        """
        return self._number_of_persons

    @number_of_persons.setter
    def number_of_persons(self, persons):
        """
        Set the number of persons for the recipe.
        """
        if persons:
            persons = re.sub(r'\D', '', persons)  # Extract only digits
        self._number_of_persons = persons

    def get_html_content(self):
        """
        Fetch HTML content from the provided URL.

        Returns:
        - str: The HTML content.
        Raises:
        - Exception: If fetching HTML content fails.
        """
        response = requests.get(self.source_url)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(
                f"Failed to fetch HTML content. Status code: {response.status_code}")

    def get_recipe_info(self):
        """
        Get a dictionary containing various recipe information.

        Returns:
        - dict: A dictionary containing recipe information.
        """
        info_dict = {
            "id": self.recipe_id,
            "recipe_name": self.recipe_name,
            "recipe_description": self.recipe_description,
            "number_of_persons": self.number_of_persons,
            "time_duration": self.time_duration,
            "source_url": self.source_url,
            "ingredients": self.ingredients_source,
            "preparation_steps": self.preparation_steps
        }
        return info_dict

    def data_to_database(self):
        """
        Create SQLite database tables and insert parsed data into the tables.
        """
        conn = sqlite3.connect('recipe_database.db')
        cursor = conn.cursor()

        try:
            self.recipe_info_to_table(cursor)
            self.ingredients_to_table(cursor)
            self.prep_steps_to_table(cursor)
            print(f'{self.recipe_name} from {self.recipe_source} saved to database.')

        except sqlite3.IntegrityError as e:
            # Catch the 'UNIQUE constraint failed' error
            print(f"SQLite Error: {e}")
            print("Failed to insert record due to duplicate name.")

        conn.commit()
        conn.close()

    def recipe_info_to_table(self, cursor):
        """
        Create the RecipeInfo table.
        """
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS RecipeInfo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                number_of_persons TEXT,
                time_duration TEXT,
                source_url TEXT
            )
        ''')
        cursor.execute('INSERT INTO RecipeInfo (name, description, number_of_persons, time_duration, source_url) VALUES (?, ?, ?, ?, ?)',
                       (self.recipe_name, self.recipe_description, self.number_of_persons, self.time_duration, self.source_url))
        self.recipe_id = cursor.lastrowid

    def ingredients_to_table(self, cursor):
        """
        Create the Ingredients table.
        """
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient TEXT,
                amount TEXT,
                unit TEXT,
                ingredient_source TEXT,
                recipe_id INTEGER,
                FOREIGN KEY (recipe_id) REFERENCES RecipeInfo (id)
            )
        ''')
        for raw_ingredient in self.ingredients_source:
            self.insert_ingredient(cursor, raw_ingredient)

    def insert_ingredient(self, cursor, raw_ingredient):
        """
        Insert an ingredient into the Ingredients table.
        """
        amount, unit, ingredient = self.parse_amount_unit_ingredient(
            raw_ingredient)
        ingredient = ingredient if ingredient is not None else 'Unknown Ingredient'
        amount = amount if amount is not None else 0
        unit = unit if unit is not None else 'Unknown Unit'
        cursor.execute(
            'INSERT INTO Ingredients (ingredient, amount, unit, ingredient_source, recipe_id) VALUES (?, ?, ?, ?, ?)', (ingredient, amount, unit, raw_ingredient, self.recipe_id))

    def prep_steps_to_table(self, cursor):
        """
        Create the Preparation table.
        """
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Preparation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                step TEXT,
                recipe_id INTEGER,
                FOREIGN KEY (recipe_id) REFERENCES RecipeInfo (id)
            )
        ''')
        for step in self.preparation_steps:
            cursor.execute(
                'INSERT INTO Preparation (step, recipe_id) VALUES (?, ?)', (step, self.recipe_id))

    def save_recipe_image(self):
        """
        Save the recipe image to a specified folder.

        Parameters:
        - config_key (str): The key to identify the configuration for image retrieval in the config file.
                            Default is 'image_config' assuming it's present in the config file.
        """
        # Get the image configuration from the config file
        image_config = self.config_loader.get_images_config(self.recipe_source)

        # Extract values from the image configuration
        image_folder = image_config.get('image_folder')
        image_container_selector = image_config.get('image_container_selector')
        image_tag_selector = image_config.get('image_tag_selector')
        image_name_attribute = image_config.get('image_name_attribute')

        # Find the <div> tag within the specified container using the provided selector
        image_container_div = self.soup.select_one(image_container_selector)

        if image_container_div:
            # Find the <img> tag within the image container using the provided selector
            image_tag = image_container_div.select_one(image_tag_selector)

            if image_tag:
                # Get the image URL and name using the provided attributes
                image_url = image_tag['src']
                image_name = image_tag[image_name_attribute]

                # Ensure the image folder exists, if not, create it
                if not os.path.exists(image_folder):
                    os.makedirs(image_folder)
                else:
                    # Save the image
                    image_path = os.path.join(
                        image_folder, f"{image_name}.jpg")
                    response = requests.get(image_url)

                with open(image_path, 'wb') as image_file:
                    image_file.write(response.content)
            else:
                print("No image tag found in the image container.")
        else:
            print("No div tag found for image container.")

    def parse_recipe_info(self):
        """
        Parse and extract specific recipe information from the HTML content using soup.select_one.
        if there is no config found in the config file an exception will be raised.
        if there is no data found from the html content none will be returned.

        Parameters:
        - config_key (str): The key to identify the configuration for parsing recipe information.
        """
        config = self.config_loader.get_recipe_info_config(self.recipe_source)

        # Extract each piece of information from the config
        try:
            name = config.get("recipe_name")
            if name is None:
                raise Exception("Missing 'recipe_name' configuration.")

            description = config.get("recipe_description")
            if description is None:
                raise Exception("Missing 'recipe_description' configuration.")

            persons = config.get("recipe_persons")
            if persons is None:
                raise Exception("Missing 'recipe_persons' configuration.")

            time = config.get("recipe_time")
            if time is None:
                raise Exception("Missing 'recipe_time' configuration.")
        except Exception as e:
            print("\n############### ERROR in parse_recipe_info() #################")
            print(e)
            print("############### ERROR ########################################\n")

        # Extract data from the HTML based on the configurations
        r_name = self.soup.select_one(name)
        if r_name:
            self.recipe_name = r_name.get_text(strip=True)
        else:
            self.recipe_name = None

        r_persons = self.soup.select_one(persons)
        if r_persons:
            self.number_of_persons = r_persons.get_text(strip=True)
        else:
            self.number_of_persons = None

        r_time = self.soup.select_one(time)
        if r_time:
            self.time_duration = r_time.get_text(strip=True)
        else:
            self.time_duration = None

    def parse_ingredients(self):
        """
        Parse and extract ingredient information from the HTML content.

        Parameters:
        - config_key (str): The key to identify the configuration for parsing ingredients.
        """
        config = self.config_loader.get_ingredients_config(self.recipe_source)

        # Extract locator from the config file
        try:
            ingredients = config.get("recipe_ingredients")
            if ingredients is None:
                raise Exception("Missing 'recipe_ingredients' configuration.")
        except Exception as e:
            print("\n############### ERROR in parse_ingredients() #################")
            print(e)
            print("############### ERROR ########################################\n")

        ingredients_section = self.soup.select_one(ingredients)

        if ingredients_section:
            ingredients_list = ingredients_section.find_all('li')
            self.ingredients_source = [step.get_text(
                strip=True) for step in ingredients_list]
        else:
            self.ingredients_source = []

    def parse_preparation_steps(self):
        """
        Parse and extract preparation steps from the HTML content.

        Parameters:
        - config_key (str): The key to identify the configuration for parsing preparation steps.
        """
        config = self.config_loader.get_preparation_config(self.recipe_source)

        # Extract locator from the config file
        try:
            steps = config.get("recipe_prepration")
            if steps is None:
                raise Exception("Missing 'recipe_ingredients' configuration.")
        except Exception as e:
            print(
                "\n############### ERROR in parse_preparation_steps() #################")
            print(e)
            print("############### ERROR ########################################\n")

        preparation_section = self.soup.select_one(steps)

        if "script" in steps:
            # Extract the JSON content
            json_str = preparation_section.string
            try:
                # Clean the JSON string (remove extra whitespace and invalid characters)
                json_str_cleaned = json_str.strip().replace(
                    '\n', '').replace('\r', '').replace('\t', '')
                # Parse the JSON content
                data_dict = json.loads(json_str_cleaned)
                self.preparation_steps = data_dict.get(
                    "recipeInstructions", [])

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return None

        else:
            if preparation_section:
                preparation_list = preparation_section.find_all('li')
                self.preparation_steps = [step.get_text(
                    strip=True) for step in preparation_list]
            else:
                self.preparation_steps = []

    def parse_amount_unit_ingredient(self, ingredient):
        """
        Parse and extract the amount, unit and ingredient from a given ingredient.
        Parameters:
        - ingredient (str): The ingredient to parse.
        Returns:
        - tuple: The amount, unit and ingredient.
        """
        # Split the ingredient into a list of words
        ingredient_list = ingredient.split()
        # Check if the ingredient list is not empty
        if ingredient_list:
            # Check if the first word is a number
            if ingredient_list[0].isnumeric():
                # Extract the amount and unit
                amount = ingredient_list[0]
                if len(ingredient_list[1]) >= 5:
                    unit = None
                    ingredient = ' '.join(ingredient_list[1:])
                else:
                    unit = ingredient_list[1]
                    # Extract the ingredient
                    ingredient = ' '.join(ingredient_list[2:])
            else:
                # Extract the ingredient
                ingredient = ' '.join(ingredient_list)
                amount = 1
                unit = None
        else:
            amount = 1
            unit = None
        return amount, unit, ingredient


class ConfigLoader:
    """
    Parameters:
    - config_file (str): The path to the configuration file. Default is 'config.json'.
    """

    def __init__(self):
        self.config_file = self.find_config_file()
        self.config_data = self.load_config()

    def find_config_file(self):
        root_dir = os.path.dirname(os.path.abspath(__file__))
        for dirpath, dirnames, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename == 'config.json':
                    return os.path.join(dirpath, filename)
        return None  # File not found

    def load_config(self):
        """
        Load configuration data from the specified configuration file.

        Returns:
        - dict: The loaded configuration data.
        """
        with open(self.config_file, 'r') as file:
            return json.load(file)

    def get_recipe_info_config(self, source_recipe):
        """ Retrieves a dict with the locator to get the information of the recipe from the url
        Args:
            source_recipe (string): The name of the website where the recipe is located

        Returns:
            dict: a dict with the information of the recipe
        """

        data = self.config_data.get(source_recipe, {})

        # Extract recipe information
        if data:
            recipe_info = data.get("recipe_info_config", {})

        return recipe_info

    def get_preparation_config(self, source_recipe):
        """ Retrieves a dict with the locator to get the preparations of the recipe from the url
        Args:
            source_recipe (string): The name of the website where the recipe is located

        Returns:
            dict: a dict with the information of the recipe
        """

        data = self.config_data.get(source_recipe, {})

        # Extract preparation steps dict
        if data:
            recipe_info = data.get("preparation_config", {})

        return recipe_info

    def get_ingredients_config(self, source_recipe):
        """ Retrieves a dict with the locator to get the ingredients of the recipe from the url
        Args:
            source_recipe (string): The name of the website where the recipe is located

        Returns:
            dict: a dict with the information of the recipe
        """

        data = self.config_data.get(source_recipe, {})

        # Extract ingredients dict
        if data:
            recipe_info = data.get("ingredients_config", {})

        return recipe_info

    def get_images_config(self, source_recipe):
        """
        Get the image configuration for a specific key.

        Parameters:
        - config_key (str): The key to identify the configuration.

        Returns:
        - dict: The preparation configuration.
        """
        data = self.config_data.get(source_recipe, {})
        if data:
            folder_config = data.get("image_config", {})

        return folder_config


if __name__ == "__main__":

    config_loader = ConfigLoader()

    while True:
        user_url1 = input("Enter the url of the recipe: ")
        recipe_site = input("Enter the name of the recipe site: ")
        recipe = RecipeParser(
            url=user_url1, config_loader=config_loader, recipe_source=recipe_site)
        
        recipe.parse_recipe_info()
        recipe.parse_ingredients()
        recipe.parse_preparation_steps()
        recipe.get_recipe_info()

        recipe.data_to_database()
        recipe.save_recipe_image()
