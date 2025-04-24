"""
Advanced Cloudflare bypass utilities for handling various challenge scenarios.
"""
import re
import time
import random
from loguru import logger
from pathlib import Path
from typing import Optional, Dict, Any

# Cloudflare detection patterns in multiple languages
CF_CHALLENGE_PATTERNS = {
    'en': [
        r"Checking your browser before accessing",
        r"This process is automatic",
        r"Please enable Cookies and reload the page",
        r"Please wait while we check your browser",
        r"DDoS protection by"
    ],
    'it': [
        r"Controllo del browser in corso prima di accedere",
        r"Questo processo è automatico",
        r"Si prega di abilitare i cookie e ricaricare la pagina",
        r"Controlla di essere un umano"
    ],
    'fr': [
        r"Vérification de votre navigateur avant d'accéder",
        r"Ce processus est automatique",
        r"Merci d'activer les cookies et de recharger la page"
    ],
    'de': [
        r"Überprüfung Ihres Browsers bevor Sie zugreifen",
        r"Dieser Vorgang ist automatisch",
        r"Bitte aktivieren Sie Cookies und laden Sie die Seite neu"
    ],
    'es': [
        r"Comprobando su navegador antes de acceder",
        r"Este proceso es automático",
        r"Habilite las cookies y vuelva a cargar la página"
    ]
}

# Captcha detection patterns
CAPTCHA_PATTERNS = [
    r"captcha",
    r"CAPTCHA",
    r"Captcha",
    r"hcaptcha",
    r"recaptcha",
    r"cloudflare turnstile"
]

def is_cloudflare_challenge(content: str) -> bool:
    """
    Detect if the response contains a Cloudflare challenge page in any language.
    
    Args:
        content: HTML content of the page
        
    Returns:
        bool: True if a Cloudflare challenge is detected
    """
    # Check for each language's patterns
    for language, patterns in CF_CHALLENGE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                logger.warning(f"Cloudflare challenge detected! Language: {language}")
                return True
    
    return False

def has_captcha(content: str) -> bool:
    """
    Detect if the page contains a CAPTCHA challenge.
    
    Args:
        content: HTML content of the page
        
    Returns:
        bool: True if a CAPTCHA is detected
    """
    for pattern in CAPTCHA_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            logger.warning("CAPTCHA detected on the page!")
            return True
    
    return False

def detect_cloudflare_status(content: str) -> Dict[str, bool]:
    """
    Comprehensive detection of Cloudflare challenge status.
    
    Args:
        content: HTML content of the page
        
    Returns:
        Dict with detection results
    """
    return {
        "is_challenge": is_cloudflare_challenge(content),
        "has_captcha": has_captcha(content),
        "is_blocked": "Access denied" in content or "You are being rate limited" in content
    }

async def perform_cloudflare_bypass(page, url: str, advanced: bool = False) -> bool:
    """
    Attempt to bypass Cloudflare protection on a page.
    
    Args:
        page: Playwright page object
        url: URL to access
        advanced: Whether to use advanced bypass techniques
        
    Returns:
        bool: True if bypass was successful
    """
    logger.info(f"Attempting to bypass Cloudflare protection for {url}")
    
    # Initial loading of the page
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        logger.error(f"Error loading page: {e}")
        return False
    
    # Get page content
    content = await page.content()
    
    # Check if we're facing a Cloudflare challenge
    status = detect_cloudflare_status(content)
    
    if not status["is_challenge"] and not status["has_captcha"]:
        logger.info("No Cloudflare challenge detected, page loaded successfully")
        return True
        
    logger.warning("Cloudflare challenge detected, attempting bypass...")
    
    # Basic waiting strategy for automatic challenges
    await page.wait_for_timeout(random.uniform(4000, 6000))
    
    # Sometimes we need to interact with the page
    try:
        # Look for specific elements to interact with
        if await page.query_selector('#challenge-stage') is not None:
            logger.info("Found challenge stage, waiting for it to complete...")
            await page.wait_for_timeout(random.uniform(8000, 10000))
        
        # Check for "I am human" verification
        verify_button = await page.query_selector('text="Verify you are human"')
        if verify_button:
            logger.info("Found verify button, clicking...")
            await verify_button.click()
            await page.wait_for_timeout(random.uniform(2000, 3000))
    except Exception as e:
        logger.error(f"Error during interaction: {e}")
    
    # Advanced bypass techniques if requested
    if advanced:
        try:
            # Simulate mouse movements
            for _ in range(3):
                await page.mouse.move(
                    random.randint(100, 500), 
                    random.randint(100, 500),
                    steps=random.randint(5, 10)
                )
            
            # Scroll down slightly to trigger any lazy-loaded scripts
            await page.evaluate("window.scrollBy(0, 100)")
            await page.wait_for_timeout(1000)
            
            # Focus on the body to simulate user presence
            await page.focus('body')
            await page.wait_for_timeout(2000)
        except Exception as e:
            logger.error(f"Error in advanced techniques: {e}")
    
    # Check if bypass was successful
    content = await page.content()
    final_status = detect_cloudflare_status(content)
    
    if not final_status["is_challenge"] and not final_status["has_captcha"]:
        logger.success("Successfully bypassed Cloudflare protection!")
        return True
    else:
        logger.error("Failed to bypass Cloudflare protection.")
        return False

async def wait_for_navigation_after_challenge(page, timeout: int = 30000) -> bool:
    """
    Wait for navigation to complete after a Cloudflare challenge.
    
    Args:
        page: Playwright page object
        timeout: Maximum time to wait in milliseconds
        
    Returns:
        bool: True if navigation completed successfully
    """
    try:
        # Wait for network to be idle, indicating the page has fully loaded
        await page.wait_for_load_state("networkidle", timeout=timeout)
        
        # Double-check that we're not still on a challenge page
        content = await page.content()
        status = detect_cloudflare_status(content)
        
        return not status["is_challenge"] and not status["has_captcha"]
    except Exception as e:
        logger.error(f"Error waiting for navigation: {e}")
        return False 