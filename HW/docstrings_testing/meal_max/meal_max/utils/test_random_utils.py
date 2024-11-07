from unittest.mock import patch, MagicMock
import requests
import pytest
from meal_max.utils.random_utils import get_random


@patch('meal_max.utils.random_utils.requests.get')
def test_get_random_success(mock_get):
    """Test fetching a random number successfully."""
    # Simulate a successful response with a valid decimal number
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "0.45\n"
    mock_get.return_value = mock_response

    result = get_random()
    assert abs(result - 0.45) < 0.01, f"Expected 0.45, got {result}"
    mock_get.assert_called_once_with("https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new", timeout=5)

@patch('meal_max.utils.random_utils.requests.get')
def test_get_random_invalid_response(mock_get):
    """Test fetching a random number with an invalid response that raises ValueError."""
    # Simulate a response with invalid text
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "invalid_text"
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="Invalid response from random.org: invalid_text"):
        get_random()
    
    mock_get.assert_called_once_with("https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new", timeout=5)

@patch('meal_max.utils.random_utils.requests.get')
def test_get_random_timeout(mock_get):
    """Test fetching a random number with a request timeout that raises RuntimeError."""
    # Simulate a timeout exception
    mock_get.side_effect = requests.exceptions.Timeout

    with pytest.raises(RuntimeError, match="Request to random.org timed out."):
        get_random()
    
    mock_get.assert_called_once_with("https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new", timeout=5)


@patch('meal_max.utils.random_utils.requests.get')
def test_get_random_request_exception(mock_get):
    """Test fetching a random number with a general request exception that raises RuntimeError."""
    # Simulate a general request exception
    mock_get.side_effect = requests.exceptions.RequestException("Network error")

    with pytest.raises(RuntimeError, match="Request to random.org failed: Network error"):
        get_random()
    
    mock_get.assert_called_once_with("https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new", timeout=5)