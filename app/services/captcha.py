import os
import time
import random
import asyncio
from loguru import logger
from typing import Optional

class CaptchaSolver:
    """Base class for captcha solving"""
    
    async def solve(self, page, **kwargs):
        raise NotImplementedError("Solver not implemented")


class HcaptchaSolver(CaptchaSolver):
    """Solver for hCaptcha challenges"""
    
    async def solve(self, page, **kwargs):
        """
        Attempts to solve hCaptcha challenges on a page
        
        Args:
            page: Playwright page object
            **kwargs: Additional parameters
            
        Returns:
            bool: True if solved, False otherwise
        """
        logger.info("Attempting to solve hCaptcha")
        
        # Check if hCaptcha is present
        hcaptcha_frame = await page.query_selector("iframe[src*='hcaptcha']")
        if not hcaptcha_frame:
            logger.info("No hCaptcha found on page")
            return False
            
        try:
            # Click on the checkbox to start the challenge
            await page.frame_locator("iframe[src*='hcaptcha.com/captcha']").locator(".checkbox").click()
            await page.wait_for_timeout(2000)  # Wait for challenge to load
            
            # Check if we need to solve image challenge
            challenge_frame = await page.query_selector("iframe[src*='newassets.hcaptcha.com']")
            if challenge_frame:
                logger.warning("Complex hCaptcha image challenge detected - using external service")
                
                # If using an external service, implement the API call here
                captcha_api_key = os.getenv("CAPTCHA_API_KEY")
                if captcha_api_key:
                    logger.info("Attempting to solve using external service")
                    # Implement external service API call
                    
                    # Simulate waiting for external service response
                    await page.wait_for_timeout(10000)
                    
                    # Check if challenge solved
                    if await page.query_selector("iframe[src*='newassets.hcaptcha.com']"):
                        logger.error("Failed to solve hCaptcha challenge")
                        return False
                    else:
                        logger.success("hCaptcha challenge solved successfully")
                        return True
                else:
                    logger.error("No captcha API key found - cannot solve complex challenge")
                    return False
            
            # Wait for the captcha to be marked as solved
            await page.wait_for_selector(".checkbox.checked", timeout=5000)
            logger.success("hCaptcha solved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error solving hCaptcha: {str(e)}")
            return False


class RecaptchaSolver(CaptchaSolver):
    """Solver for Google reCAPTCHA challenges"""
    
    async def solve(self, page, **kwargs):
        """
        Attempts to solve reCAPTCHA challenges on a page
        
        Args:
            page: Playwright page object
            **kwargs: Additional parameters
            
        Returns:
            bool: True if solved, False otherwise
        """
        logger.info("Attempting to solve reCAPTCHA")
        
        # Check if reCAPTCHA is present
        recaptcha_frame = await page.query_selector("iframe[src*='recaptcha']")
        if not recaptcha_frame:
            logger.info("No reCAPTCHA found on page")
            return False
            
        try:
            # Click on the checkbox to start the challenge
            await page.frame_locator("iframe[title='reCAPTCHA']").locator(".recaptcha-checkbox-border").click()
            await page.wait_for_timeout(2000)  # Wait for challenge to load
            
            # Check if we need to solve image challenge
            challenge_frame = await page.query_selector("iframe[title='recaptcha challenge']")
            if challenge_frame:
                logger.warning("Complex reCAPTCHA image challenge detected - using external service")
                
                # If using an external service, implement the API call here
                captcha_api_key = os.getenv("CAPTCHA_API_KEY")
                if captcha_api_key:
                    logger.info("Attempting to solve using external service")
                    # Implement external service API call
                    
                    # Simulate waiting for external service response
                    await page.wait_for_timeout(10000)
                    
                    # Check if challenge solved
                    if await page.query_selector("iframe[title='recaptcha challenge']"):
                        logger.error("Failed to solve reCAPTCHA challenge")
                        return False
                    else:
                        logger.success("reCAPTCHA challenge solved successfully")
                        return True
                else:
                    logger.error("No captcha API key found - cannot solve complex challenge")
                    return False
            
            # Wait for the captcha to be marked as solved
            await page.wait_for_selector(".recaptcha-checkbox-checked", timeout=5000)
            logger.success("reCAPTCHA solved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA: {str(e)}")
            return False


async def solve_captcha(page, timeout: int = 30000) -> bool:
    """
    Detects and solves captchas on a page with fingerprint evasion
    
    Args:
        page: Playwright page object
        timeout: Maximum time to try solving in milliseconds
        
    Returns:
        bool: True if solved, False otherwise
    """
    # Ensure we're using proper human-like fingerprints
    # This helps reduce captcha appearance in the first place
    await _simulate_random_human_behavior(page)
    
    # Detect captcha type
    captcha_type = await _detect_captcha_type(page)
    if not captcha_type:
        logger.info("No recognized captcha detected")
        return True
        
    solver: Optional[CaptchaSolver] = None
    
    if captcha_type == "hcaptcha":
        solver = HcaptchaSolver()
    elif captcha_type == "recaptcha":
        solver = RecaptchaSolver()
    else:
        logger.warning(f"Unsupported captcha type: {captcha_type}")
        return False
        
    # Try to solve with timeout
    start_time = time.time()
    end_time = start_time + (timeout / 1000)
    
    while time.time() < end_time:
        if await solver.solve(page):
            # Verify page is accessible after solving
            await page.wait_for_timeout(2000)
            return True
            
        # Wait before retrying
        await page.wait_for_timeout(3000)
        
    logger.error(f"Failed to solve {captcha_type} within timeout period")
    return False


async def _detect_captcha_type(page) -> Optional[str]:
    """
    Detects the type of captcha present on a page
    
    Args:
        page: Playwright page object
        
    Returns:
        str: Captcha type ("hcaptcha", "recaptcha", or None)
    """
    # Check for hCaptcha
    hcaptcha_frame = await page.query_selector("iframe[src*='hcaptcha']")
    if hcaptcha_frame:
        return "hcaptcha"
        
    # Check for reCAPTCHA
    recaptcha_frame = await page.query_selector("iframe[src*='recaptcha']")
    if recaptcha_frame:
        return "recaptcha"
        
    # Check for text indicators
    content = await page.content()
    if "hcaptcha" in content.lower():
        return "hcaptcha"
    if "recaptcha" in content.lower():
        return "recaptcha"
        
    return None


async def _simulate_random_human_behavior(page):
    """
    Simulates random human-like behavior to reduce captcha suspicion
    
    Args:
        page: Playwright page object
    """
    try:
        # Random mouse movements
        viewport = await page.viewport_size()
        if viewport:
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, viewport["width"] - 200)
                y = random.randint(100, viewport["height"] - 200)
                await page.mouse.move(x, y)
                await page.wait_for_timeout(random.randint(200, 800))
        
        # Random scrolling
        await page.evaluate("""
        () => {
            const scrollHeight = document.body.scrollHeight;
            const viewportHeight = window.innerHeight;
            const scrollPositions = [
                viewportHeight / 2,
                viewportHeight,
                scrollHeight / 2,
                scrollHeight / 3,
                scrollHeight / 1.5
            ];
            
            for (const pos of scrollPositions) {
                window.scrollTo({
                    top: Math.min(pos, scrollHeight - viewportHeight),
                    behavior: 'smooth'
                });
            }
        }
        """)
        
        # Random pauses
        await page.wait_for_timeout(random.randint(500, 1500))
        
    except Exception as e:
        logger.warning(f"Error during human behavior simulation: {str(e)}") 