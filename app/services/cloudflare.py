"""
Specialized Cloudflare challenge handling and bypass techniques
"""
import os
import random
import time
import re
from loguru import logger
from pathlib import Path
import json

# List of Cloudflare challenge types
CHALLENGE_TYPES = {
    "JS_CHALLENGE": "js_challenge",
    "CAPTCHA": "captcha",
    "TURNSTILE": "turnstile",
    "FIREWALL": "firewall",
    "UAM": "uam",  # Under Attack Mode
    "WAITING_ROOM": "waiting_room"
}

# Cloudflare challenge selectors
CF_SELECTORS = {
    "checkbox": [
        "input[type='checkbox']", 
        ".cf-checkbox", 
        "[data-testid='challenge-checkbox']",
        "#challenge-stage input",
        "[data-sitekey]",
        "#challenge-checkbox",
        "iframe[src*='challenges']"
    ],
    "turnstile": [
        ".cf-turnstile",
        "iframe[src*='challenges/turnstile']",
        "iframe[src*='turnstile']",
        "[data-sitekey]"
    ],
    "captcha": [
        ".g-recaptcha",
        ".h-captcha",
        "[data-sitekey]",
        "iframe[src*='captcha']",
        "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']"
    ],
    "challenge_content": [
        "#challenge-stage",
        "#challenge-body",
        "#challenge-running",
        "#challenge-form",
        "#challenge-error-title",
        ".ray-id",
        ".cf-error-code",
        ".cf-browser-verification",
        "#cf-please-wait",
        "#challenge-spinner",
        "#trk_jschal_js"
    ]
}

# Phrases that indicate Cloudflare in various languages
CF_INDICATORS = {
    "english": [
        "cloudflare", "checking your browser", "security check", 
        "please wait", "please stand by", "one moment",
        "challenge", "enabled for security reasons", "protect against",
        "automated", "protection", "attention required"
    ],
    "italian": [
        "ci siamo quasi", "dimostra di essere un utente umano", "controllo aggiuntivo",
        "prestazioni e sicurezza", "ray id", "cloudflare", "completando l'azione"
    ],
    "spanish": [
        "comprueba que eres humano", "estamos comprobando", "un momento",
        "atención necesaria", "desafío de seguridad", "cloudflare"
    ],
    "french": [
        "vérification", "prouvez que vous êtes humain", "nous vérifions",
        "cloudflare", "contrôle de sécurité", "attention requise"
    ],
    "german": [
        "überprüfung", "mensch", "sicherheitsabfrage", "cloudflare",
        "bitte warten", "einen moment", "sicherheitsgründen"
    ]
}

class CloudflareConfig:
    """Configuration for Cloudflare bypass"""
    # Time to wait for Cloudflare challenge to process
    INITIAL_WAIT_TIME = int(os.getenv("CLOUDFLARE_WAIT_TIME", 7000))  # ms
    
    # Max number of bypass attempts per challenge
    MAX_BYPASS_ATTEMPTS = int(os.getenv("CLOUDFLARE_RETRY_ATTEMPTS", 3))
    
    # Extended wait time for stubborn challenges
    EXTENDED_WAIT = float(os.getenv("CLOUDFLARE_EXTENDED_WAIT", 20.0))  # seconds
    
    # Whether to persist cookies between runs
    PERSIST_COOKIES = os.getenv("CLOUDFLARE_COOKIES_PERSIST", "true").lower() == "true"
    
    # Cookie storage directory
    COOKIE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cookies")
    
    # Make sure cookie dir exists
    os.makedirs(COOKIE_DIR, exist_ok=True)

def detect_challenge_type(page):
    """
    Detect what type of Cloudflare challenge we're facing
    
    Args:
        page: Playwright page object
        
    Returns:
        str: Challenge type from CHALLENGE_TYPES or None
    """
    # First check URL and title
    url = page.url.lower()
    title = page.title().lower()
    content = page.inner_text("body").lower()
    
    # Check for explicit Cloudflare indicators first
    if "cloudflare" not in url and "cloudflare" not in title and "cloudflare" not in content:
        # Quick check if this contains common CF text in different languages
        has_cf_text = False
        for lang, phrases in CF_INDICATORS.items():
            for phrase in phrases:
                if phrase in title or phrase in content:
                    has_cf_text = True
                    break
            if has_cf_text:
                break
                
        if not has_cf_text:
            return None
    
    # Now determine the challenge type
    if any(page.query_selector(selector) for selector in CF_SELECTORS["turnstile"]):
        return CHALLENGE_TYPES["TURNSTILE"]
        
    if any(page.query_selector(selector) for selector in CF_SELECTORS["captcha"]):
        return CHALLENGE_TYPES["CAPTCHA"]
    
    if any(page.query_selector(selector) for selector in CF_SELECTORS["checkbox"]):
        return CHALLENGE_TYPES["JS_CHALLENGE"]
        
    # Check if it's the waiting room
    if "waiting room" in content or "queue" in content or "wait" in title:
        return CHALLENGE_TYPES["WAITING_ROOM"]
        
    # Generic JS challenge
    if "challenge" in content or "challenge" in url:
        return CHALLENGE_TYPES["JS_CHALLENGE"]
        
    # UAM (Under Attack Mode)
    if "attack" in content or "attack" in title or "security" in title:
        return CHALLENGE_TYPES["UAM"]
        
    # Default to JS challenge if we detected Cloudflare but can't pin down the type
    return CHALLENGE_TYPES["JS_CHALLENGE"]

def save_cf_cookies(page, domain):
    """
    Save Cloudflare cookies for future use
    
    Args:
        page: Playwright page
        domain: Domain to save cookies for
    """
    if not CloudflareConfig.PERSIST_COOKIES:
        return False
        
    try:
        cookies = page.context.cookies()
        if not cookies:
            return False
            
        # Filter for Cloudflare cookies or cookies from this domain
        cf_cookies = [c for c in cookies if 
                     "cloudflare" in c.get("name", "").lower() or 
                     "cf_" in c.get("name", "").lower() or
                     domain in c.get("domain", "")]
        
        if not cf_cookies:
            return False
            
        # Create filename based on domain
        domain_clean = domain.replace(".", "_").replace(":", "_")
        cookie_file = os.path.join(CloudflareConfig.COOKIE_DIR, f"{domain_clean}_cookies.json")
        
        # Save cookies to file
        with open(cookie_file, 'w') as f:
            json.dump(cf_cookies, f)
            
        logger.info(f"Saved {len(cf_cookies)} Cloudflare cookies for {domain}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving Cloudflare cookies: {e}")
        return False

def load_cf_cookies(page, domain):
    """
    Load saved Cloudflare cookies
    
    Args:
        page: Playwright page
        domain: Domain to load cookies for
        
    Returns:
        bool: True if cookies were loaded successfully
    """
    if not CloudflareConfig.PERSIST_COOKIES:
        return False
        
    try:
        # Create filename based on domain
        domain_clean = domain.replace(".", "_").replace(":", "_")
        cookie_file = os.path.join(CloudflareConfig.COOKIE_DIR, f"{domain_clean}_cookies.json")
        
        if not os.path.exists(cookie_file):
            return False
            
        # Load cookies from file
        with open(cookie_file, 'r') as f:
            cookies = json.load(f)
            
        if cookies:
            page.context.add_cookies(cookies)
            logger.info(f"Loaded {len(cookies)} saved Cloudflare cookies for {domain}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error loading Cloudflare cookies: {e}")
        return False

def extract_domain(url):
    """Extract domain from URL"""
    match = re.search(r'https?://([^/]+)', url)
    if match:
        return match.group(1)
    return None

async def solve_js_challenge(page):
    """
    Try to solve JavaScript challenge
    
    Args:
        page: Playwright page
        
    Returns:
        bool: True if solved, False otherwise
    """
    # Wait for initial challenge processing
    await page.wait_for_timeout(random.uniform(4000, 6000))
    
    # Look for any checkbox
    for selector in CF_SELECTORS["checkbox"]:
        try:
            checkbox = await page.query_selector(selector)
            if checkbox:
                logger.info(f"Found checkbox: {selector}")
                # Get checkbox position
                bbox = await checkbox.bounding_box()
                if bbox:
                    # Click at a random position within the checkbox
                    x = bbox['x'] + random.uniform(3, bbox['width'] - 3)
                    y = bbox['y'] + random.uniform(3, bbox['height'] - 3)
                    
                    # Move mouse gradually
                    await page.mouse.move(x/2, y/2)
                    await page.wait_for_timeout(random.uniform(100, 300))
                    await page.mouse.move(x, y)
                    await page.wait_for_timeout(random.uniform(100, 200))
                    await page.mouse.click(x, y)
                    
                    logger.info("Clicked checkpoint")
                    await page.wait_for_timeout(5000)
                    
                    if await page.query_selector('[data-hcaptcha-response]'):
                        logger.warning("Checkbox revealed a captcha - cannot solve automatically")
                        return False
                    
                    # Check if challenge is still present
                    if not await is_cloudflare_page(page):
                        logger.info("Successfully solved JS challenge")
                        return True
                else:
                    await checkbox.click()
                    await page.wait_for_timeout(5000)
        except Exception as e:
            logger.debug(f"Error clicking checkbox {selector}: {e}")
    
    # Try pressing some buttons
    button_selectors = [
        "button", 
        "[role='button']", 
        ".cf-button", 
        "a.button", 
        ".btn",
        "#challenge-stage button"
    ]
    
    for selector in button_selectors:
        try:
            buttons = await page.query_selector_all(selector)
            for i, button in enumerate(buttons):
                visible = await button.is_visible()
                if visible:
                    logger.info(f"Clicking button {selector} #{i}")
                    await button.click()
                    await page.wait_for_timeout(3000)
                    
                    if not await is_cloudflare_page(page):
                        logger.info("Successfully solved challenge by clicking button")
                        return True
        except Exception as e:
            logger.debug(f"Error clicking button {selector}: {e}")
    
    # Try navigating with keyboard
    try:
        await page.keyboard.press("Tab")
        await page.wait_for_timeout(100)
        await page.keyboard.press("Tab")
        await page.wait_for_timeout(100)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(3000)
        
        if not await is_cloudflare_page(page):
            logger.info("Successfully solved challenge with keyboard navigation")
            return True
    except Exception as e:
        logger.debug(f"Error with keyboard navigation: {e}")
    
    return False

async def solve_waiting_room(page):
    """
    Attempt to handle Cloudflare waiting room
    
    Args:
        page: Playwright page
        
    Returns:
        bool: True if page eventually loads, False if timeout
    """
    logger.info("Detected Cloudflare waiting room - waiting for queue")
    
    # Just wait a really long time - these usually resolve on their own
    for _ in range(6):  # up to 3 minutes total
        await page.wait_for_timeout(30000)  # 30 seconds
        
        # Check if we're past the waiting room
        if not await is_cloudflare_page(page):
            logger.info("Successfully passed through waiting room")
            return True
            
        logger.info("Still in waiting room, continuing to wait...")
    
    logger.warning("Timeout waiting for Cloudflare waiting room")
    return False

async def is_cloudflare_page(page):
    """
    Check if the current page is a Cloudflare challenge
    
    Args:
        page: Playwright page
        
    Returns:
        bool: True if detected as Cloudflare, False otherwise
    """
    title = await page.title()
    title = title.lower()
    
    # Check URL for Cloudflare
    url = page.url.lower()
    if "cloudflare" in url or "challenges" in url:
        return True
        
    # Check for Cloudflare in title
    if "cloudflare" in title:
        return True
        
    # Check for challenge selectors
    for selector in CF_SELECTORS["challenge_content"]:
        try:
            element = await page.query_selector(selector)
            if element:
                return True
        except:
            pass
            
    # Check content for Cloudflare indicators
    try:
        content = await page.inner_text("body")
        content = content.lower()
        
        # Check all language indicators
        for lang, phrases in CF_INDICATORS.items():
            for phrase in phrases:
                if phrase in content:
                    return True
    except:
        pass
        
    return False

async def bypass_cloudflare(page):
    """
    Main function to bypass Cloudflare challenges
    
    Args:
        page: Playwright page
        
    Returns:
        bool: True if bypass successful, False otherwise
    """
    # First check if we're dealing with Cloudflare
    if not await is_cloudflare_page(page):
        return True
        
    # Get domain for cookie management
    domain = extract_domain(page.url)
    if domain:
        # Try loading saved cookies first
        if load_cf_cookies(page, domain):
            logger.info("Loaded saved Cloudflare cookies, attempting to navigate with them")
            await page.reload()
            await page.wait_for_timeout(5000)
            
            # Check if cookies worked
            if not await is_cloudflare_page(page):
                logger.info("Successfully bypassed Cloudflare using saved cookies")
                return True
    
    # Detect challenge type
    challenge_type = detect_challenge_type(page)
    if not challenge_type:
        logger.warning("Possible Cloudflare detection, but couldn't identify challenge type")
        challenge_type = CHALLENGE_TYPES["JS_CHALLENGE"]  # Default
    
    logger.info(f"Detected Cloudflare challenge type: {challenge_type}")
    
    # Handle based on challenge type
    if challenge_type == CHALLENGE_TYPES["JS_CHALLENGE"]:
        success = await solve_js_challenge(page)
    elif challenge_type == CHALLENGE_TYPES["WAITING_ROOM"]:
        success = await solve_waiting_room(page)
    elif challenge_type in [CHALLENGE_TYPES["CAPTCHA"], CHALLENGE_TYPES["TURNSTILE"]]:
        logger.warning(f"Cannot automatically solve {challenge_type} challenges")
        success = False
    else:
        # Default JS challenge handling for unknown types
        logger.info("Using default JS challenge handling")
        success = await solve_js_challenge(page)
    
    # If successful, save cookies for future use
    if success and domain:
        save_cf_cookies(page, domain)
    
    return success 