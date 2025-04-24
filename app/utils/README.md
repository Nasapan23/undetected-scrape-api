# Fingerprint Evasion Utilities

This directory contains advanced utilities for browser fingerprint evasion in your web scraping projects.

## Features

- **Fingerprint injection** - Inject consistent, realistic browser fingerprints
- **Canvas fingerprint evasion** - Prevents canvas-based fingerprinting
- **WebGL fingerprint evasion** - Spoofs WebGL vendor and renderer information
- **Audio fingerprint protection** - Adds subtle noise to audio fingerprints
- **Navigator properties protection** - Customizes navigator properties to prevent detection
- **WebRTC leak prevention** - Prevents WebRTC from leaking real IP addresses
- **Consistent fingerprints** - Generate fingerprints that remain consistent during a session

## Key Components

### fingerprint_injection.py

Provides advanced fingerprint injection capabilities that modify the browser environment to mimic real user browsers. It generates consistent fingerprints that include:

- Browser type, version, and user agent
- Hardware specs (memory, CPU cores)
- Screen resolutions and color depth
- GPU vendor and renderer information
- Navigator properties
- WebRTC configuration
- Timezone settings

### fp_evasion.py

Contains various browser fingerprinting evasion techniques:

- Canvas fingerprint protection
- Audio fingerprint protection
- Font fingerprint protection
- WebGL fingerprint protection
- Hardware fingerprint consistency

## Usage Examples

### Basic Usage with Playwright

```python
from playwright.async_api import async_playwright
from app.utils.fingerprint_injection import inject_fingerprint, FingerprintGenerator

async def run_with_fingerprint_evasion():
    async with async_playwright() as p:
        # Launch browser with anti-detection args
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Create a new fingerprint
        generator = FingerprintGenerator()
        fingerprint = generator.generate_fingerprint(
            browser_type="chrome", 
            os_type="windows"
        )
        
        # Create context with fingerprint settings
        context = await browser.new_context(
            viewport={
                "width": fingerprint["device"]["screen"]["width"],
                "height": fingerprint["device"]["screen"]["height"]
            },
            user_agent=fingerprint["browser"]["user_agent"],
            locale=fingerprint["browser"]["language"],
            timezone_id=fingerprint["timezone"]["name"]
        )
        
        # Create page
        page = await context.new_page()
        
        # Apply fingerprint injection
        await inject_fingerprint(page, fingerprint)
        
        # Now browse normally
        await page.goto("https://example.com")
        # ...rest of your code
```

### Using with browser_stealth Service

Our browser_stealth.py service integrates these fingerprint evasion techniques:

```python
from app.services.browser_stealth import create_stealth_page

async def run_with_stealth_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Create a stealth page with fingerprint evasion already applied
        page = await create_stealth_page(browser)
        
        # Now browse as normal
        await page.goto("https://example.com")
        # ...rest of your code
```

## Testing

To test the effectiveness of the fingerprint evasion techniques, run the test script:

```bash
python -m app.test_fingerprint_injection
```

This will run a series of tests against different fingerprinting detection mechanisms:
- CreepJS advanced fingerprint detection
- WebGL fingerprinting
- WebRTC leak detection
- Cloudflare bot detection

The test script will save screenshots in a `screenshots` directory for you to compare the different approaches.

## Advanced Configuration

You can customize the fingerprint generation by specifying parameters:

```python
# Generate a fingerprint for a mobile device
fingerprint = generator.generate_fingerprint(
    browser_type="chrome",
    os_type="android",
    device_type="mobile"
)

# Or a MacOS device with Firefox
fingerprint = generator.generate_fingerprint(
    browser_type="firefox",
    os_type="macos",
    device_type="desktop"
)
```

## Integration with Cloudflare Bypass

The fingerprint evasion utilities work well with our Cloudflare bypass module. When used together, they provide a comprehensive solution for accessing websites protected by sophisticated anti-bot measures.

```python
from app.services.cloudflare import bypass_cloudflare
from app.utils.fingerprint_injection import inject_fingerprint, FingerprintGenerator

async def access_cloudflare_protected_site():
    # ... create browser and page with fingerprint injection
    
    # Visit Cloudflare protected site
    await page.goto("https://cloudflare-protected-site.com")
    
    # Apply Cloudflare bypass if needed
    bypass_result = await bypass_cloudflare(page)
    
    if bypass_result:
        print("Successfully bypassed Cloudflare protection")
    
    # Continue with your scraping...
``` 