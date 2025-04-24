"""
Fingerprint injection module for advanced browser stealth capabilities.
This module provides functionality to inject consistent browser fingerprints
to evade detection mechanisms used by anti-bot systems.
"""
import json
import random
import string
import time
from typing import Dict, Any, Optional, List, Union
from loguru import logger
from pathlib import Path

# Constants for fingerprinting
BROWSER_TYPES = ["chrome", "firefox", "safari", "edge"]
OS_TYPES = ["windows", "macos", "linux"]
DEVICE_TYPES = ["desktop", "mobile", "tablet"]

# GPU configurations for different platforms
GPU_PROFILES = {
    "windows": [
        {
            "vendor": "Google Inc.",
            "renderer": "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)"
        },
        {
            "vendor": "Google Inc.",
            "renderer": "ANGLE (NVIDIA GeForce GTX 1660 Direct3D11 vs_5_0 ps_5_0)"
        },
        {
            "vendor": "Google Inc.",
            "renderer": "ANGLE (AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)"
        },
        {
            "vendor": "Google Inc.",
            "renderer": "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"
        }
    ],
    "macos": [
        {
            "vendor": "Apple",
            "renderer": "Apple M1"
        },
        {
            "vendor": "Apple",
            "renderer": "Apple M2"
        },
        {
            "vendor": "Intel Inc.",
            "renderer": "Intel Iris Pro OpenGL Engine"
        }
    ],
    "linux": [
        {
            "vendor": "NVIDIA Corporation",
            "renderer": "NVIDIA GeForce GTX 1650/PCIe/SSE2"
        },
        {
            "vendor": "Mesa/X.org",
            "renderer": "Mesa DRI Intel(R) UHD Graphics 620 (Kabylake GT2)"
        },
        {
            "vendor": "AMD",
            "renderer": "AMD Radeon Pro 5500M OpenGL Engine"
        }
    ]
}

class FingerprintGenerator:
    """
    Generates consistent fingerprints for browser instances.
    
    This class creates realistic fingerprints that remain consistent
    throughout a browsing session to evade fingerprinting detection.
    """
    
    def __init__(self, seed: Optional[str] = None):
        """
        Initialize the fingerprint generator.
        
        Args:
            seed: Optional seed for reproducible fingerprints
        """
        self.seed = seed if seed else self._generate_seed()
        self._init_random()
    
    def _init_random(self):
        """Initialize random generator with seed for consistency"""
        random.seed(self.seed)
    
    def _generate_seed(self, length: int = 16) -> str:
        """Generate a random seed string"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def generate_fingerprint(self, 
                             browser_type: Optional[str] = None,
                             os_type: Optional[str] = None,
                             device_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a complete browser fingerprint.
        
        Args:
            browser_type: Type of browser (chrome, firefox, safari, edge)
            os_type: Type of OS (windows, macos, linux)
            device_type: Type of device (desktop, mobile, tablet)
            
        Returns:
            Dict containing a complete fingerprint configuration
        """
        self._init_random()  # Reset random to maintain consistency
        
        # Set defaults if not provided
        browser_type = browser_type or random.choice(BROWSER_TYPES)
        os_type = os_type or random.choice(OS_TYPES)
        device_type = device_type or "desktop"  # Default to desktop
        
        # Generate browser version based on browser type
        browser_version = self._generate_browser_version(browser_type)
        
        # Generate consistent values
        hardware_concurrency = random.choice([2, 4, 6, 8, 12, 16])
        device_memory = random.choice([2, 4, 8, 16])
        
        # Generate screen resolution based on device type
        screen_resolution = self._generate_screen_resolution(device_type)
        
        # Get appropriate GPU for OS
        gpu = random.choice(GPU_PROFILES.get(os_type, GPU_PROFILES["windows"]))
        
        # Create user agent
        user_agent = self._generate_user_agent(browser_type, browser_version, os_type)
        
        # Create timezone info
        timezone_info = self._generate_timezone_info()
        
        # Construct the fingerprint
        fingerprint = {
            "browser": {
                "type": browser_type,
                "version": browser_version,
                "user_agent": user_agent,
                "language": random.choice(["en-US", "en-GB", "fr-FR", "de-DE", "es-ES"]),
                "do_not_track": random.choice([None, "1"]),
                "plugins_length": random.randint(3, 10) if browser_type != "firefox" else 0,
            },
            "engine": {
                "hardware_concurrency": hardware_concurrency,
                "device_memory": device_memory,
                "max_touch_points": 0 if device_type == "desktop" else random.randint(1, 5),
            },
            "os": {
                "type": os_type,
                "version": self._generate_os_version(os_type)
            },
            "device": {
                "type": device_type,
                "screen": {
                    "width": screen_resolution[0],
                    "height": screen_resolution[1],
                    "color_depth": random.choice([24, 30, 32]),
                    "pixel_ratio": random.choice([1, 1.5, 2, 2.5, 3])
                },
            },
            "gpu": {
                "vendor": gpu["vendor"],
                "renderer": gpu["renderer"],
            },
            "timezone": timezone_info,
            "audio": {
                "state": random.choice(["allowed", "prompt", "denied"]),
            },
            "webrtc": {
                "mode": "proxy", # Ensure WebRTC respects proxy settings
                "public_ip": None, # Will be filled by the system
                "local_ip": None, # Will be filled by the system
            }
        }
        
        return fingerprint
    
    def _generate_browser_version(self, browser_type: str) -> str:
        """Generate realistic browser version based on browser type"""
        if browser_type == "chrome":
            return f"{random.randint(100, 122)}.0.{random.randint(0, 9999)}.{random.randint(0, 999)}"
        elif browser_type == "firefox":
            return f"{random.randint(100, 123)}.0"
        elif browser_type == "safari":
            return f"{random.randint(14, 17)}.{random.randint(0, 9)}"
        elif browser_type == "edge":
            return f"{random.randint(100, 122)}.0.{random.randint(0, 9999)}.{random.randint(0, 999)}"
        return "100.0.0.0"  # Default
    
    def _generate_os_version(self, os_type: str) -> str:
        """Generate OS version based on OS type"""
        if os_type == "windows":
            return random.choice(["10.0", "11.0"])
        elif os_type == "macos":
            return f"10.{random.randint(13, 15)}" 
        elif os_type == "linux":
            return random.choice(["5.10", "5.15", "6.0"])
        return "10.0"  # Default
    
    def _generate_screen_resolution(self, device_type: str) -> List[int]:
        """Generate screen resolution based on device type"""
        if device_type == "desktop":
            return random.choice([
                [1920, 1080],
                [2560, 1440],
                [1366, 768],
                [1440, 900],
                [1536, 864],
                [1680, 1050],
                [3840, 2160],  # 4K
            ])
        elif device_type == "mobile":
            return random.choice([
                [390, 844],  # iPhone 12, 13
                [414, 896],  # iPhone 11
                [375, 812],  # iPhone X
                [360, 780],  # Various Android phones
                [412, 915],  # Pixel 6
            ])
        elif device_type == "tablet":
            return random.choice([
                [768, 1024],  # iPad
                [834, 1112],  # iPad Pro 10.5"
                [1024, 1366],  # iPad Pro 12.9"
                [800, 1280],  # Various Android tablets
            ])
        return [1920, 1080]  # Default
    
    def _generate_user_agent(self, browser_type: str, browser_version: str, os_type: str) -> str:
        """Generate a realistic user agent string"""
        if browser_type == "chrome":
            if os_type == "windows":
                return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36"
            elif os_type == "macos":
                return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(13, 15)}_{random.randint(0, 9)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36"
            elif os_type == "linux":
                return f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36"
        elif browser_type == "firefox":
            if os_type == "windows":
                return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{browser_version.split('.')[0]}.0) Gecko/20100101 Firefox/{browser_version}"
            elif os_type == "macos":
                return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.{random.randint(13, 15)}; rv:{browser_version.split('.')[0]}.0) Gecko/20100101 Firefox/{browser_version}"
            elif os_type == "linux":
                return f"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:{browser_version.split('.')[0]}.0) Gecko/20100101 Firefox/{browser_version}"
        
        # Default to Chrome on Windows
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    def _generate_timezone_info(self) -> Dict[str, Any]:
        """Generate timezone information"""
        timezones = [
            {"name": "America/New_York", "offset": -5 * 60},
            {"name": "America/Los_Angeles", "offset": -8 * 60},
            {"name": "Europe/London", "offset": 0},
            {"name": "Europe/Berlin", "offset": 1 * 60},
            {"name": "Europe/Paris", "offset": 1 * 60},
            {"name": "Asia/Tokyo", "offset": 9 * 60},
            {"name": "Australia/Sydney", "offset": 10 * 60}
        ]
        
        selected_timezone = random.choice(timezones)
        return {
            "name": selected_timezone["name"],
            "offset": selected_timezone["offset"]
        }

def create_fingerprint_injection_script(fingerprint: Dict[str, Any]) -> str:
    """
    Create a JavaScript injection script to apply the fingerprint.
    
    Args:
        fingerprint: The fingerprint configuration to apply
        
    Returns:
        JavaScript code to inject
    """
    script = """
    (function() {
        // Store original functions to avoid detection of overrides
        const originalGetPrototypeOf = Object.getPrototypeOf;
        const originalDefineProperty = Object.defineProperty;
        const originalDefineProperties = Object.defineProperties;
        
        // Helper to safely define a property
        function safeDefineProperty(obj, prop, descriptor) {
            try {
                originalDefineProperty(obj, prop, descriptor);
            } catch (e) {
                console.debug('Could not define property:', prop, e);
            }
        }
        
        // Function to modify navigator properties
        function modifyNavigator() {
            const navigatorProps = {
                hardwareConcurrency: FINGERPRINT.engine.hardware_concurrency,
                deviceMemory: FINGERPRINT.engine.device_memory,
                userAgent: FINGERPRINT.browser.user_agent,
                platform: FINGERPRINT.os.type === 'windows' ? 'Win32' : 
                         (FINGERPRINT.os.type === 'macos' ? 'MacIntel' : 'Linux x86_64'),
                maxTouchPoints: FINGERPRINT.engine.max_touch_points,
                language: FINGERPRINT.browser.language,
                languages: [FINGERPRINT.browser.language],
                doNotTrack: FINGERPRINT.browser.do_not_track,
                webdriver: false
            };
            
            // Create a proxy for navigator
            const navigatorProxy = new Proxy(navigator, {
                get: function(target, key) {
                    if (key in navigatorProps) {
                        return navigatorProps[key];
                    }
                    return target[key];
                },
                has: function(target, key) {
                    if (key in navigatorProps) {
                        return true;
                    }
                    return key in target;
                }
            });
            
            // Try to override navigator
            try {
                // This won't actually work in most browsers, but it's part of the fingerprinting evasion
                window.navigator = navigatorProxy;
            } catch (e) {
                // Fallback to property-by-property overriding
                for (const [key, value] of Object.entries(navigatorProps)) {
                    try {
                        if (key === 'languages') continue; // Skip array property
                        
                        safeDefineProperty(Navigator.prototype, key, {
                            get: function() { return value; }
                        });
                    } catch (err) {
                        console.debug('Failed to override navigator.' + key, err);
                    }
                }
            }
            
            // Additional WebDriver evasion
            try {
                // Delete webdriver property
                delete navigator.webdriver;
                // Override navigator.webdriver
                safeDefineProperty(navigator, 'webdriver', {
                    get: function() { return false; }
                });
            } catch (e) {
                console.debug('Could not override webdriver property', e);
            }
        }
        
        // Function to modify screen properties
        function modifyScreen() {
            const screenProps = {
                width: FINGERPRINT.device.screen.width,
                height: FINGERPRINT.device.screen.height,
                colorDepth: FINGERPRINT.device.screen.color_depth,
                pixelDepth: FINGERPRINT.device.screen.color_depth,
                availWidth: FINGERPRINT.device.screen.width,
                availHeight: FINGERPRINT.device.screen.height - 40, // Simulate taskbar/dock
            };
            
            for (const [key, value] of Object.entries(screenProps)) {
                try {
                    safeDefineProperty(Screen.prototype, key, {
                        get: function() { return value; }
                    });
                } catch (e) {
                    console.debug('Failed to override screen.' + key, e);
                }
            }
            
            // Device pixel ratio
            try {
                safeDefineProperty(window, 'devicePixelRatio', {
                    get: function() { return FINGERPRINT.device.screen.pixel_ratio; }
                });
            } catch (e) {
                console.debug('Failed to override devicePixelRatio', e);
            }
        }
        
        // Function to modify WebGL properties
        function modifyWebGL() {
            const webglVendor = FINGERPRINT.gpu.vendor;
            const webglRenderer = FINGERPRINT.gpu.renderer;
            
            // Create function to override getParameter in WebGL contexts
            const getParameterProxyHandler = {
                apply: function(target, thisArg, args) {
                    const param = args[0];
                    // UNMASKED_VENDOR_WEBGL
                    if (param === 37445) {
                        return webglVendor;
                    }
                    // UNMASKED_RENDERER_WEBGL
                    if (param === 37446) {
                        return webglRenderer;
                    }
                    return target.apply(thisArg, args);
                }
            };
            
            // Apply to WebGLRenderingContext if it exists
            if (typeof WebGLRenderingContext !== 'undefined') {
                try {
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = new Proxy(getParameter, getParameterProxyHandler);
                } catch (e) {
                    console.debug('Failed to override WebGLRenderingContext.getParameter', e);
                }
            }
            
            // Apply to WebGL2RenderingContext if it exists
            if (typeof WebGL2RenderingContext !== 'undefined') {
                try {
                    const getParameter = WebGL2RenderingContext.prototype.getParameter;
                    WebGL2RenderingContext.prototype.getParameter = new Proxy(getParameter, getParameterProxyHandler);
                } catch (e) {
                    console.debug('Failed to override WebGL2RenderingContext.getParameter', e);
                }
            }
        }
        
        // Function to add canvas fingerprint protection
        function protectCanvas() {
            try {
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                
                // Override toDataURL
                HTMLCanvasElement.prototype.toDataURL = function(type) {
                    if (this.width > 16 && this.height > 16) {
                        // Add subtle noise to canvas data
                        const ctx = this.getContext('2d');
                        const imageData = ctx.getImageData(0, 0, this.width, this.height);
                        const pixels = imageData.data;
                        
                        // Add subtle random noise to pixels (minimal visual impact)
                        for (let i = 0; i < pixels.length; i += 4) {
                            // Only modify 5% of pixels with minimal changes
                            if (Math.random() < 0.05) {
                                // Add small random value to RGB channels
                                pixels[i] = Math.max(0, Math.min(255, pixels[i] + (Math.random() * 2 - 1)));     // R
                                pixels[i+1] = Math.max(0, Math.min(255, pixels[i+1] + (Math.random() * 2 - 1))); // G
                                pixels[i+2] = Math.max(0, Math.min(255, pixels[i+2] + (Math.random() * 2 - 1))); // B
                            }
                        }
                        
                        ctx.putImageData(imageData, 0, 0);
                    }
                    return originalToDataURL.apply(this, arguments);
                };
                
                // Override getImageData with subtle noise
                CanvasRenderingContext2D.prototype.getImageData = function() {
                    const imageData = originalGetImageData.apply(this, arguments);
                    
                    // Add subtle noise to large image data (to avoid fingerprinting)
                    if (imageData.width > 16 && imageData.height > 16) {
                        const pixels = imageData.data;
                        for (let i = 0; i < pixels.length; i += 4) {
                            if (Math.random() < 0.02) { // Only modify 2% of pixels
                                // Add minor noise (-1, 0, or 1) to RGB values
                                pixels[i] = Math.max(0, Math.min(255, pixels[i] + (Math.random() > 0.5 ? 1 : -1)));
                                pixels[i+1] = Math.max(0, Math.min(255, pixels[i+1] + (Math.random() > 0.5 ? 1 : -1)));
                                pixels[i+2] = Math.max(0, Math.min(255, pixels[i+2] + (Math.random() > 0.5 ? 1 : -1)));
                                // Alpha remains unchanged
                            }
                        }
                    }
                    
                    return imageData;
                };
            } catch (e) {
                console.debug('Failed to protect canvas fingerprinting', e);
            }
        }
        
        // Protect against getClientRects fingerprinting
        function protectClientRects() {
            try {
                const originalGetClientRects = Element.prototype.getClientRects;
                Element.prototype.getClientRects = function() {
                    const rects = originalGetClientRects.apply(this, arguments);
                    // Add tiny random noise to measurements for fingerprinting prevention
                    for (let i = 0; i < rects.length; i++) {
                        const rect = rects[i];
                        const noise = 0.0000001;
                        rect.x += Math.random() * noise;
                        rect.y += Math.random() * noise;
                        rect.width += Math.random() * noise;
                        rect.height += Math.random() * noise;
                    }
                    return rects;
                };
                
                const originalGetBoundingClientRect = Element.prototype.getBoundingClientRect;
                Element.prototype.getBoundingClientRect = function() {
                    const rect = originalGetBoundingClientRect.apply(this, arguments);
                    // Clone the rect to make it writable
                    const newRect = {};
                    for (const prop of Object.keys(rect)) {
                        newRect[prop] = rect[prop];
                    }
                    // Add tiny random noise
                    const noise = 0.0000001;
                    newRect.x += Math.random() * noise;
                    newRect.y += Math.random() * noise;
                    newRect.width += Math.random() * noise;
                    newRect.height += Math.random() * noise;
                    return newRect;
                };
            } catch (e) {
                console.debug('Failed to protect client rects fingerprinting', e);
            }
        }
        
        // Override timezone methods
        function modifyTimezone() {
            try {
                const timezoneOffset = FINGERPRINT.timezone.offset;
                
                // Override Date.prototype.getTimezoneOffset
                const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
                Date.prototype.getTimezoneOffset = function() {
                    return timezoneOffset;
                };
                
                // Try to override Intl.DateTimeFormat
                if (typeof Intl !== 'undefined' && typeof Intl.DateTimeFormat !== 'undefined') {
                    const originalDateTimeFormat = Intl.DateTimeFormat;
                    const originalDateTimeFormatResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
                    
                    Intl.DateTimeFormat.prototype.resolvedOptions = function() {
                        const result = originalDateTimeFormatResolvedOptions.apply(this, arguments);
                        result.timeZone = FINGERPRINT.timezone.name;
                        return result;
                    };
                }
            } catch (e) {
                console.debug('Failed to modify timezone', e);
            }
        }
        
        // Apply all modifications
        function applyFingerprint() {
            modifyNavigator();
            modifyScreen();
            modifyWebGL();
            protectCanvas();
            protectClientRects();
            modifyTimezone();
            console.debug('Fingerprint applied successfully');
        }
        
        // Set fingerprint data from the injected object
        const FINGERPRINT = FINGERPRINT_PLACEHOLDER;
        
        // Apply fingerprint modifications
        applyFingerprint();
    })();
    """
    
    # Replace the placeholder with the actual fingerprint
    script = script.replace('FINGERPRINT_PLACEHOLDER', json.dumps(fingerprint))
    
    return script

async def inject_fingerprint(page, fingerprint: Optional[Dict[str, Any]] = None, 
                        browser_type: Optional[str] = None,
                        os_type: Optional[str] = None,
                        device_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Inject a fingerprint into a Playwright page.
    
    Args:
        page: Playwright page object
        fingerprint: Optional pre-defined fingerprint to inject
        browser_type: Browser type to mimic if generating a new fingerprint
        os_type: OS type to mimic if generating a new fingerprint
        device_type: Device type to mimic if generating a new fingerprint
        
    Returns:
        The injected fingerprint
    """
    try:
        # Generate fingerprint if not provided
        if not fingerprint:
            generator = FingerprintGenerator()
            fingerprint = generator.generate_fingerprint(
                browser_type=browser_type,
                os_type=os_type,
                device_type=device_type
            )
        
        # Create injection script with the fingerprint
        injection_script = create_fingerprint_injection_script(fingerprint)
        
        # Inject the script to modify browser fingerprint
        await page.add_init_script(injection_script)
        
        logger.info(f"Injected fingerprint: {browser_type or fingerprint['browser']['type']} on {os_type or fingerprint['os']['type']}")
        return fingerprint
    
    except Exception as e:
        logger.error(f"Failed to inject fingerprint: {e}")
        # Return empty dict if failed
        return {} 