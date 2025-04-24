"""
Browser service for Playwright integration with anti-detection measures
"""
from flask import current_app, g
import os
import random
import time
import json
from loguru import logger
from playwright.sync_api import sync_playwright
from app.services.proxy import get_proxy_for_playwright
from app.utils.fp_evasion import apply_fingerprint_evasion, generate_consistent_fingerprint, apply_consistent_fingerprint
from app.utils.fingerprint_injection import FingerprintGenerator, inject_fingerprint

# Extended list of common user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 OPR/102.0.0.0",
]

# Common screen resolutions
SCREEN_RESOLUTIONS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
]

# Common languages and timezones
LANGUAGE_LOCALES = ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "ja-JP"]
TIMEZONES = ["America/New_York", "Europe/London", "Europe/Paris", "Asia/Tokyo", "Australia/Sydney"]

# Cookie domains to avoid clearing (for maintaining sessions)
PRESERVE_COOKIE_DOMAINS = [".google.com", ".cloudflare.com", ".amazon.com"]

def get_user_agent():
    """
    Get a random user agent or return the default one
    
    Returns:
        str: User agent string
    """
    if current_app.config.get("USER_AGENT_ROTATION", True):
        return random.choice(USER_AGENTS)
    return USER_AGENTS[0]

def get_random_viewport():
    """
    Get a random screen resolution for the viewport
    
    Returns:
        dict: Screen resolution
    """
    return random.choice(SCREEN_RESOLUTIONS)

def get_browser():
    """
    Get or create a browser instance
    
    Returns:
        Browser: Playwright browser instance
    """
    if "browser" not in g:
        init_browser()
    
    return g.browser if hasattr(g, "browser") else None

def get_context_options(fingerprint=None):
    """
    Create randomized browser context options to evade fingerprinting
    
    Args:
        fingerprint: Optional pre-generated fingerprint to use
        
    Returns:
        dict: Context options
    """
    # Generate fingerprint for consistency across parameters if not provided
    if fingerprint is None:
        # First try to use our enhanced FingerprintGenerator
        try:
            generator = FingerprintGenerator()
            fingerprint = generator.generate_fingerprint()
            logger.info("Using advanced fingerprint generator")
        except Exception as e:
            logger.warning(f"Error using advanced fingerprint generator, falling back to basic: {e}")
            fingerprint = generate_consistent_fingerprint()
    
    try:
        # Extract data from fingerprint
        browser_data = fingerprint.get('browser', {})
        device_data = fingerprint.get('device', {})
        screen_data = device_data.get('screen', {})
        
        # Get user agent and viewport from fingerprint
        user_agent = browser_data.get('user_agent', get_user_agent())
        viewport = {
            "width": screen_data.get('width', 1920),
            "height": screen_data.get('height', 1080)
        }
        
        # Get locale from browser language
        locale = browser_data.get('language', random.choice(LANGUAGE_LOCALES))
        
        # Get timezone
        timezone_id = fingerprint.get('timezone', {}).get('name', random.choice(TIMEZONES))
    except (KeyError, AttributeError):
        # Fallback to random values
        viewport = get_random_viewport()
        user_agent = get_user_agent()
        locale = random.choice(LANGUAGE_LOCALES)
        timezone_id = random.choice(TIMEZONES)
    
    # Construct context options
    context_options = {
        "viewport": viewport,
        "user_agent": user_agent,
        "locale": locale,
        "timezone_id": timezone_id,
        "bypass_csp": True,  # Bypass Content-Security-Policy
        "ignore_https_errors": True,
        "extra_http_headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": f"{locale.split('-')[0]},{locale};q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1"
        }
    }
    
    # Add proxy configuration if proxy rotation is enabled
    proxy_config = get_proxy_for_playwright()
    if proxy_config:
        context_options["proxy"] = proxy_config
    
    if random.random() > 0.5:
        # Randomly decide whether to include color scheme
        context_options["color_scheme"] = random.choice(["light", "dark"])
        
    # Add geolocation for extra realism - 30% chance
    if random.random() < 0.3:
        # Random coordinates based on popular cities
        geo_locations = [
            {"latitude": 40.7128, "longitude": -74.0060},  # New York
            {"latitude": 51.5074, "longitude": -0.1278},   # London
            {"latitude": 48.8566, "longitude": 2.3522},    # Paris
            {"latitude": 35.6762, "longitude": 139.6503},  # Tokyo
            {"latitude": 37.7749, "longitude": -122.4194}, # San Francisco
            {"latitude": 52.5200, "longitude": 13.4050},   # Berlin
        ]
        context_options["geolocation"] = random.choice(geo_locations)
        
    # Set permissions - allow geolocation, notifications etc.
    context_options["permissions"] = ["geolocation"]
    
    return context_options

def handle_cloudflare_challenge(page):
    """
    Attempt to solve Cloudflare challenges in multiple languages
    
    Args:
        page: Playwright page instance
        
    Returns:
        bool: True if solved, False otherwise
    """
    # Get page title and content
    title = page.title().lower()
    content = page.inner_text("body").lower()
    
    # Check for Cloudflare indicators in multiple languages
    cloudflare_indicators = [
        # English
        "cloudflare", "check", "challenge", "security", "ddos", "protection",
        "verify you are human", "one moment", "just a moment",
        
        # Italian
        "ci siamo quasi", "dimostra di essere un utente umano",
        
        # Spanish
        "comprueba que eres humano", "estamos comprobando",
        
        # French
        "vérification", "prouvez que vous êtes humain", "nous vérifions",
        
        # German
        "überprüfung", "mensch", "sicherheitsabfrage", "bestätigen sie", 
        "nur einen moment", "einen moment"
    ]
    
    is_cloudflare = False
    detected_indicator = None
    
    for indicator in cloudflare_indicators:
        if indicator in title or indicator in content:
            is_cloudflare = True
            detected_indicator = indicator
            logger.info(f"Detected Cloudflare challenge: {indicator}")
            break
            
    if not is_cloudflare and "cloudflare" not in page.url:
        return False
        
    logger.info("Attempting to solve Cloudflare challenge")
    
    # Step 1: Wait longer for initial challenge processing
    page.wait_for_timeout(random.uniform(4000, 7000))
    
    # Step 2: Look for checkbox challenge in multiple languages
    checkbox_selectors = [
        "input[type='checkbox']", 
        ".checkbox", 
        ".cf-checkbox", 
        "[data-testid='challenge-checkbox']",
        "[role='checkbox']",
        "[aria-checked]",
        "#challenge-stage input",
        "form input"
    ]
    
    for selector in checkbox_selectors:
        try:
            checkbox = page.query_selector(selector)
            if checkbox:
                logger.info(f"Found Cloudflare checkbox: {selector}")
                # Move mouse naturally to checkbox
                page.wait_for_timeout(random.uniform(800, 1200))
                
                # Get checkbox position and size
                bbox = checkbox.bounding_box()
                if bbox:
                    # Move to a random point within the checkbox
                    target_x = bbox['x'] + random.uniform(3, bbox['width'] - 3)
                    target_y = bbox['y'] + random.uniform(3, bbox['height'] - 3)
                    
                    # Move mouse in a human-like curve
                    randomize_mouse_movement(page, target_x, target_y)
                    
                    # Click and wait
                    checkbox.click()
                    page.wait_for_timeout(random.uniform(1000, 2000))
                    
                    # Wait for challenge to complete
                    wait_for_challenge_completion(page)
                    return True
        except Exception as e:
            logger.warning(f"Error interacting with checkbox: {e}")
    
    # Step 3: Try to find and solve other challenge types
    if "turnstile" in content or "turnstile" in page.url:
        logger.info("Detected Cloudflare Turnstile challenge")
        # Wait a bit longer for Turnstile
        page.wait_for_timeout(random.uniform(5000, 8000))
        
        # Check if the page has navigated past the challenge
        wait_for_challenge_completion(page)
        
        return True
    
    # Check for "I am human" verification button in multiple languages
    human_button_selectors = [
        "button:has-text('human')", 
        "button:has-text('verify')",
        "button:has-text('continue')",
        "button:has-text('mensch')",
        "button:has-text('bestätigen')",
        "button:has-text('fortfahren')",
        "button:has-text('verificar')",
        "button:has-text('continuar')",
        "button:has-text('vérifier')",
        "button:has-text('humain')",
        "button.challenge-button",
        "[data-testid='challenge-button']",
        "#challenge-stage button",
        "form button"
    ]
    
    for selector in human_button_selectors:
        try:
            button = page.query_selector(selector)
            if button:
                logger.info(f"Found Cloudflare button: {selector}")
                
                # Get button position for natural movement
                bbox = button.bounding_box()
                if bbox:
                    # Move to a random point within the button
                    target_x = bbox['x'] + random.uniform(5, bbox['width'] - 5)
                    target_y = bbox['y'] + random.uniform(5, bbox['height'] - 5)
                    
                    # Move mouse in a human-like curve
                    randomize_mouse_movement(page, target_x, target_y)
                    
                button.click()
                page.wait_for_timeout(random.uniform(2000, 4000))
                wait_for_challenge_completion(page)
                return True
        except Exception as e:
            logger.warning(f"Error clicking button: {e}")
    
    # Try a more aggressive approach - look for any clickable elements in the challenge
    try:
        # Find any interactive elements in the challenge form
        interactive_elements = page.query_selector_all("#challenge-stage button, #challenge-stage a, form button, form input[type='submit']")
        if interactive_elements and len(interactive_elements) > 0:
            # Click the first interactive element
            logger.info(f"Attempting to click generic interactive element in challenge")
            interactive_elements[0].click()
            page.wait_for_timeout(random.uniform(2000, 4000))
            wait_for_challenge_completion(page, timeout=15000)
    except Exception as e:
        logger.warning(f"Error with generic interaction: {e}")
    
    # Just wait a bit to see if challenge resolves itself
    page.wait_for_timeout(random.uniform(5000, 10000))
    
    # Check if we've passed the challenge
    return "challenge" not in page.url.lower() and "cloudflare" not in page.url.lower()

def randomize_mouse_movement(page, target_x, target_y):
    """
    Move mouse cursor in a human-like pattern
    
    Args:
        page: Playwright page object
        target_x: Target X coordinate
        target_y: Target Y coordinate
    """
    # Get current mouse position or use a default starting point
    current_x = random.randint(100, 800)
    current_y = random.randint(100, 600)
    
    # Create a natural curve with multiple points
    steps = random.randint(5, 15)
    points = []
    
    # Control points for bezier curve
    cp1x = current_x + (target_x - current_x) * random.uniform(0.2, 0.4)
    cp1y = current_y + random.uniform(-200, 200)
    cp2x = current_x + (target_x - current_x) * random.uniform(0.6, 0.8)
    cp2y = target_y + random.uniform(-200, 200)
    
    # Generate points along the curve
    for i in range(steps + 1):
        t = i / steps
        # Bezier curve formula
        x = (1-t)**3 * current_x + 3*(1-t)**2 * t * cp1x + 3*(1-t) * t**2 * cp2x + t**3 * target_x
        y = (1-t)**3 * current_y + 3*(1-t)**2 * t * cp1y + 3*(1-t) * t**2 * cp2y + t**3 * target_y
        points.append((x, y))
    
    # Move through each point with human-like timing
    for x, y in points:
        page.mouse.move(x, y)
        # Random pause between movements
        time.sleep(random.uniform(0.01, 0.05))

def wait_for_challenge_completion(page, timeout=30000):
    """
    Wait for Cloudflare challenge to complete
    
    Args:
        page: Playwright page object
        timeout: Maximum wait time in ms
    """
    # Check for successful navigation past challenge
    start_time = time.time()
    check_interval = 500  # ms
    
    while (time.time() - start_time) * 1000 < timeout:
        # Check if URL no longer contains challenge indicators
        current_url = page.url
        if ("challenge" not in current_url.lower() and 
            "cloudflare" not in current_url.lower() and
            "captcha" not in current_url.lower()):
            
            # Also check page content
            title = page.title().lower()
            try:
                body_text = page.inner_text("body").lower()
                if not any(term in body_text for term in ["cloudflare", "challenge", "security check", "captcha"]):
                    logger.info("Challenge appears to be completed")
                    return True
            except Exception:
                # If we can't check the body text, rely on URL only
                pass
        
        # Wait before checking again
        page.wait_for_timeout(check_interval)
    
    logger.warning("Challenge completion timeout exceeded")
    return False

def randomize_scroll_behavior(page):
    """
    Implement human-like scrolling behavior
    
    Args:
        page: Playwright page object
    """
    try:
        # Get page height with fallback values
        try:
            page_height = page.evaluate("() => document.body.scrollHeight || document.documentElement.scrollHeight")
            viewport_height = page.evaluate("() => window.innerHeight || 600")
        except Exception as e:
            logger.warning(f"Error getting page dimensions: {e}")
            # Use default values if evaluation fails
            page_height = 1000
            viewport_height = 600
        
        if page_height <= viewport_height:
            # Page fits in viewport, no need to scroll
            return
        
        # Determine number of scroll actions - limit to fewer scrolls to reduce timeouts
        num_scrolls = random.randint(1, 3)
        
        # Create random scroll pattern
        for _ in range(num_scrolls):
            # Random scroll amount
            scroll_amount = random.randint(100, min(300, viewport_height))
            
            # Execute scroll with random timing - no timeout parameter
            try:
                page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                # Use shorter wait times
                page.wait_for_timeout(random.randint(200, 500))
            except Exception as e:
                logger.warning(f"Error during scroll operation: {e}")
                break  # Exit loop if we hit an error
        
        # 20% chance to scroll back up a bit - reduced from 30%
        if random.random() < 0.2:
            try:
                page.evaluate(f"window.scrollBy(0, {-random.randint(50, 150)})")
                page.wait_for_timeout(random.randint(100, 300))
            except Exception:
                pass  # Ignore errors here
        
        # 10% chance to scroll to a random element - reduced from 20%
        if random.random() < 0.1:
            try:
                # Use JavaScript to find and scroll to an element - safer than query_selector_all
                page.evaluate("""() => {
                    const elements = document.querySelectorAll('a, button, input, .card, .item, article');
                    if (elements.length > 0) {
                        const randomIndex = Math.floor(Math.random() * elements.length);
                        const element = elements[randomIndex];
                        if (element) {
                            element.scrollIntoView({ behavior: 'auto', block: 'center' });
                        }
                    }
                }""")
                page.wait_for_timeout(random.randint(100, 300))
            except Exception as e:
                logger.warning(f"Error scrolling to element: {e}")
    except Exception as e:
        logger.warning(f"Error in randomized scrolling: {e}")

def simulate_human_interaction(page):
    """
    Simulate realistic human-like interactions with the page
    
    Args:
        page: Playwright page object
    """
    try:
        # Add shorter random delays
        page.wait_for_timeout(random.randint(300, 1000))
        
        # Random scrolling behavior with timeout protection
        randomize_scroll_behavior(page)
        
        # Random mouse movements
        try:
            # Get window dimensions with fallback values - no timeout parameter
            screen_width = page.evaluate("() => window.innerWidth || 1024")
            screen_height = page.evaluate("() => window.innerHeight || 768")
            
            # Move mouse to random positions - fewer moves
            num_moves = random.randint(1, 2)
            for _ in range(num_moves):
                x = random.randint(0, screen_width)
                y = random.randint(0, screen_height)
                randomize_mouse_movement(page, x, y)
                page.wait_for_timeout(random.randint(200, 500))
        except Exception as e:
            logger.warning(f"Error during mouse movement: {e}")
        
        # Only 10% chance to hover over a random element
        if random.random() < 0.1:
            try:
                # Use JavaScript to hover - avoids potential element handling issues
                page.evaluate("""() => {
                    const elements = document.querySelectorAll('a, button, .nav-item, .menu-item');
                    if (elements.length > 0) {
                        const randomIndex = Math.floor(Math.random() * elements.length);
                        const element = elements[randomIndex];
                        if (element) {
                            // Create a synthetic mouseover event
                            const event = new MouseEvent('mouseover', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            element.dispatchEvent(event);
                        }
                    }
                }""")
                page.wait_for_timeout(random.randint(200, 500))
            except Exception as e:
                logger.warning(f"Error during element hover: {e}")
        
        # Only 5% chance to interact with form elements
        if random.random() < 0.05:
            try:
                # Use JavaScript to interact with form - safer approach
                page.evaluate("""() => {
                    const inputs = document.querySelectorAll('input[type="text"], input[type="search"]');
                    if (inputs.length > 0) {
                        const randomIndex = Math.floor(Math.random() * inputs.length);
                        const input = inputs[randomIndex];
                        if (input) {
                            input.focus();
                            input.value = '';
                            // Add a simple value
                            const values = ['example', 'test', 'hello'];
                            input.value = values[Math.floor(Math.random() * values.length)];
                        }
                    }
                }""")
                page.wait_for_timeout(random.randint(300, 800))
            except Exception as e:
                logger.warning(f"Error interacting with form elements: {e}")
        
        logger.debug("Human interaction simulation completed")
    except Exception as e:
        logger.warning(f"Error simulating human interaction: {e}")

def manage_cookies(page):
    """
    Manage cookies intelligently to maintain important sessions
    
    Args:
        page: Playwright page object
    """
    try:
        # Get all cookies
        cookies = page.context.cookies()
        
        # Filter cookies to keep important ones
        cookies_to_keep = []
        cookies_to_remove = []
        
        for cookie in cookies:
            domain = cookie.get("domain", "")
            name = cookie.get("name", "")
            
            # Keep cookies for specific domains
            if any(domain.endswith(preserved) for preserved in PRESERVE_COOKIE_DOMAINS):
                cookies_to_keep.append(cookie)
            # Keep important session and authentication cookies
            elif any(important in name.lower() for important in ["session", "auth", "token", "id", "csrf"]):
                cookies_to_keep.append(cookie)
            else:
                cookies_to_remove.append(cookie)
        
        # Only run this occasionally to avoid suspicious behavior
        if random.random() < 0.3:
            # Clear non-essential cookies individually
            try:
                # Method 1: Try to clear all cookies first
                page.context.clear_cookies()
                
                # Method 2: Set only the cookies we want to keep
                if cookies_to_keep:
                    page.context.add_cookies(cookies_to_keep)
                
                logger.debug(f"Managed cookies: kept {len(cookies_to_keep)}, removed {len(cookies_to_remove)}")
            except Exception as e:
                logger.warning(f"Error managing specific cookies: {e}")
    except Exception as e:
        logger.warning(f"Error managing cookies: {e}")

def init_browser(e=None):
    """
    Initialize a new browser instance with anti-detection measures
    
    Args:
        e: Exception object (used in teardown context)
        
    Returns:
        None
    """
    # Close existing browser if it exists
    if hasattr(g, "browser") and g.browser:
        g.browser.close()
    
    if hasattr(g, "playwright") and g.playwright:
        g.playwright.stop()
    
    try:
        # Check if undetected-playwright should be used
        use_undetected = current_app.config.get("USE_UNDETECTED", False)
        
        if use_undetected and 'undetected_playwright' in sys.modules:
            # Use imported undetected_playwright
            logger.info("Using undetected-playwright for enhanced stealth")
            import undetected_playwright
            g.playwright = undetected_playwright.sync_playwright().start()
        else:
            # Use standard Playwright
            from playwright.sync_api import sync_playwright
            g.playwright = sync_playwright().start()
            logger.info("Using standard Playwright with custom stealth measures")
        
        # Get browser launch options
        browser_options = get_browser_launch_options()
        
        # Get browser type config (default to chromium)
        browser_type = current_app.config.get("BROWSER_TYPE", "chromium").lower()
        
        # Launch browser with stealth options
        if browser_type == "chromium" or browser_type == "chrome":
            # Use proper channel if specified
            channel = current_app.config.get("BROWSER_CHANNEL", None)
            g.browser = g.playwright.chromium.launch(
                headless=current_app.config.get("HEADLESS", True),
                channel=channel,
                args=browser_options.get("args", []),
                ignore_default_args=browser_options.get("ignore_default_args", []),
                slow_mo=current_app.config.get("SLOW_MO", 10)
            )
        elif browser_type == "firefox":
            g.browser = g.playwright.firefox.launch(
                headless=current_app.config.get("HEADLESS", True),
                slow_mo=current_app.config.get("SLOW_MO", 10)
            )
        elif browser_type == "webkit":
            g.browser = g.playwright.webkit.launch(
                headless=current_app.config.get("HEADLESS", True),
                slow_mo=current_app.config.get("SLOW_MO", 10)
            )
        else:
            logger.warning(f"Unknown browser type: {browser_type}, falling back to chromium")
            g.browser = g.playwright.chromium.launch(
                headless=current_app.config.get("HEADLESS", True),
                args=browser_options.get("args", []),
                ignore_default_args=browser_options.get("ignore_default_args", []),
                slow_mo=current_app.config.get("SLOW_MO", 10)
            )
        
        logger.info(f"Browser initialized: {browser_type}")
    except Exception as e:
        logger.error(f"Error initializing browser: {e}")
        raise

def get_browser_launch_options():
    """
    Get browser launch options for enhanced stealth
    
    Returns:
        dict: Browser launch options
    """
    # Standard arguments for stealth
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process,SitePerProcess",
        "--disable-site-isolation-trials",
        "--disable-setuid-sandbox",
        "--no-sandbox",
        "--disable-infobars",
        "--no-default-browser-check",
        "--no-first-run",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins",
        "--disable-site-isolation-trials",
    ]
    
    # Add arguments from config if available
    custom_args = current_app.config.get("BROWSER_ARGS", [])
    if custom_args:
        args.extend(custom_args)
    
    # Arguments to ignore
    ignore_default_args = ["--enable-automation"]
    
    # Create options object
    options = {
        "args": args,
        "ignore_default_args": ignore_default_args
    }
    
    return options

async def create_stealth_page(browser, fingerprint=None):
    """
    Create a page with stealth features enabled
    
    Args:
        browser: Playwright browser instance
        fingerprint: Optional fingerprint to use
        
    Returns:
        Page: Playwright page with stealth features
    """
    # Generate fingerprint if not provided
    if fingerprint is None:
        try:
            generator = FingerprintGenerator()
            fingerprint = generator.generate_fingerprint()
            logger.info("Generated new fingerprint")
        except Exception as e:
            logger.warning(f"Error generating fingerprint: {e}")
            fingerprint = generate_consistent_fingerprint()
    
    # Get context options with fingerprint
    context_options = get_context_options(fingerprint)
    
    try:
        # Check if we're dealing with a sync or async browser
        if hasattr(browser, 'new_context'):
            # Sync browser
            context = browser.new_context(**context_options)
            page = context.new_page()
        elif hasattr(browser, 'new_context_async'):
            # Async browser with explicit async methods
            context = await browser.new_context_async(**context_options)
            page = await context.new_page_async()
        else:
            # Assume it's an async browser without explicit _async methods
            # Use try/except to handle sync/async automatically
            try:
                context = await browser.new_context(**context_options)
                page = await context.new_page()
            except TypeError:
                # If await fails, try without await
                context = browser.new_context(**context_options)
                page = context.new_page()
                
        # Apply stealth techniques
        from app.services.browser_stealth import apply_stealth_to_page
        await apply_stealth_to_page(page)
        
        # Apply fingerprint evasion
        await apply_fingerprint_evasion(page)
        
        # Apply consistent fingerprint if needed
        if fingerprint:
            await inject_fingerprint(page, fingerprint)
        
        logger.info("Created stealth page with enhanced fingerprint evasion")
        return page
    except Exception as e:
        logger.error(f"Error creating stealth page: {e}")
        raise 