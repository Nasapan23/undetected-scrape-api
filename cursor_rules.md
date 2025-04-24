# Cursor Rules for Undetectable Web Scraping API

## Project Structure
```
undetected-scrape-api/
├── app/
│   ├── __init__.py           # Flask app initialization
│   ├── routes/
│   │   ├── __init__.py
│   │   └── scrape.py         # Scraping endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── browser.py        # Playwright browser service
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── error_handler.py  # Error handling utilities
│   │   └── logging.py        # Logging utilities
├── config/
│   ├── __init__.py
│   └── settings.py           # Configuration settings
├── tests/
│   ├── __init__.py
│   ├── test_routes/
│   └── test_services/
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore file
├── requirements.txt          # Project dependencies
├── run.py                    # Application entry point
└── README.md                 # Project documentation
```

## Coding Standards

### General
- Follow PEP 8 style guide for Python code
- Use meaningful variable and function names
- Keep functions small and focused on a single responsibility
- Document code with docstrings
- Use type hints where appropriate

### Flask Best Practices
- Use Flask Blueprints for route organization
- Implement proper error handling
- Use environment variables for configuration
- Follow RESTful API design principles

### Testing
- Write unit tests for all services and utilities
- Write integration tests for API endpoints
- Aim for high test coverage

### Anti-Detection Measures
- Encapsulate browser fingerprinting logic in dedicated services
- Maintain clean separation between scraping logic and anti-detection measures
- Design for easy configuration of randomization parameters

### Security
- Don't commit sensitive information to version control
- Validate and sanitize all user inputs
- Implement rate limiting to prevent abuse
- Use proper exception handling to avoid exposing implementation details

### Performance
- Use async where appropriate for better concurrency
- Implement caching where beneficial
- Monitor and optimize resource usage

## Git Workflow
- Use feature branches for new functionality
- Write descriptive commit messages
- Perform code reviews before merging

## Documentation
- Keep README up to date with setup instructions and usage examples
- Document API endpoints with examples
- Include comments explaining complex logic or algorithms 