"""
Enhanced browser service with stealth plugins integration
"""
import os
import random
import time
import asyncio
import importlib.util
from loguru import logger
from flask import current_app, g
from playwright.sync_api import sync_playwright
import sys
from app.services.proxy import get_proxy_for_playwright

# Import our fingerprint injection module
from app.utils.fingerprint_injection import inject_fingerprint, FingerprintGenerator
from app.utils.fp_evasion import apply_fingerprint_evasion, generate_consistent_fingerprint, apply_consistent_fingerprint

# Check if stealth plugins are available
STEALTH_AVAILABLE = False
PYPPETEER_STEALTH_AVAILABLE = False

try:
    import playwright_stealth
    STEALTH_AVAILABLE = True
    logger.info("playwright-stealth plugin available")
except ImportError:
    logger.warning("playwright-stealth not installed, using basic stealth techniques")

try:
    import pyppeteer_stealth
    PYPPETEER_STEALTH_AVAILABLE = True
    logger.info("pyppeteer-stealth available for fallback techniques")
except ImportError:
    logger.warning("pyppeteer-stealth not installed, using basic stealth techniques")

# Attempt to import undetected-playwright
UNDETECTED_AVAILABLE = False
try:
    import undetected_playwright
    UNDETECTED_AVAILABLE = True
    logger.info("undetected-playwright available")
except ImportError:
    logger.warning("undetected-playwright not installed, using standard playwright")

# Try to import our custom stealth module
from app.services.stealth import get_stealth_js

# User Agent list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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

# Try loading cloudflare bypass module
try:
    from app.services.cloudflare import bypass_cloudflare
    CLOUDFLARE_MODULE_AVAILABLE = True
    logger.info("Cloudflare bypass module available")
except ImportError:
    CLOUDFLARE_MODULE_AVAILABLE = False
    logger.warning("Cloudflare bypass module not available")

def get_user_agent():
    """
    Get a random user agent or return the default one
    
    Returns:
        str: User agent string
    """
    if current_app.config.get("USER_AGENT_ROTATION", True):
        return random.choice(USER_AGENTS)
    return USER_AGENTS[0]

def get_context_options(fingerprint=None):
    """
    Create randomized browser context options to evade fingerprinting
    
    Args:
        fingerprint: Optional pre-generated fingerprint to use
    
    Returns:
        dict: Context options
    """
    # Use provided fingerprint or generate a consistent one
    if fingerprint is None:
        fingerprint = generate_consistent_fingerprint()
    
    # Extract fingerprint data for context options
    try:
        # Get browser data from fingerprint
        user_agent = fingerprint.get('browser', {}).get('user_agent', get_user_agent())
        
        # Get device screen info
        device_screen = fingerprint.get('device', {}).get('screen', {})
        viewport = {
            "width": device_screen.get('width', 1920),
            "height": device_screen.get('height', 1080)
        }
        
        # Get locale from browser language
        locale = fingerprint.get('browser', {}).get('language', "en-US")
        
        # Get timezone
        timezone_id = fingerprint.get('timezone', {}).get('name', "America/New_York")
    except (KeyError, AttributeError, TypeError):
        # Fallback to random values if fingerprint is invalid
        logger.warning("Invalid fingerprint provided, using random values")
        viewport = random.choice(SCREEN_RESOLUTIONS)
        user_agent = get_user_agent()
        locale = random.choice(["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "ja-JP"])
        timezone_id = random.choice(["America/New_York", "Europe/London", "Europe/Paris", "Asia/Tokyo", "Australia/Sydney"])
    
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
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
    }
    
    # Add proxy configuration if proxy rotation is enabled
    proxy_config = get_proxy_for_playwright()
    if proxy_config:
        context_options["proxy"] = proxy_config
    
    # 50% chance to use color scheme
    if random.random() > 0.5:
        context_options["color_scheme"] = random.choice(["light", "dark"])
        
    # 30% chance to include geolocation
    if random.random() < 0.3:
        # Random coordinates based on popular cities
        geo_locations = [
            {"latitude": 40.7128, "longitude": -74.0060},  # New York
            {"latitude": 51.5074, "longitude": -0.1278},   # London
            {"latitude": 48.8566, "longitude": 2.3522},    # Paris
            {"latitude": 35.6762, "longitude": 139.6503},  # Tokyo
            {"latitude": 37.7749, "longitude": -122.4194}, # San Francisco
        ]
        context_options["geolocation"] = random.choice(geo_locations)
    
    # Default permissions to grant
    context_options["permissions"] = ["geolocation", "notifications"]
    
    # Extra options for device scaling and mobile simulation - 10% chance to be mobile
    if random.random() < 0.1:
        context_options["is_mobile"] = True
        context_options["has_touch"] = True
        context_options["device_scale_factor"] = 2.0
    else:
        context_options["device_scale_factor"] = random.choice([1.0, 1.25, 1.5, 2.0])
    
    return context_options

async def apply_stealth_to_page(page):
    """
    Apply stealth techniques to a page
    
    Args:
        page: Playwright page object
    """
    logger.info("Applying stealth techniques to page")
    
    # Get fingerprint from context if available
    context = page.context
    fingerprint = getattr(context, "_fingerprint", None)
    
    # Apply fingerprint injection if available
    if fingerprint:
        logger.info("Applying fingerprint injection")
        await inject_fingerprint(page, fingerprint)
    
    # Apply fingerprint evasion techniques
    logger.info("Applying fingerprint evasion")
    await apply_fingerprint_evasion(page)
    
    # Apply custom stealth script
    stealth_js = get_stealth_js()
    await page.add_init_script(stealth_js)
    
    # Apply playwright-stealth if available
    if STEALTH_AVAILABLE:
        try:
            logger.info("Applying playwright-stealth")
            await playwright_stealth.stealth_async(page)
        except Exception as e:
            logger.error(f"Error applying playwright-stealth: {e}")
    
    # If available, adapt techniques from pyppeteer-stealth (as a fallback)
    elif PYPPETEER_STEALTH_AVAILABLE:
        try:
            logger.info("Adapting techniques from pyppeteer-stealth")
            # We can't use pyppeteer_stealth directly with playwright, but we can
            # apply similar JavaScript evasion techniques
            await page.add_init_script("""
            () => {
                // User-Agent vendor customization
                Object.defineProperty(navigator, 'vendor', {
                    get: () => 'Google Inc.',
                });
                
                // WebGL vendor spoofing
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    // UNMASKED_VENDOR_WEBGL
                    if (parameter === 37445) {
                        return 'Google Inc.';
                    }
                    // UNMASKED_RENDERER_WEBGL
                    if (parameter === 37446) {
                        return 'ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)';
                    }
                    return getParameter.apply(this, arguments);
                };
            }
            """)
        except Exception as e:
            logger.error(f"Error applying pyppeteer-stealth techniques: {e}")
    
    # Apply additional anti-detection measures
    await apply_additional_stealth_measures(page)
    
    logger.info("Stealth techniques applied successfully")

async def apply_additional_stealth_measures(page):
    """
    Apply additional stealth measures to the page
    
    Args:
        page: Playwright page object
    """
    try:
        # Patch for webdriver detection
        await page.add_init_script("""
        () => {
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
                configurable: true
            });
            
            // Hide automation property
            if (navigator.hasOwnProperty('automationControlled')) {
                Object.defineProperty(navigator, 'automationControlled', {
                    get: () => false,
                    configurable: true
                });
            }
            
            // Hide chrome driver properties
            if (window.hasOwnProperty('cdc_adoQpoasnfa76pfcZLmcfl_Array')) {
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            }
            if (window.hasOwnProperty('cdc_adoQpoasnfa76pfcZLmcfl_Promise')) {
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            }
            if (window.hasOwnProperty('cdc_adoQpoasnfa76pfcZLmcfl_Symbol')) {
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            }
        }
        """)
        
        # Add WebRTC protection
        await page.add_init_script("""
        () => {
            // Override WebRTC methods to prevent IP leaks
            if (typeof RTCPeerConnection !== 'undefined') {
                const originalRTCPeerConnection = window.RTCPeerConnection;
                
                window.RTCPeerConnection = function(...args) {
                    // Use the original constructor
                    const pc = new originalRTCPeerConnection(...args);
                    
                    // Override createOffer method
                    const originalCreateOffer = pc.createOffer;
                    pc.createOffer = function(options) {
                        // Force using relay ICE servers to prevent direct connections
                        const modifiedOptions = options || {};
                        modifiedOptions.iceTransportPolicy = 'relay';
                        return originalCreateOffer.call(this, modifiedOptions);
                    };
                    
                    return pc;
                };
                
                // Copy over prototype and static properties
                window.RTCPeerConnection.prototype = originalRTCPeerConnection.prototype;
                Object.setPrototypeOf(window.RTCPeerConnection, originalRTCPeerConnection);
            }
        }
        """)
        
        # Randomize client rects
        await page.add_init_script("""
        () => {
            // Add subtle noise to element positioning to defeat fingerprinting
            const originalGetBoundingClientRect = Element.prototype.getBoundingClientRect;
            Element.prototype.getBoundingClientRect = function() {
                const rect = originalGetBoundingClientRect.apply(this, arguments);
                
                // Create a proxy with subtle modifications
                if (rect.width > 0 && rect.height > 0) {
                    const noise = 0.000001; // Extremely subtle noise
                    return new Proxy(rect, {
                        get: function(target, prop) {
                            if (prop === 'x' || prop === 'left') {
                                return target[prop] + Math.random() * noise;
                            }
                            if (prop === 'y' || prop === 'top') {
                                return target[prop] + Math.random() * noise;
                            }
                            if (prop === 'width' || prop === 'height') {
                                return target[prop] + Math.random() * noise;
                            }
                            return target[prop];
                        }
                    });
                }
                
                return rect;
            };
        }
        """)
        
        logger.info("Applied additional stealth measures")
    except Exception as e:
        logger.error(f"Error applying additional stealth measures: {e}")

async def apply_cloudflare_bypass(page):
    """
    Apply specialized Cloudflare bypass techniques
    
    Args:
        page: Playwright page
    
    Returns:
        bool: True if bypass was successful, False otherwise
    """
    if CLOUDFLARE_MODULE_AVAILABLE:
        try:
            result = await bypass_cloudflare(page)
            return result
        except Exception as e:
            logger.error(f"Error in Cloudflare bypass: {e}")
    
    return False

def get_browser():
    """
    Get or create a browser instance
    
    Returns:
        Browser: Playwright browser instance
    """
    if "browser" not in g:
        init_browser()
    
    return g.browser if hasattr(g, "browser") else None

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
        # Check if we should use undetected_playwright or standard playwright
        use_undetected = current_app.config.get("USE_UNDETECTED", False)
        
        if use_undetected and UNDETECTED_AVAILABLE:
            logger.info("Using undetected-playwright for improved stealth")
            g.playwright = undetected_playwright.stealth_sync()
        else:
            # Start standard Playwright
            g.playwright = sync_playwright().start()
        
        # Get browser arguments for added stealth
        browser_args = get_browser_arguments()
        
        # Get browser type config (default to chromium)
        browser_type = current_app.config.get("BROWSER_TYPE", "chromium").lower()
        
        # Launch browser with stealth options
        logger.info(f"Launching {browser_type} browser with stealth options")
        
        if browser_type == "chromium" or browser_type == "chrome":
            # Use proper channel if specified
            channel = current_app.config.get("BROWSER_CHANNEL", None)
            g.browser = g.playwright.chromium.launch(
                headless=current_app.config.get("HEADLESS", True),
                channel=channel,
                args=browser_args,
                ignore_default_args=["--enable-automation"],
                slow_mo=current_app.config.get("SLOW_MO", 0)
            )
        elif browser_type == "firefox":
            g.browser = g.playwright.firefox.launch(
                headless=current_app.config.get("HEADLESS", True),
                args=browser_args,
                slow_mo=current_app.config.get("SLOW_MO", 0)
            )
        elif browser_type == "webkit":
            g.browser = g.playwright.webkit.launch(
                headless=current_app.config.get("HEADLESS", True),
                slow_mo=current_app.config.get("SLOW_MO", 0)
            )
        else:
            logger.warning(f"Unknown browser type: {browser_type}, using chromium")
            g.browser = g.playwright.chromium.launch(
                headless=current_app.config.get("HEADLESS", True),
                args=browser_args,
                ignore_default_args=["--enable-automation"],
                slow_mo=current_app.config.get("SLOW_MO", 0)
            )
        
        logger.info("Browser initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing browser: {e}")
        raise

def get_browser_arguments():
    """
    Get browser arguments for enhanced stealth
    
    Returns:
        list: Browser arguments
    """
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins",
        "--disable-site-isolation-trials",
        "--disable-infobars",
        "--no-default-browser-check",
        "--no-first-run",
        "--disable-setuid-sandbox",
    ]
    
    # Add arguments from config if available
    if current_app.config.get("BROWSER_ARGS"):
        args.extend(current_app.config.get("BROWSER_ARGS"))
    
    return args

def create_stealth_context(browser, fingerprint=None):
    """
    Create a browser context with stealth features
    
    Args:
        browser: Playwright browser object
        fingerprint: Optional fingerprint to use
        
    Returns:
        BrowserContext: Stealth-enhanced browser context
    """
    # Get context options with fingerprint info
    context_options = get_context_options(fingerprint)
    
    # Create the context with our options
    context = browser.new_context(**context_options)
    
    # Store fingerprint on context as attribute for later use by stealth techniques
    if fingerprint:
        setattr(context, "_fingerprint", fingerprint)
    
    return context

async def create_stealth_page(browser, fingerprint=None):
    """
    Create a page with stealth features
    
    Args:
        browser: Playwright browser instance
        fingerprint: Optional fingerprint to use
        
    Returns:
        Page: Playwright page with stealth features
    """
    # Create a stealth context
    context = None
    page = None
    
    try:
        # Create stealth context
        if fingerprint is None:
            fingerprint = generate_consistent_fingerprint()
            
        context_options = get_context_options(fingerprint)
        
        # Check if we're dealing with sync or async browser
        if hasattr(browser, 'new_context'):
            # Sync browser
            context = browser.new_context(**context_options)
            page = context.new_page()
        elif hasattr(browser, 'new_context_async'):
            # Async browser with explicit async methods
            context = await browser.new_context_async(**context_options)
            page = await context.new_page_async()
        else:
            # Assume it's async browser without explicit methods
            try:
                context = await browser.new_context(**context_options)
                page = await context.new_page()
            except TypeError:
                # If await fails, try without await
                context = browser.new_context(**context_options)
                page = context.new_page()
        
        # Store fingerprint as attribute on context
        if fingerprint and context:
            setattr(context, "_fingerprint", fingerprint)
        
        # Apply stealth features to the page
        await apply_stealth_to_page(page)
        
        return page
    except Exception as e:
        logger.error(f"Error creating stealth page: {e}")
        # Clean up resources if there was an error
        if page:
            try:
                page.close()
            except:
                pass
        if context:
            try:
                context.close()
            except:
                pass
        raise 