import json
import traceback
import os
from flask import Blueprint, current_app, request, jsonify, g
from loguru import logger
from app.services.browser import get_browser, handle_cloudflare_challenge, simulate_human_interaction
from app.utils.request_utils import validate_scrape_request, validate_headers
from app.services.captcha import solve_captcha
from app.utils.fingerprint_injection import FingerprintGenerator, inject_fingerprint
from app.utils.fingerprint_profiles import get_or_create_profile, get_profile_manager

scraper_bp = Blueprint('scraper', __name__, url_prefix='/api/v1')

@scraper_bp.route('/scrape', methods=['POST'])
async def scrape():
    """
    Main scraping endpoint that handles website navigation and content extraction
    with anti-detection and Cloudflare bypass capabilities
    """
    try:
        # Validate the incoming request
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "Invalid JSON payload"}), 400
        
        validation_result = validate_scrape_request(request_data)
        if validation_result:
            return jsonify({"error": validation_result}), 400
            
        # Extract parameters
        url = request_data.get('url')
        wait_for = request_data.get('wait_for', 5000)  # Default 5 seconds
        selectors = request_data.get('selectors', [])
        extract_html = request_data.get('extract_html', False)
        bypass_cloudflare = request_data.get('bypass_cloudflare', True)
        handle_captcha = request_data.get('handle_captcha', True)
        apply_stealth = request_data.get('apply_stealth', True)
        
        # Fingerprint evasion parameters
        use_fingerprint_evasion = request_data.get('use_fingerprint_evasion', 
                                                  os.getenv('ENABLE_FINGERPRINT_EVASION', 'true').lower() == 'true')
        profile_id = request_data.get('profile_id')
        browser_type = request_data.get('browser_type', os.getenv('BROWSER_TYPE', 'chromium'))
        os_type = request_data.get('os_type')
        device_type = request_data.get('device_type', 'desktop')
        
        # Get browser from app context
        browser = get_browser()
        
        # Get or create fingerprint profile if evasion is enabled
        fingerprint = None
        profile = None
        if use_fingerprint_evasion:
            try:
                profile = get_or_create_profile(
                    profile_id=profile_id,
                    browser_type=browser_type,
                    os_type=os_type,
                    device_type=device_type
                )
                fingerprint = profile.get('fingerprint')
                logger.info(f"Using fingerprint profile: {profile.get('id')}")
            except Exception as e:
                logger.error(f"Error loading fingerprint profile: {str(e)}")
                # If profile loading fails, generate a new fingerprint
                generator = FingerprintGenerator()
                fingerprint = generator.generate_fingerprint(
                    browser_type=browser_type,
                    os_type=os_type,
                    device_type=device_type
                )
                logger.info("Generated new fingerprint for session")
        
        # Create browser context with appropriate options
        context_options = {}
        if fingerprint:
            # Apply fingerprint settings to context options
            context_options = {
                "viewport": {
                    "width": fingerprint["device"]["screen"]["width"],
                    "height": fingerprint["device"]["screen"]["height"]
                },
                "user_agent": fingerprint["browser"]["user_agent"],
                "locale": fingerprint["browser"]["language"],
                "timezone_id": fingerprint["timezone"]["name"],
                "color_scheme": "light"
            }
        
        # Create context and page
        context = browser.new_context(**context_options) if context_options else browser.new_context()
        page = context.new_page()
        
        try:
            # Apply fingerprint injection if available
            if fingerprint and use_fingerprint_evasion:
                logger.info("Applying fingerprint injection to page")
                await inject_fingerprint(page, fingerprint)
                
            # Add WebRTC protection script
            if use_fingerprint_evasion:
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
            
            # Go to the target URL
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Apply enhanced stealth techniques if requested
            if apply_stealth:
                await simulate_human_interaction(page)
                
            # Handle Cloudflare protection if needed
            if bypass_cloudflare and "cloudflare" in await page.content().lower():
                logger.info(f"Cloudflare detected on {url}, attempting bypass...")
                await handle_cloudflare_challenge(page)
            
            # Handle any captchas that appear
            if handle_captcha and ("captcha" in await page.content().lower() or 
                                  await page.query_selector("iframe[src*='captcha']") or
                                  await page.query_selector("iframe[src*='recaptcha']")):
                logger.info(f"Captcha detected on {url}, attempting to solve...")
                await solve_captcha(page)
                
            # Wait for content to load
            await page.wait_for_timeout(wait_for)
            
            # Extract data from selectors
            result = {
                "url": page.url,
                "title": await page.title(),
                "data": {}
            }
            
            # Process each selector
            for selector_info in selectors:
                selector = selector_info.get('selector')
                name = selector_info.get('name', selector)
                get_text = selector_info.get('get_text', True)
                get_attribute = selector_info.get('attribute')
                
                try:
                    elements = await page.query_selector_all(selector)
                    
                    if get_attribute:
                        # Extract attribute value from elements
                        values = [await element.get_attribute(get_attribute) for element in elements if element]
                    elif get_text:
                        # Extract text content from elements
                        values = [await element.inner_text() for element in elements if element]
                    else:
                        # Get outerHTML if neither text nor attribute is specified
                        values = [await element.evaluate('el => el.outerHTML') for element in elements if element]
                    
                    result["data"][name] = values
                except Exception as e:
                    result["data"][name] = []
                    logger.error(f"Error extracting data for selector {selector}: {str(e)}")
            
            # Include full HTML if requested
            if extract_html:
                result["html"] = await page.content()
                
            # Get cookies as dictionary
            cookies = {}
            for cookie in await context.cookies():
                cookies[cookie["name"]] = cookie["value"]
                
            result["cookies"] = cookies
            
            # Include fingerprint information if used
            if fingerprint and use_fingerprint_evasion:
                result["fingerprint"] = {
                    "browser": fingerprint["browser"]["type"],
                    "os": fingerprint["os"]["type"],
                    "device": device_type,
                    "profile_id": profile.get("id") if profile else None
                }
            
            return jsonify(result)
        finally:
            # Clean up resources
            await page.close()
            await context.close()
            
    except Exception as e:
        logger.error(f"Scraper error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500 