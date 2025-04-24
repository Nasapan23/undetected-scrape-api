"""
Tests for browser service
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.browser import get_user_agent, USER_AGENTS

def test_get_user_agent():
    """
    Test the user agent rotation functionality
    """
    # Test with rotation enabled
    with patch('app.services.browser.current_app') as mock_app:
        mock_app.config.get.return_value = True
        user_agent = get_user_agent()
        assert user_agent in USER_AGENTS
        mock_app.config.get.assert_called_once_with('USER_AGENT_ROTATION', True)
    
    # Test with rotation disabled
    with patch('app.services.browser.current_app') as mock_app:
        mock_app.config.get.return_value = False
        user_agent = get_user_agent()
        assert user_agent == USER_AGENTS[0]
        mock_app.config.get.assert_called_once_with('USER_AGENT_ROTATION', True) 