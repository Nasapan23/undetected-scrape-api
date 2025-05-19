# Undetected Scrape API

A powerful, stealth-focused web scraping API with advanced fingerprint evasion techniques to bypass bot detection systems.

## Features

- **Advanced Fingerprint Evasion** - Realistic browser fingerprints to evade detection
- **Browser Stealth** - Multiple layers of stealth techniques to avoid detection
- **Proxy Support** - Integrate with residential and datacenter proxies
- **Cloudflare Bypass** - Specialized techniques to bypass Cloudflare protection
- **Human-like Interaction** - Simulates natural user behavior (mouse movement, scrolling)
- **Multiple Browser Support** - Works with Chrome, Firefox, and WebKit

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/undetected-scrape-api
cd undetected-scrape-api
```

### Standard Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

### Docker Installation (Recommended for Production)

This project is Docker-ready for production deployment. To get started:

1. Copy the environment example file:
   ```bash
   cp env.example .env
   ```
   
2. Edit the `.env` file with your desired configuration

3. Run the deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
   
4. Or manually run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

The API will be available at http://localhost:5000 with health monitoring at http://localhost:5000/health

## Quick Start

The API can be used programmatically or through a Flask server.

### Using the Flask API

Start the Flask development server:

```bash
python app.py
```

Make a request to scrape a URL:

```bash
curl -X POST "http://localhost:5000/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "use_stealth": true}'
```

### Using the Library Programmatically

```python
from app.services.browser_stealth import create_stealth_page
from playwright.async_api import async_playwright

async def scrape_with_stealth():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Create a page with full stealth features
        page = await create_stealth_page(browser)
        
        # Navigate to the target site
        await page.goto("https://target-site.com")
        
        # Extract data
        data = await page.content()
        
        # Close everything
        await browser.close()
        
        return data

# Run the async function
import asyncio
result = asyncio.run(scrape_with_stealth())
print(result)
```

## Recent Enhancements

### Advanced Fingerprint Injection

We've added a powerful new fingerprint injection system that makes your browser appear completely legitimate to anti-bot systems. Key features:

- **Complete Browser Emulation** - Mimics real browsers with consistent fingerprints 
- **Hardware & OS Emulation** - Realistic hardware and OS configurations
- **GPU Fingerprinting Bypass** - Spoofs WebGL renderer and vendor information
- **Audio Fingerprinting Bypass** - Adds subtle noise to audio fingerprints
- **Canvas Fingerprinting Protection** - Prevents canvas-based tracking

### Undetected Browser Integration

Integration with undetected-playwright techniques:

- **Runtime.enable patching** - Prevents automation flags from being detected
- **Chrome DevTools Protocol Modifications** - Prevents detection through CDP
- **Error Stack Trace Cleaning** - Removes automation markers from error messages

### WebRTC Leak Prevention

Protection against revealing your real IP address through WebRTC:

- **Connection Policy Override** - Forces relay-only connections
- **STUN/TURN Server Blocking** - Prevents direct connection establishment 
- **IP Masking** - Ensures WebRTC requests don't leak identifying information

## Usage Examples

### Basic Stealth Scraping

```python
from app.services.browser import get_browser
from app.services.browser_stealth import create_stealth_page
import asyncio

async def scrape_with_stealth():
    browser = get_browser()
    page = await create_stealth_page(browser)
    
    await page.goto("https://example.com")
    content = await page.content()
    
    return content

# Run the async function
result = asyncio.run(scrape_with_stealth())
```

### Cloudflare Bypass

```python
from app.services.browser_stealth import create_stealth_page, apply_cloudflare_bypass
from app.services.browser import get_browser
import asyncio

async def bypass_cloudflare_site():
    browser = get_browser()
    page = await create_stealth_page(browser)
    
    # Go to Cloudflare protected site
    await page.goto("https://cloudflare-protected-site.com")
    
    # Apply specialized Cloudflare bypass technique
    bypass_success = await apply_cloudflare_bypass(page)
    
    if bypass_success:
        # Continue with scraping
        content = await page.content()
        return content
    else:
        return "Failed to bypass Cloudflare"

# Run the async function
result = asyncio.run(bypass_cloudflare_site())
```

### Custom Fingerprint

```python
from app.utils.fingerprint_injection import FingerprintGenerator, inject_fingerprint
from playwright.async_api import async_playwright
import asyncio

async def scrape_with_custom_fingerprint():
    # Create a generator with a custom seed for reproducibility
    generator = FingerprintGenerator(seed="my-consistent-seed")
    
    # Generate a Mac + Safari fingerprint
    fingerprint = generator.generate_fingerprint(
        browser_type="safari",
        os_type="macos",
        device_type="desktop"
    )
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Create context with fingerprint settings
        context = await browser.new_context(
            viewport={
                "width": fingerprint["device"]["screen"]["width"],
                "height": fingerprint["device"]["screen"]["height"]
            },
            user_agent=fingerprint["browser"]["user_agent"]
        )
        
        page = await context.new_page()
        
        # Apply the fingerprint
        await inject_fingerprint(page, fingerprint)
        
        # Continue with scraping
        await page.goto("https://example.com")
        content = await page.content()
        
        await browser.close()
        return content

# Run the async function
result = asyncio.run(scrape_with_custom_fingerprint())
```

## Testing Your Fingerprint

Use the included test script to verify the effectiveness of our fingerprint evasion:

```bash
python -m app.test_fingerprint_injection
```

This will:
1. Run tests with different configurations (vanilla, undetected args, fingerprint injection, full stealth)
2. Visit fingerprinting detection sites to test effectiveness
3. Save screenshots for comparing results

## Configuration

The API can be configured through environment variables or a configuration file:

- `BROWSER_TYPE`: Browser to use (chromium, firefox, webkit)
- `BROWSER_CHANNEL`: Specific browser channel (chrome, msedge)
- `HEADLESS`: Whether to run in headless mode (true/false)
- `USE_UNDETECTED`: Use undetected-playwright if available (true/false)
- `USER_AGENT_ROTATION`: Enable random user agent rotation (true/false)
- `PROXY_ENABLED`: Enable proxy usage (true/false)
- `PROXY_TYPE`: Type of proxy to use (http, socks5)
- `PROXY_HOST`: Proxy host address
- `PROXY_PORT`: Proxy port
- `PROXY_USERNAME`: Proxy username (if required)
- `PROXY_PASSWORD`: Proxy password (if required)

## Extending

The API is designed to be extensible:

1. Add new stealth techniques in `app/services/stealth.py`
2. Add new fingerprint components in `app/utils/fingerprint_injection.py`
3. Customize browser behavior in `app/services/browser.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Ensure you use this tool responsibly and in compliance with websites' terms of service and applicable laws.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Troubleshooting

### Dependency Installation Issues

If you encounter issues with package dependencies during installation:

1. Try updating pip first:
   ```bash
   pip install --upgrade pip
   ```

2. Install packages individually if needed:
   ```bash
   cat requirements.txt | grep -v "^#" | xargs -n 1 pip install
   ```

3. For Playwright-related issues, install only what's needed:
   ```bash
   playwright install chromium
   playwright install-deps chromium
   ```

### Docker Build Issues

If Docker build fails due to dependency conflicts:

1. Try building with the `--no-cache` option:
   ```bash
   docker-compose build --no-cache
   ```

2. Ensure your Docker daemon has sufficient resources allocated

3. Check for network issues that might affect downloading packages 