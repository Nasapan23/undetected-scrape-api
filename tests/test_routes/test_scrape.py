"""
Tests for the scrape endpoint
"""
import pytest
from app import create_app

@pytest.fixture
def client():
    """
    Test client fixture
    """
    app = create_app({"TESTING": True})
    
    with app.test_client() as client:
        yield client

def test_scrape_missing_url(client):
    """
    Test scraping without a URL parameter
    """
    response = client.get("/scrape/")
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "URL parameter is required" in data["message"]

def test_index_route(client):
    """
    Test the index route
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "Undetectable Web Scraping API is running" in data["message"] 