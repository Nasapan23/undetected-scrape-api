"""
Proxy management service for IP rotation
"""
import random
import time
import os
from loguru import logger
from flask import current_app

class ProxyManager:
    """Manages proxy rotation for web scraping requests"""
    
    def __init__(self):
        """Initialize the proxy manager"""
        self.proxies = []
        self.last_used = {}  # Track when a proxy was last used
        self.banned_proxies = set()  # Track banned/non-working proxies
        self.max_uses_per_proxy = 5  # Maximum number of uses before rotation
        self.min_proxy_rotation_time = 30  # Min seconds between using the same proxy
        self.load_proxies()
    
    def load_proxies(self):
        """
        Load proxies from environment variables or configuration
        """
        # Load from environment variables if available
        proxy_list = os.getenv("PROXY_LIST", "")
        if proxy_list:
            self.proxies = [p.strip() for p in proxy_list.split(",") if p.strip() and not p.strip().startswith('#')]
            logger.info(f"Loaded {len(self.proxies)} proxies from environment variables")
            return
            
        # If no proxies in env vars, try to load from a file
        proxy_file = os.getenv("PROXY_FILE", "config/proxies.txt")
        try:
            if os.path.exists(proxy_file):
                with open(proxy_file, 'r') as f:
                    # Only include lines that aren't comments and aren't empty
                    self.proxies = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                if self.proxies:
                    logger.info(f"Loaded {len(self.proxies)} proxies from {proxy_file}")
                else:
                    logger.warning(f"No valid proxies found in {proxy_file}")
            else:
                logger.warning(f"No proxy file found at {proxy_file}")
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
    
    def get_proxy(self):
        """
        Get the next available proxy using a smart rotation algorithm
        
        Returns:
            str: Proxy string in the format "host:port" or None if no proxies available
        """
        if not self.proxies:
            logger.debug("No proxies available, continuing without proxy")
            return None
            
        # Filter out banned proxies and recently used ones
        current_time = time.time()
        available_proxies = [
            p for p in self.proxies 
            if p not in self.banned_proxies and 
            (p not in self.last_used or 
             current_time - self.last_used[p]["last_time"] > self.min_proxy_rotation_time)
        ]
        
        if not available_proxies:
            # If all proxies are on cooldown, use the one that was used longest ago
            if self.last_used:
                proxy = min(self.last_used.items(), key=lambda x: x[1]["last_time"])[0]
                logger.warning(f"All proxies on cooldown, reusing oldest proxy: {self._mask_proxy(proxy)}")
            else:
                proxy = random.choice(self.proxies)
                logger.warning(f"No usage data for proxies, choosing random: {self._mask_proxy(proxy)}")
        else:
            # Choose a proxy with preference for less used ones
            proxies_with_usage = [
                (p, self.last_used.get(p, {"uses": 0})["uses"]) 
                for p in available_proxies
            ]
            
            # Sort by usage count (less used first)
            proxies_with_usage.sort(key=lambda x: x[1])
            
            # Select from the least used 1/3 of proxies for better distribution
            selection_pool = proxies_with_usage[:max(1, len(proxies_with_usage) // 3)]
            proxy = random.choice(selection_pool)[0]
            
        # Update usage statistics
        if proxy in self.last_used:
            self.last_used[proxy]["uses"] += 1
            self.last_used[proxy]["last_time"] = current_time
        else:
            self.last_used[proxy] = {"uses": 1, "last_time": current_time}
            
        logger.info(f"Using proxy: {self._mask_proxy(proxy)}")
        return proxy
    
    def mark_proxy_bad(self, proxy):
        """
        Mark a proxy as bad/banned after failed request
        
        Args:
            proxy: The proxy string to mark as bad
        """
        if proxy and proxy in self.proxies:
            self.banned_proxies.add(proxy)
            logger.warning(f"Marked proxy as bad: {self._mask_proxy(proxy)}")
    
    def get_playwright_proxy_option(self):
        """
        Get the proxy configuration for Playwright
        
        Returns:
            dict: Proxy configuration for Playwright or None if no proxy available
        """
        proxy = self.get_proxy()
        if not proxy:
            return None
            
        # Parse proxy string (expected format: host:port)
        try:
            host, port = proxy.split(':')
            return {
                "server": f"http://{host}:{port}"
            }
        except Exception as e:
            logger.error(f"Invalid proxy format: {proxy} - {e}")
            return None
    
    def _mask_proxy(self, proxy):
        """Mask proxy for logging to avoid exposing full IP"""
        if not proxy:
            return None
            
        try:
            parts = proxy.split(':')
            if len(parts) == 2:
                ip_parts = parts[0].split('.')
                if len(ip_parts) == 4:
                    masked_ip = f"{ip_parts[0]}.{ip_parts[1]}.*.*:{parts[1]}"
                    return masked_ip
            return "[masked]"
        except:
            return "[masked]"

# Create singleton instance
proxy_manager = ProxyManager()

def get_proxy_for_playwright():
    """
    Get proxy configuration for Playwright
    
    Returns:
        dict: Playwright proxy configuration or None
    """
    # Only use proxies if enabled in configuration and proxies exist
    if current_app.config.get("USE_PROXIES", False) and proxy_manager.proxies:
        return proxy_manager.get_playwright_proxy_option()
    return None

def mark_proxy_bad(proxy):
    """
    Mark a proxy as bad (helper function)
    
    Args:
        proxy: The proxy to mark as bad
    """
    if proxy:
        proxy_manager.mark_proxy_bad(proxy) 