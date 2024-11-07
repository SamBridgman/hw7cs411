import pytest
from contextlib import contextmanager
import re
import sqlite3
from dataclasses import dataclass
from meal_max.models.kitchen_model import *


# Mocking the database connection for tests

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_cursor.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test


def test_meal_initialization_valid_data():
    # Test creating a meal with valid data
    meal = Meal(id=1, meal="Pizza", cuisine="Italian", price=15.0, difficulty="MED")
    assert meal.id == 1
    assert meal.meal == "Pizza"
    assert meal.cuisine == "Italian"
    assert meal.price == 15.0
    assert meal.difficulty == "MED"

def test_meal_initialization_invalid_price():
    # Test that an invalid price (negative) raises a ValueError
    try:
        Meal(id=2, meal="Sushi", cuisine="Japanese", price=-5.0, difficulty="HIGH")
    except ValueError as e:
        assert str(e) == "Price must be a positive value."

def test_meal_initialization_invalid_difficulty():
    # Test that an invalid difficulty raises a ValueError
    try:
        Meal(id=3, meal="Burger", cuisine="American", price=10.0, difficulty="EASY")
    except ValueError as e:
        assert str(e) == "Difficulty must be 'LOW', 'MED', or 'HIGH'."

def test_meal_initialization_boundary_price():
    # Test that a zero price raises a ValueError
    try:
        Meal(id=4, meal="Salad", cuisine="Vegetarian", price=0.0, difficulty="LOW")
    except ValueError as e:
        assert str(e) == "Price must be a positive value."

def test_meal_initialization_valid_difficulties():
    # Test valid difficulties
    for difficulty in ["LOW", "MED", "HIGH"]:
        meal = Meal(id=5, meal="Pasta", cuisine="Italian", price=12.0, difficulty=difficulty)
        assert meal.difficulty == difficulty


#################################################
        
def test_create_meal(mock_cursor):
    """Test creating a new meal in the catalog."""

    # Call the function to create a new meal
    create_meal(meal="Meal Name", cuisine="Cuisine Type", price=10.99, difficulty="MED")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name", "Cuisine Type", 10.99, "MED")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_create_meal_invalid_price(mock_cursor):
    """Test creating a meal with an invalid price."""
    with pytest.raises(ValueError, match="Invalid price: -10.99. Price must be a positive number."):
        create_meal(meal="Meal Name", cuisine="Italian", price=-10.99, difficulty="MED")


def test_create_meal_invalid_difficulty(mock_cursor):
    """Test creating a meal with an invalid difficulty level."""
    with pytest.raises(ValueError, match="Invalid difficulty level: EASY. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Meal Name", cuisine="Italian", price=10.99, difficulty="EASY")


def test_create_meal_duplicate_name(mock_cursor):
    """Test creating a meal that already exists in the database."""
    mock_cursor.execute.side_effect = sqlite3.IntegrityError  # Simulate duplicate entry
    with pytest.raises(ValueError, match="Meal with name 'Meal Name' already exists"):
        create_meal(meal="Meal Name", cuisine="Italian", price=10.99, difficulty="MED")

        
###############################################################

def test_delete_meal_success(mock_cursor):
    """Test successfully deleting a meal."""
    mock_cursor.fetchone.return_value = [(False)]  # Meal is not deleted

    # Create the meal directly before attempting to delete it
    delete_meal(1)
    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."


def test_delete_meal_already_deleted(mock_cursor):
    """Test trying to delete a meal that has already been marked as deleted."""
    meal_id = 1
    mock_cursor.fetchone.return_value = (True,)  # Meal is already deleted

    with pytest.raises(ValueError, match=f"Meal with ID {meal_id} has been deleted"):
        delete_meal(meal_id)


def test_delete_meal_not_found(mock_cursor):
    """Test trying to delete a meal that does not exist."""
    meal_id = 1
    mock_cursor.fetchone.side_effect = TypeError()  # Simulate meal not found

    with pytest.raises(ValueError, match=f"Meal with ID {meal_id} not found"):
        delete_meal(meal_id)

################################################################
        
def test_get_leaderboard_sorted_by_wins(mock_cursor):
    """Test retrieving the leaderboard sorted by wins."""
    mock_cursor.fetchall.return_value = [
        (1, 'Meal 1', 'Cuisine 1', 10.0, 'LOW', 5, 4, 0.8),
        (2, 'Meal 2', 'Cuisine 2', 15.0, 'MED', 3, 2, 0.67),
    ]

    expected_leaderboard = [
        {'id': 1, 'meal': 'Meal 1', 'cuisine': 'Cuisine 1', 'price': 10.0, 'difficulty': 'LOW', 'battles': 5, 'wins': 4, 'win_pct': 80.0},
        {'id': 2, 'meal': 'Meal 2', 'cuisine': 'Cuisine 2', 'price': 15.0, 'difficulty': 'MED', 'battles': 3, 'wins': 2, 'win_pct': 67.0},
    ]

    result = get_leaderboard("wins")
    assert result == expected_leaderboard, "The leaderboard did not match the expected results."

def test_get_leaderboard_sorted_by_win_pct(mock_cursor):
    """Test retrieving the leaderboard sorted by win percentage."""
    mock_cursor.fetchall.return_value = [
        (1, 'Meal 1', 'Cuisine 1', 10.0, 'LOW', 5, 4, 0.8),
        (2, 'Meal 2', 'Cuisine 2', 15.0, 'MED', 3, 2, 0.67),
    ]

    expected_leaderboard = [
        {'id': 1, 'meal': 'Meal 1', 'cuisine': 'Cuisine 1', 'price': 10.0, 'difficulty': 'LOW', 'battles': 5, 'wins': 4, 'win_pct': 80.0},
        {'id': 2, 'meal': 'Meal 2', 'cuisine': 'Cuisine 2', 'price': 15.0, 'difficulty': 'MED', 'battles': 3, 'wins': 2, 'win_pct': 67.0},
    ]

    result = get_leaderboard("win_pct")
    assert result == expected_leaderboard, "The leaderboard did not match the expected results."

def test_get_leaderboard_invalid_sort_by(mock_cursor):
    """Test handling an invalid sort_by parameter."""
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid"):
        get_leaderboard(sort_by="invalid")



#########################################################################################
        
def test_get_meal_by_id_success(mock_cursor):
    """Test retrieving a meal by ID successfully."""
    meal_id = 1
    mock_cursor.fetchone.return_value = (meal_id, 'Meal 1', 'Cuisine 1', 10.0, 'LOW', False)

    result = get_meal_by_id(meal_id)

    expected_meal = Meal(id=meal_id, meal='Meal 1', cuisine='Cuisine 1', price=10.0, difficulty='LOW')
    assert result == expected_meal, "The retrieved meal did not match the expected result."

def test_get_meal_by_id_deleted(mock_cursor):
    """Test retrieving a meal that has been marked as deleted."""
    meal_id = 1
    mock_cursor.fetchone.return_value = (meal_id, 'Meal 1', 'Cuisine 1', 10.0, 'LOW', True)

    with pytest.raises(ValueError, match=f"Meal with ID {meal_id} has been deleted"):
        get_meal_by_id(meal_id)


def test_get_meal_by_id_not_found(mock_cursor):
    """Test retrieving a meal that does not exist."""
    meal_id = 1
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match=f"Meal with ID {meal_id} not found"):
        get_meal_by_id(meal_id)

#################################################################
        
def test_get_meal_by_name_found(mock_cursor):
    """Test getting a meal by name when it exists."""
    meal_name = "Pizza"
    mock_cursor.fetchone.return_value = (1, meal_name, "Italian", 12.99, "LOW", False)  # Meal is found and not deleted

    meal = get_meal_by_name(meal_name)

    assert meal.id == 1
    assert meal.meal == meal_name
    assert meal.cuisine == "Italian"
    assert meal.price == 12.99
    assert meal.difficulty == "LOW"


def test_get_meal_by_name_deleted(mock_cursor):
    """Test getting a meal by name when it has been marked as deleted."""
    meal_name = "Burger"
    mock_cursor.fetchone.return_value = (2, meal_name, "American", 8.99, "MED", True)  # Meal is deleted

    with pytest.raises(ValueError, match=f"Meal with name {meal_name} has been deleted"):
        get_meal_by_name(meal_name)


def test_get_meal_by_name_not_found(mock_cursor):
    """Test getting a meal by name that does not exist."""
    meal_name = "Sushi"
    mock_cursor.fetchone.return_value = None  # Meal not found

    with pytest.raises(ValueError, match=f"Meal with name {meal_name} not found"):
        get_meal_by_name(meal_name)

###########################################################


def test_update_meal_stats_win(mock_cursor):
    """Test updating meal stats for a win."""
    meal_id = 1
    mock_cursor.fetchone.return_value = [False]  # Meal is not deleted

    update_meal_stats(meal_id, 'win')

    # Expected SQL query for updating meal stats
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_loss(mock_cursor):
    """Test updating meal stats for a loss."""
    meal_id = 2
    mock_cursor.fetchone.return_value = [False]  # Meal is not deleted

    update_meal_stats(meal_id, 'loss')

    # Expected SQL query for updating meal stats
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])  # Change index to 0

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]  # Change index to 0

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_update_meal_stats_deleted(mock_cursor):
    """Test updating stats for a meal that has been marked as deleted."""
    meal_id = 3
    mock_cursor.fetchone.return_value = (True,)  # Meal is deleted

    with pytest.raises(ValueError, match=f"Meal with ID {meal_id} has been deleted"):
        update_meal_stats(meal_id, 'win')

def test_update_meal_stats_not_found(mock_cursor):
    """Test updating stats for a meal that does not exist."""
    meal_id = 4
    mock_cursor.fetchone.return_value = None  # Meal not found

    with pytest.raises(ValueError, match=f"Meal with ID {meal_id} not found"):
        update_meal_stats(meal_id, 'win')

def test_update_meal_stats_invalid_result(mock_cursor):
    """Test updating stats with an invalid result input."""
    meal_id = 5
    mock_cursor.fetchone.return_value = (False,)  # Meal is not deleted

    with pytest.raises(ValueError, match="Invalid result: invalid_result. Expected 'win' or 'loss'."):
        update_meal_stats(meal_id, 'invalid_result')