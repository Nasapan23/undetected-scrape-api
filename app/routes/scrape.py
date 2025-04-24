"""
Scraping endpoint for the API
"""
from flask import Blueprint, request, current_app, jsonify
from app.services.browser import (
    get_browser, 
    get_context_options, 
    handle_cloudflare_challenge, 
    simulate_human_interaction,
    manage_cookies
)
from app.utils.error_handler import handle_error
import traceback
from loguru import logger
import random
import time
import re
from urllib.parse import urlparse

bp = Blueprint("scrape", __name__, url_prefix="/scrape")

def is_valid_url(url):
    """
    Validate if a URL is properly formatted
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except:
        return False

def is_blocked_page(page):
    """
    Check if the page shows signs of being blocked or restricted
    
    Args:
        page: Playwright page
    
    Returns:
        bool: True if page appears to be blocked
    """
    try:
        # Get page title and content
        title = page.title().lower()
        content = page.inner_text("body").lower()
        url = page.url.lower()
        
        # Check for Cloudflare in URL or content
        if "cloudflare" in url or "cloudflare" in content:
            logger.warning("Detected Cloudflare in URL or content")
            return True
            
        # Check for common block indicators in multiple languages
        block_indicators = [
            # English
            "blocked", "captcha", "robot", "automated", "bot", 
            "suspicious", "unusual activity", "security check",
            "attention required", "ddos", "forbidden",
            "sorry", "access denied", "verify you are human",
            
            # Italian
            "ci siamo quasi", "dimostra di essere un utente umano", "completando l'azione",
            "richiesto un controllo", "utente umano", "prestazioni e sicurezza",
            
            # Spanish
            "comprueba que eres humano", "estamos comprobando", "desafío de seguridad",
            
            # French
            "vérification que vous êtes humain", "prouvez que vous êtes humain",
            "nous vérifions", "contrôle de sécurité",
            
            # German
            "überprüfung", "bitte bestätigen sie", "sicherheitsabfrage"
        ]
        
        # Check title and prominent content
        for indicator in block_indicators:
            if indicator in title:
                logger.warning(f"Block indicator in title: {indicator}")
                return True
        
        # Check content for block messages
        block_phrases = [
            # English
            "please verify you are human",
            "unusual traffic",
            "automated access",
            "browser check",
            "you have been blocked",
            "access to this page has been denied",
            "checking if the site connection is secure",
            "waiting for verification",
            
            # Italian
            "dimostra di essere un utente umano",
            "completando l'azione",
            "controllo aggiuntivo",
            "ray id",
            
            # Spanish
            "comprueba que eres humano",
            "comprobando si la conexión del sitio es segura",
            
            # French
            "vérifier que vous êtes humain",
            "nous vérifions si le site est sécurisé",
            
            # German
            "bitte bestätigen sie, dass sie kein roboter sind",
            "schützen sie ihre website"
        ]
        
        for phrase in block_phrases:
            if phrase in content:
                logger.warning(f"Block phrase in content: {phrase}")
                return True
        
        try:
            # Safer approach to check for element count - avoid accessing elements directly
            element_count = 0
            try:
                # Use JavaScript to count elements safely
                element_count = page.evaluate("""() => {
                    return document.querySelectorAll('p, div, h1, h2, h3, h4, h5, h6').length;
                }""")
            except Exception as e:
                logger.warning(f"Error evaluating element count: {str(e)}")
                element_count = 0  # Default to 0 on error
            
            if element_count < 5:
                text_content = content.strip()
                # If the page has very little content and contains keywords that suggest challenge
                keywords = ["check", "secure", "wait", "human", "utente", "security", "challenge"]
                if len(text_content) < 500 and any(keyword in text_content for keyword in keywords):
                    logger.warning(f"Suspiciously small page with challenge keywords. Element count: {element_count}")
                    return True
        except Exception as e:
            logger.warning(f"Error checking page structure: {str(e)}")
            # If we can't check elements, fall back to content-based checks
            if len(content.strip()) < 500:
                keywords = ["check", "secure", "wait", "human", "utente", "security", "challenge"]
                if any(keyword in content.lower() for keyword in keywords):
                    logger.warning("Small content with challenge keywords detected")
                    return True
        
        # Check for captcha/challenge related elements safely using evaluate
        challenge_selectors = [
            "input[type='checkbox']",
            ".captcha",
            ".challenge",
            ".cf-challenge",
            "[data-testid='challenge-spinner']",
            "[data-testid='challenge-body']",
            "[data-hcaptcha-response]",
            "[data-sitekey]",
            ".g-recaptcha"
        ]
        
        for selector in challenge_selectors:
            try:
                # Properly escape selector for JavaScript evaluation
                escaped_selector = selector.replace("'", "\\'")
                # Use JavaScript evaluation instead of query_selector to avoid element handling issues
                has_element = page.evaluate("""(selector) => {
                    return document.querySelector(selector) !== null;
                }""", escaped_selector)
                
                if has_element:
                    logger.warning(f"Found challenge element: {selector}")
                    return True
            except Exception as e:
                logger.warning(f"Error checking selector {selector}: {str(e)}")
                # Continue checking other selectors
                continue
        
        return False
    except Exception as e:
        logger.error(f"Error in is_blocked_page: {str(e)}")
        # If we can't properly check the page, assume it's not blocked
        # to avoid false positives
        return False

@bp.route("/", methods=["GET"])
def scrape():
    """
    Scrape a webpage with anti-detection measures
    
    Query Parameters:
        url (str): The URL to scrape
        wait_time (int, optional): Custom wait time in seconds
        retry (int, optional): Number of retry attempts
        
    Returns:
        JSON response with scraped data
    """
    try:
        # Get URL and parameters from request
        url = request.args.get("url")
        wait_time = request.args.get("wait_time", default=0, type=int)
        retry_attempts = request.args.get("retry", default=2, type=int)
        
        # Validate URL
        if not url:
            return jsonify({
                "status": "error",
                "message": "URL parameter is required"
            }), 400
            
        if not is_valid_url(url):
            return jsonify({
                "status": "error",
                "message": "Invalid URL format"
            }), 400
        
        # Get browser instance
        browser = get_browser()
        if not browser:
            return jsonify({
                "status": "error",
                "message": "Failed to initialize browser"
            }), 500
        
        # Initial context and page
        context = None
        page = None
        
        # Initialize retry counter
        current_attempt = 0
        max_attempts = max(1, min(retry_attempts, 5))  # Cap at 5 retries
        success = False
        data = {}
        
        # Special flags
        cloudflare_detected = False
        got_cloudflare_page = False
        
        while current_attempt < max_attempts and not success:
            try:
                # Clean up previous attempt resources
                if page:
                    page.close()
                if context:
                    context.close()
                
                if current_attempt > 0:
                    logger.info(f"Retry attempt {current_attempt} for {url}")
                    # Wait increasingly longer between retries
                    time.sleep(current_attempt * random.uniform(2.0, 5.0))
                
                # Create stealth context with randomized options
                context_options = get_context_options()
                context = browser.new_context(**context_options)
                
                # Create a new page
                page = context.new_page()
                
                # Add random delay before navigation
                time.sleep(random.uniform(1.0, 3.0))
                
                # Enhanced navigation options
                navigation_timeout = current_app.config.get("NAVIGATION_TIMEOUT", 60000)
                logger.info(f"Navigating to {url}")
                
                # Navigate to URL with wait_until="networkidle" for better page loading
                page.goto(url, wait_until="networkidle", timeout=navigation_timeout)
                
                # Add specified wait time or random wait
                actual_wait_time = wait_time if wait_time > 0 else random.uniform(2.0, 5.0)
                time.sleep(actual_wait_time)
                
                # Check if page appears to be blocked
                if is_blocked_page(page):
                    logger.warning("Detected block page indicators")
                    
                    # Special handling for cloudflare
                    if "cloudflare" in page.url.lower() or "cloudflare" in page.title().lower() or "cloudflare" in page.inner_text("body").lower():
                        logger.info("Detected Cloudflare challenge page")
                        cloudflare_detected = True
                        got_cloudflare_page = True
                        
                        # Try multiple times with additional waits for Cloudflare
                        cloudflare_bypass_attempts = 3
                        for cf_attempt in range(cloudflare_bypass_attempts):
                            # Try to solve Cloudflare
                            if handle_cloudflare_challenge(page):
                                logger.info(f"Successfully bypassed Cloudflare on attempt {cf_attempt+1}")
                                cloudflare_detected = False
                                # Wait after successful bypass before proceeding
                                time.sleep(random.uniform(3.0, 6.0))
                                break
                            
                            if cf_attempt < cloudflare_bypass_attempts - 1:
                                # Wait between Cloudflare bypass attempts
                                wait_time = random.uniform(5.0, 10.0)
                                logger.info(f"Waiting {wait_time:.1f}s before next Cloudflare bypass attempt")
                                time.sleep(wait_time)
                        
                        # If we still have Cloudflare and have retries left, restart with new context
                        if cloudflare_detected and current_attempt < max_attempts - 1:
                            raise Exception("Failed to bypass Cloudflare, retrying with new session")
                    
                    # If we're on the last attempt and still blocked, we'll try to get whatever data is available
                    if current_attempt >= max_attempts - 1:
                        logger.warning("Giving up on bypass attempts, returning what's available")
                    else:
                        raise Exception("Detected block page, retrying with new session")
                
                # Simulate human interaction with the page
                simulate_human_interaction(page)
                
                # Extract data after successfully loading
                data = {
                    "title": page.title(),
                    "content": page.inner_text("body"),
                    "links": page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('a')).map(a => a.href);
                    }""")
                }
                
                # If we previously got a Cloudflare page, and now we have a very short content,
                # it might still be a Cloudflare page with different text
                if got_cloudflare_page and len(data["content"]) < 500:
                    logger.warning(f"Got suspiciously short content after Cloudflare ({len(data['content'])} chars)")
                    # Check if it still contains any challenge-like text
                    challenge_indicators = ["ray id", "performance", "security", "check", "wait", "human"]
                    if any(indicator in data["content"].lower() for indicator in challenge_indicators):
                        logger.warning("Content appears to be a challenge page")
                        if current_attempt < max_attempts - 1:
                            # Try a much longer wait before the next attempt
                            logger.info("Waiting 20-30 seconds before next attempt")
                            time.sleep(random.uniform(20.0, 30.0))
                            raise Exception("Still on challenge page, retrying with extended wait")
                
                # Check if we got meaningful data
                if len(data["content"]) < 50 and current_attempt < max_attempts - 1:
                    logger.warning(f"Got suspiciously short content ({len(data['content'])} chars), may be blocked")
                    raise Exception("Received limited content, may be blocked")
                
                # Intelligently manage cookies to maintain sessions
                manage_cookies(page)
                
                success = True
                
            except Exception as e:
                logger.error(f"Error during attempt {current_attempt}: {str(e)}")
                current_attempt += 1
                
                try:
                    if page and page.url:
                        # Screenshot for debugging (uncomment if needed)
                        # debug_dir = "debug_screenshots"
                        # os.makedirs(debug_dir, exist_ok=True)
                        # page.screenshot(path=f"{debug_dir}/error_screenshot_{current_attempt}.png")
                        pass
                except:
                    pass
                
                if current_attempt >= max_attempts:
                    # If this was our last attempt and we have some data, return it anyway
                    if data and data.get("content"):
                        logger.warning("Returning partial data after exhausting retries")
                        success = True
                    else:
                        # If we have no data at all, re-raise the exception
                        raise e
        
        # Clean up resources
        if page:
            page.close()
        if context:
            context.close()
        
        # Return the scraped data
        return jsonify({
            "status": "success",
            "data": data
        })
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        logger.error(traceback.format_exc())
        return handle_error(e) 