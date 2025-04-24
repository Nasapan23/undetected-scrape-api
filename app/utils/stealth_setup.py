"""
Stealth browser setup for Playwright browsers.
Configures various browser settings to minimize detection by anti-bot systems.
"""
import random
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from loguru import logger

# Import the fingerprint evasion module
from app.utils.fp_evasion import apply_fingerprint_evasion, apply_consistent_fingerprint

# Common User-Agent strings
USER_AGENTS = {
    "windows": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0",
    ],
    "macos": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0",
    ],
    "linux": [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
    ]
}

# Common screen resolutions
SCREEN_RESOLUTIONS = [
    [1920, 1080],  # Full HD (most common)
    [2560, 1440],  # QHD
    [1366, 768],   # HD (common for laptops)
    [1440, 900],   # WXGA+
    [1536, 864],   # HD+
    [1680, 1050],  # WSXGA+
    [1280, 720],   # HD
    [1600, 900],   # HD+
    [3840, 2160],  # 4K UHD
]

# Common languages
LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "en-CA,en;q=0.9",
    "fr-FR,fr;q=0.9,en;q=0.8",
    "de-DE,de;q=0.9,en;q=0.8",
    "es-ES,es;q=0.9,en;q=0.8",
    "it-IT,it;q=0.9,en;q=0.8",
    "pt-BR,pt;q=0.9,en;q=0.8",
    "nl-NL,nl;q=0.9,en;q=0.8",
    "ja-JP,ja;q=0.9,en;q=0.8",
]

# Viewport sizes
VIEWPORT_SIZES = [
    {"width": 1920, "height": 1080},  # Full HD
    {"width": 1366, "height": 768},   # Common laptop
    {"width": 1440, "height": 900},   # WXGA+
    {"width": 1280, "height": 720},   # HD
    {"width": 1536, "height": 864},   # HD+
    {"width": 1600, "height": 900},   # HD+
    {"width": 1680, "height": 1050},  # WSXGA+
    {"width": 2560, "height": 1440},  # QHD
]

# WebGL vendor/renderer information
WEBGL_VENDORS = [
    {"vendor": "Google Inc.", "renderer": "ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)"},
    {"vendor": "Google Inc.", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0)"},
    {"vendor": "Google Inc.", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 Direct3D11 vs_5_0 ps_5_0)"},
    {"vendor": "Google Inc.", "renderer": "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)"},
    {"vendor": "Apple", "renderer": "Apple M1"},
    {"vendor": "Apple", "renderer": "Apple M2"},
    {"vendor": "Intel Inc.", "renderer": "Intel Iris OpenGL Engine"},
    {"vendor": "NVIDIA Corporation", "renderer": "NVIDIA GeForce GTX 980/PCIe/SSE2"},
]

def generate_random_user_agent(os_type: Optional[str] = None) -> str:
    """Generate a random user agent string."""
    if os_type is None:
        os_type = random.choice(list(USER_AGENTS.keys()))
    return random.choice(USER_AGENTS[os_type])

def generate_random_device_memory() -> int:
    """Generate a random device memory value."""
    return random.choice([2, 4, 8, 16])

def generate_random_hardware_concurrency() -> int:
    """Generate a random number of CPU cores."""
    return random.randint(4, 16)

def generate_random_timezone_offset() -> int:
    """Generate a random timezone offset."""
    return random.choice([-720, -660, -600, -540, -480, -420, -360, -300, -240, -210, -180, -120, -60, 
                         0, 60, 120, 180, 210, 240, 270, 300, 330, 345, 360, 390, 420, 480, 540, 570, 600, 660, 720])

def generate_stealth_args(playwright: Any, browser_type: str = "chromium", 
                          headless: bool = False, proxy: Optional[Dict[str, str]] = None,
                          user_data_dir: Optional[str] = None, persistent: bool = False,
                          enable_fingerprint_evasion: bool = True,
                          evasion_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Generate stealth browser arguments.
    
    Args:
        playwright: Playwright instance
        browser_type: Type of browser ('chromium', 'firefox', or 'webkit')
        headless: Whether to run in headless mode
        proxy: Proxy configuration
        user_data_dir: User data directory for persistent context
        persistent: Whether to use a persistent context
        enable_fingerprint_evasion: Whether to enable advanced fingerprint evasion
        evasion_types: List of evasion types to apply (canvas, audio, font, webgl, battery, hardware)
    
    Returns:
        Dict with browser launch options and context options
    """
    # Choose a random platform
    platform = random.choice(list(USER_AGENTS.keys()))
    
    # Select a user agent consistent with the platform
    user_agent = generate_random_user_agent(platform)
    
    # Select viewport size
    viewport = random.choice(VIEWPORT_SIZES)
    
    # Select screen size
    screen = random.choice(SCREEN_RESOLUTIONS)
    
    # Generate device settings
    device_memory = generate_random_device_memory()
    hardware_concurrency = generate_random_hardware_concurrency()
    timezone_offset = generate_random_timezone_offset()
    language = random.choice(LANGUAGES)
    color_scheme = random.choice(["dark", "light", "no-preference"])
    
    # Select WebGL vendor and renderer
    webgl_info = random.choice(WEBGL_VENDORS)
    
    # Browser launch options
    browser_args = {
        "headless": headless
    }
    
    # Add proxy if provided
    if proxy:
        browser_args["proxy"] = proxy
    
    # Add user data directory for persistent context
    if persistent and user_data_dir:
        browser_args["user_data_dir"] = user_data_dir
    
    # Context options
    context_args = {
        "user_agent": user_agent,
        "viewport": viewport,
        "screen": {"width": screen[0], "height": screen[1]},
        "device_scale_factor": random.choice([1, 1.25, 1.5, 2]),
        "is_mobile": False,
        "has_touch": random.random() < 0.2,  # 20% chance of touch enabled
        "locale": language.split(",")[0].split("-")[0] + "-" + language.split(",")[0].split("-")[1],
        "timezone_id": random.choice([
            "America/New_York", "America/Los_Angeles", "America/Chicago", 
            "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Moscow",
            "Asia/Tokyo", "Asia/Shanghai", "Asia/Singapore", "Australia/Sydney"
        ]),
        "geolocation": None,  # Disabled by default
        "permissions": [],
        "color_scheme": color_scheme,
        "accept_downloads": True,
        "ignore_https_errors": False,
        "java_script_enabled": True,
        "bypass_csp": False,
        "http_credentials": None,
        "reduced_motion": random.choice(["reduce", "no-preference"]),
        "forced_colors": random.choice(["active", "none"]),
    }
    
    # Extra parameters for specific browser types
    if browser_type == "chromium":
        # Chrome-specific args
        chrome_args = [
            f"--device-memory={device_memory}",
            f"--renderer-process-limit={random.randint(2, 8)}",
            f"--hardcore-concurrency={hardware_concurrency}",
            "--disable-features=IsolateOrigins,site-per-process,SitePerProcess,AutomationControlled",
            "--disable-blink-features=AutomationControlled",
            "--disable-site-isolation-trials",
        ]
        
        # Additional Chrome args if headless
        if headless:
            chrome_args.extend([
                "--window-size=1920,1080",
                "--start-maximized",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--allow-running-insecure-content",
                "--disable-blink-features=AutomationControlled",
                "--disable-automation",
            ])
        
        # Add args to browser launch options
        browser_args["args"] = chrome_args
        
        # Set Chrome user preferences
        context_args["ignore_default_args"] = ["--enable-automation"]
        
    elif browser_type == "firefox":
        # Firefox-specific preferences
        browser_args["firefox_user_prefs"] = {
            "media.navigator.streams.fake": False,
            "browser.cache.disk.enable": True,
            "browser.cache.memory.enable": True,
            "browser.cache.offline.enable": True,
            "network.http.use-cache": True,
            "privacy.trackingprotection.enabled": False,
            "dom.webdriver.enabled": False,
            "dom.enable_performance": True,
        }
    
    # Store the selected browser and context configuration
    config = {
        "browser_args": browser_args,
        "context_args": context_args,
        "has_advanced_fingerprinting": enable_fingerprint_evasion,
        "evasion_types": evasion_types or ['canvas', 'audio', 'font', 'webgl', 'battery', 'hardware']
    }
    
    return config

async def setup_stealth_browser(playwright: Any, browser_type: str = "chromium", 
                              headless: bool = False, proxy: Optional[Dict[str, str]] = None,
                              user_data_dir: Optional[str] = None, persistent: bool = False,
                              enable_fingerprint_evasion: bool = True,
                              evasion_types: Optional[List[str]] = None) -> Tuple[Any, Any]:
    """
    Set up a stealth browser with anti-detection measures.
    
    Args:
        playwright: Playwright instance
        browser_type: Type of browser ('chromium', 'firefox', or 'webkit')
        headless: Whether to run in headless mode
        proxy: Proxy configuration
        user_data_dir: User data directory for persistent context
        persistent: Whether to use a persistent context
        enable_fingerprint_evasion: Whether to enable advanced fingerprint evasion
        evasion_types: List of evasion types to apply
    
    Returns:
        Tuple of (browser, context)
    """
    try:
        # Get browser and context options
        config = generate_stealth_args(
            playwright=playwright,
            browser_type=browser_type,
            headless=headless,
            proxy=proxy,
            user_data_dir=user_data_dir,
            persistent=persistent,
            enable_fingerprint_evasion=enable_fingerprint_evasion,
            evasion_types=evasion_types
        )
        
        browser_args = config["browser_args"]
        context_args = config["context_args"]
        
        # Get the appropriate browser launcher based on type
        if browser_type == "chromium":
            browser_launcher = playwright.chromium
        elif browser_type == "firefox":
            browser_launcher = playwright.firefox
        elif browser_type == "webkit":
            browser_launcher = playwright.webkit
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")
        
        # Launching browser and creating context
        if persistent and user_data_dir:
            # For persistent context, launch browser with persistent context
            context = await browser_launcher.launch_persistent_context(
                user_data_dir=user_data_dir,
                **{**browser_args, **context_args}
            )
            browser = context.browser
        else:
            # For non-persistent, launch browser then create context
            browser = await browser_launcher.launch(**browser_args)
            context = await browser.new_context(**context_args)
        
        # Create a new page
        page = await context.new_page()
        
        # Apply additional stealth scripts to hide automation
        await apply_stealth_scripts(page, browser_type)
        
        # Apply advanced fingerprint evasion if enabled
        if enable_fingerprint_evasion:
            await apply_fingerprint_evasion(page, evasion_types)
            await apply_consistent_fingerprint(page)
        
        logger.info(f"Stealth {browser_type} browser setup complete")
        return browser, context
        
    except Exception as e:
        logger.error(f"Error setting up stealth browser: {str(e)}")
        raise

async def apply_stealth_scripts(page: Any, browser_type: str = "chromium") -> None:
    """
    Apply stealth scripts to hide automation flags.
    
    Args:
        page: Playwright page object
        browser_type: Type of browser
    """
    # Basic stealth script to remove automation flags
    await page.add_init_script("""
    () => {
        // Overwrite the automation flag
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        
        // Remove automation-related properties
        if (window.navigator.plugins) {
            // Overwrite plugins with a non-empty array
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [1, 2, 3, 4, 5];
                }
            });
            
            // Overwrite mimeTypes with a non-empty array
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => {
                    return [1, 2, 3, 4, 5];
                }
            });
        }
        
        // Hide Chrome headless flags
        if (window.chrome === undefined) {
            window.chrome = {
                runtime: {}
            };
        }
        
        // Create a fake permission query method
        if (!('permissions' in navigator)) {
            navigator.permissions = {
                query: () => Promise.resolve({ state: 'granted' })
            };
        }
    }
    """)
    
    # Browser-specific scripts
    if browser_type == "chromium":
        # Additional Chrome-specific stealth scripts
        await page.add_init_script("""
        () => {
            // Override properties that leak headless mode
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Fake resolution and dimensions
            ['height', 'width'].forEach(property => {
                const imageDescriptor = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, property);
                Object.defineProperty(HTMLImageElement.prototype, property, {
                    ...imageDescriptor,
                    get: function() {
                        if (this.complete && this.naturalHeight == 0) {
                            return 20;
                        }
                        return imageDescriptor.get.apply(this);
                    }
                });
            });
            
            // Hide automation artifacts
            const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return originalGetParameter.apply(this, arguments);
            };
        }
        """)
    
    elif browser_type == "firefox":
        # Firefox-specific stealth scripts
        await page.add_init_script("""
        () => {
            // Hide Firefox-specific automation flags
            Object.defineProperty(window, 'mozInnerScreenX', {
                get: () => 0
            });
            Object.defineProperty(window, 'mozInnerScreenY', {
                get: () => 0
            });
            
            // Override Notification API
            if (window.Notification) {
                window.Notification.requestPermission = function() {
                    return Promise.resolve('granted');
                };
            }
        }
        """)
    
    logger.debug(f"Applied stealth scripts for {browser_type}") 