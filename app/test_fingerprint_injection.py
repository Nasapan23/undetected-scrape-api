"""
Test script to demonstrate fingerprint injection technique and its effectiveness in evading detection.
Run this test with: python -m app.test_fingerprint_injection
"""
import asyncio
import os
import time
from loguru import logger
from playwright.async_api import async_playwright
from app.utils.fingerprint_injection import FingerprintGenerator, inject_fingerprint

# Target URLs to test against various detection mechanisms
TEST_URLS = {
    "fingerprint_test": "https://browserleaks.com/canvas",
    "cloudflare_test": "https://nowsecure.nl/",  # Common Cloudflare protected site
    "creep_js": "https://abrahamjuliot.github.io/creepjs/",  # Advanced fingerprinting detection
    "webgl_test": "https://browserleaks.com/webgl",
    "webrtc_test": "https://browserleaks.com/webrtc"
}

async def setup_browser(browser_type="chrome", headless=False):
    """
    Setup a browser with specified options
    
    Args:
        browser_type: Type of browser to use (chrome, firefox)
        headless: Whether to run in headless mode
        
    Returns:
        tuple: (playwright, browser) instances
    """
    playwright = await async_playwright().start()
    
    # Setup browser launch options
    browser_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-site-isolation-trials",
    ]
    
    # Launch the appropriate browser type
    if browser_type.lower() == "firefox":
        browser = await playwright.firefox.launch(
            headless=headless,
            slow_mo=20
        )
    else:  # Default to Chrome/Chromium
        browser = await playwright.chromium.launch(
            headless=headless,
            args=browser_args,
            channel="chrome" if browser_type.lower() == "chrome" else None,
            ignore_default_args=["--enable-automation"],
            slow_mo=20
        )
    
    return playwright, browser

async def test_without_injection():
    """Test browser fingerprinting detection without any injection"""
    logger.info("=== Starting test WITHOUT fingerprint injection ===")
    
    playwright, browser = await setup_browser(headless=False)
    
    try:
        # Create context with default settings
        context = await browser.new_context()
        page = await context.new_page()
        
        # Test against fingerprinting detection
        logger.info("Testing against CreepJS fingerprinting detection...")
        await page.goto(TEST_URLS["creep_js"])
        await page.wait_for_timeout(5000)  # Wait for page to fully load
        
        # Take a screenshot
        os.makedirs("screenshots", exist_ok=True)
        await page.screenshot(path="screenshots/without_injection_creepjs.png", full_page=True)
        logger.info("Screenshot saved to screenshots/without_injection_creepjs.png")
        
        # Test against WebGL detection
        logger.info("Testing WebGL fingerprinting...")
        await page.goto(TEST_URLS["webgl_test"])
        await page.wait_for_timeout(3000)
        await page.screenshot(path="screenshots/without_injection_webgl.png")
        logger.info("Screenshot saved to screenshots/without_injection_webgl.png")
        
        # Test Cloudflare
        logger.info("Testing Cloudflare detection...")
        await page.goto(TEST_URLS["cloudflare_test"])
        await page.wait_for_timeout(5000)
        await page.screenshot(path="screenshots/without_injection_cloudflare.png")
        logger.info("Screenshot saved to screenshots/without_injection_cloudflare.png")
        
        logger.info("Tests without injection completed")
        
    finally:
        await browser.close()
        await playwright.stop()

async def test_with_injection():
    """Test browser fingerprinting detection with fingerprint injection"""
    logger.info("=== Starting test WITH fingerprint injection ===")
    
    # Generate a consistent fingerprint
    generator = FingerprintGenerator()
    fingerprint = generator.generate_fingerprint(
        browser_type="chrome", 
        os_type="windows",
        device_type="desktop"
    )
    
    logger.info(f"Generated fingerprint: {fingerprint['browser']['type']} on {fingerprint['os']['type']}")
    
    playwright, browser = await setup_browser(headless=False)
    
    try:
        # Create context with viewport and user agent from fingerprint
        context = await browser.new_context(
            viewport={
                "width": fingerprint["device"]["screen"]["width"],
                "height": fingerprint["device"]["screen"]["height"]
            },
            user_agent=fingerprint["browser"]["user_agent"],
            locale=fingerprint["browser"]["language"],
            timezone_id=fingerprint["timezone"]["name"],
        )
        
        page = await context.new_page()
        
        # Apply the fingerprint injection
        logger.info("Applying fingerprint injection...")
        await inject_fingerprint(page, fingerprint)
        
        # Add WebRTC protection
        await page.add_init_script("""
        () => {
            // Protect against WebRTC leaks
            if (typeof RTCPeerConnection !== 'undefined') {
                const originalRTCPeerConnection = window.RTCPeerConnection;
                
                window.RTCPeerConnection = function(...args) {
                    if (args[0] && args[0].iceServers) {
                        args[0].iceServers = [];
                    }
                    
                    const pc = new originalRTCPeerConnection(...args);
                    
                    // Override createOffer to prevent IP leaks
                    const originalCreateOffer = pc.createOffer.bind(pc);
                    pc.createOffer = function(offerOptions) {
                        const modifiedOptions = Object.assign({}, offerOptions || {});
                        modifiedOptions.offerToReceiveAudio = true;
                        modifiedOptions.offerToReceiveVideo = true;
                        return originalCreateOffer(modifiedOptions);
                    };
                    
                    return pc;
                };
                
                Object.setPrototypeOf(window.RTCPeerConnection, originalRTCPeerConnection);
            }
        }
        """)
        
        # Test against fingerprinting detection
        logger.info("Testing against CreepJS fingerprinting detection...")
        await page.goto(TEST_URLS["creep_js"])
        await page.wait_for_timeout(5000)  # Wait for page to fully load
        
        # Take a screenshot
        os.makedirs("screenshots", exist_ok=True)
        await page.screenshot(path="screenshots/with_injection_creepjs.png", full_page=True)
        logger.info("Screenshot saved to screenshots/with_injection_creepjs.png")
        
        # Test against WebGL detection
        logger.info("Testing WebGL fingerprinting...")
        await page.goto(TEST_URLS["webgl_test"])
        await page.wait_for_timeout(3000)
        await page.screenshot(path="screenshots/with_injection_webgl.png")
        logger.info("Screenshot saved to screenshots/with_injection_webgl.png")
        
        # Test Cloudflare
        logger.info("Testing Cloudflare detection...")
        await page.goto(TEST_URLS["cloudflare_test"])
        await page.wait_for_timeout(5000)
        await page.screenshot(path="screenshots/with_injection_cloudflare.png")
        logger.info("Screenshot saved to screenshots/with_injection_cloudflare.png")
        
        logger.info("Tests with injection completed")
        
    finally:
        await browser.close()
        await playwright.stop()

async def test_with_undetected_args():
    """Test with undetected browser arguments only, no injection"""
    logger.info("=== Starting test with undetected browser arguments only ===")
    
    # Enhanced browser arguments from undetected-playwright
    undetected_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process,TranslateUI",
        "--disable-site-isolation-trials",
        "--disable-setuid-sandbox",
        "--no-sandbox",
        "--disable-infobars",
        "--no-default-browser-check",
        "--no-first-run",
        "--ignore-certificate-errors",
        "--ignore-ssl-errors",
        "--allow-running-insecure-content",
    ]
    
    playwright = await async_playwright().start()
    
    try:
        # Launch browser with undetected args
        browser = await playwright.chromium.launch(
            headless=False, 
            args=undetected_args,
            ignore_default_args=["--enable-automation"],
            slow_mo=20
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # Test against fingerprinting detection
        logger.info("Testing against CreepJS fingerprinting detection...")
        await page.goto(TEST_URLS["creep_js"])
        await page.wait_for_timeout(5000)
        
        # Take a screenshot
        os.makedirs("screenshots", exist_ok=True)
        await page.screenshot(path="screenshots/undetected_args_creepjs.png", full_page=True)
        logger.info("Screenshot saved to screenshots/undetected_args_creepjs.png")
        
        # Test Cloudflare
        logger.info("Testing Cloudflare detection...")
        await page.goto(TEST_URLS["cloudflare_test"])
        await page.wait_for_timeout(5000)
        await page.screenshot(path="screenshots/undetected_args_cloudflare.png")
        logger.info("Screenshot saved to screenshots/undetected_args_cloudflare.png")
        
        logger.info("Tests with undetected arguments completed")
        
    finally:
        await browser.close()
        await playwright.stop()

async def test_with_full_stealth():
    """Test with both undetected args and fingerprint injection - full stealth mode"""
    logger.info("=== Starting test with FULL stealth mode ===")
    
    # Generate a consistent fingerprint
    generator = FingerprintGenerator()
    fingerprint = generator.generate_fingerprint(
        browser_type="chrome", 
        os_type="windows",
        device_type="desktop"
    )
    
    # Enhanced browser arguments
    stealth_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-site-isolation-trials",
        "--disable-setuid-sandbox",
        "--no-sandbox",
        "--disable-infobars",
        "--no-default-browser-check",
        "--no-first-run",
    ]
    
    playwright = await async_playwright().start()
    
    try:
        # Launch browser with stealth args
        browser = await playwright.chromium.launch(
            headless=False, 
            args=stealth_args,
            ignore_default_args=["--enable-automation"],
            slow_mo=20
        )
        
        # Create context with fingerprint data
        context = await browser.new_context(
            viewport={
                "width": fingerprint["device"]["screen"]["width"],
                "height": fingerprint["device"]["screen"]["height"]
            },
            user_agent=fingerprint["browser"]["user_agent"],
            locale=fingerprint["browser"]["language"],
            timezone_id=fingerprint["timezone"]["name"],
        )
        
        page = await context.new_page()
        
        # Apply the fingerprint injection
        logger.info("Applying fingerprint injection...")
        await inject_fingerprint(page, fingerprint)
        
        # Apply additional stealth measures
        await page.add_init_script("""
        () => {
            // Remove automation flags
            delete navigator.webdriver;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            
            // Protect against WebRTC leaks
            if (typeof RTCPeerConnection !== 'undefined') {
                const originalRTCPeerConnection = window.RTCPeerConnection;
                
                window.RTCPeerConnection = function(...args) {
                    if (args[0] && args[0].iceServers) {
                        args[0].iceServers = [];
                    }
                    
                    const pc = new originalRTCPeerConnection(...args);
                    
                    // Override createOffer to prevent IP leaks
                    const originalCreateOffer = pc.createOffer.bind(pc);
                    pc.createOffer = function(offerOptions) {
                        const modifiedOptions = Object.assign({}, offerOptions || {});
                        modifiedOptions.offerToReceiveAudio = true;
                        modifiedOptions.offerToReceiveVideo = true;
                        return originalCreateOffer(modifiedOptions);
                    };
                    
                    return pc;
                };
                
                Object.setPrototypeOf(window.RTCPeerConnection, originalRTCPeerConnection);
            }
            
            // Override Error stack traces to remove playwright references
            const originalPrepareStackTrace = Error.prepareStackTrace;
            if (originalPrepareStackTrace) {
                Error.prepareStackTrace = function(error, structuredStackTrace) {
                    const stack = originalPrepareStackTrace.call(this, error, structuredStackTrace);
                    return stack.replace(/playwright/gi, 'chrome');
                };
            }
        }
        """)
        
        # Test against fingerprinting detection
        logger.info("Testing against CreepJS fingerprinting detection...")
        await page.goto(TEST_URLS["creep_js"])
        await page.wait_for_timeout(5000)
        
        # Take a screenshot
        os.makedirs("screenshots", exist_ok=True)
        await page.screenshot(path="screenshots/full_stealth_creepjs.png", full_page=True)
        logger.info("Screenshot saved to screenshots/full_stealth_creepjs.png")
        
        # Test against WebGL detection
        logger.info("Testing WebGL fingerprinting...")
        await page.goto(TEST_URLS["webgl_test"])
        await page.wait_for_timeout(3000)
        await page.screenshot(path="screenshots/full_stealth_webgl.png")
        logger.info("Screenshot saved to screenshots/full_stealth_webgl.png")
        
        # Test WebRTC
        logger.info("Testing WebRTC leak prevention...")
        await page.goto(TEST_URLS["webrtc_test"])
        await page.wait_for_timeout(3000)
        await page.screenshot(path="screenshots/full_stealth_webrtc.png")
        logger.info("Screenshot saved to screenshots/full_stealth_webrtc.png")
        
        # Test Cloudflare
        logger.info("Testing Cloudflare detection...")
        await page.goto(TEST_URLS["cloudflare_test"])
        await page.wait_for_timeout(5000)
        await page.screenshot(path="screenshots/full_stealth_cloudflare.png")
        logger.info("Screenshot saved to screenshots/full_stealth_cloudflare.png")
        
        logger.info("Full stealth mode tests completed")
        
    finally:
        await browser.close()
        await playwright.stop()

async def main():
    """Run all tests sequentially"""
    logger.info("Starting fingerprint injection tests")
    
    # Run test without injection
    await test_without_injection()
    
    # Small delay between tests
    await asyncio.sleep(2)
    
    # Run test with undetected args only
    await test_with_undetected_args()
    
    # Small delay between tests
    await asyncio.sleep(2)
    
    # Run test with injection
    await test_with_injection()
    
    # Small delay between tests
    await asyncio.sleep(2)
    
    # Run test with full stealth
    await test_with_full_stealth()
    
    logger.info("All tests completed. Check the screenshots directory for results.")

if __name__ == "__main__":
    # Set up logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=""))
    
    # Run all tests
    asyncio.run(main()) 