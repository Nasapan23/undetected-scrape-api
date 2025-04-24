"""
Advanced stealth techniques for browser fingerprint evasion
"""
import json
import random
import string
import os
from loguru import logger
from pathlib import Path

class StealthConfig:
    """Configuration for advanced stealth techniques"""
    
    # WebGL vendor and renderer to use (randomized if None)
    WEBGL_VENDOR = None
    WEBGL_RENDERER = None
    
    # Standard vendors and renderers for common GPUs
    WEBGL_VENDORS = ['Google Inc.', 'Intel Inc.', 'NVIDIA Corporation', 'AMD']
    WEBGL_RENDERERS = [
        'ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'ANGLE (AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'Mesa DRI Intel(R) HD Graphics 520 (Skylake GT2)',
        'ANGLE (Apple, Apple M1, OpenGL 4.1)'
    ]
    
    # Navigator platform options
    PLATFORMS = [
        'Win32', 'MacIntel', 'Linux x86_64', 'Linux i686'
    ]
    
    # Hardware concurrency (CPU cores) options
    HARDWARE_CONCURRENCY = [2, 4, 6, 8, 12, 16]
    
    # Device memory options (in GB)
    DEVICE_MEMORY = [2, 4, 8, 16, 32]
    
    # Screen color depth options
    COLOR_DEPTH = [24, 30, 32]
    
    # Browser plugin formats to mimic
    PLUGINS = [
        {"name": "Chrome PDF Plugin", "filename": "internal-pdf-viewer"},
        {"name": "Chrome PDF Viewer", "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai"},
        {"name": "Native Client", "filename": "internal-nacl-plugin"}
    ]

def generate_webgl_info():
    """Generate randomized WebGL vendor and renderer information"""
    vendor = StealthConfig.WEBGL_VENDOR or random.choice(StealthConfig.WEBGL_VENDORS)
    renderer = StealthConfig.WEBGL_RENDERER or random.choice(StealthConfig.WEBGL_RENDERERS)
    return {'vendor': vendor, 'renderer': renderer}

def generate_device_info():
    """Generate consistent device information"""
    return {
        'platform': random.choice(StealthConfig.PLATFORMS),
        'hardwareConcurrency': random.choice(StealthConfig.HARDWARE_CONCURRENCY),
        'deviceMemory': random.choice(StealthConfig.DEVICE_MEMORY),
        'colorDepth': random.choice(StealthConfig.COLOR_DEPTH),
    }

def get_stealth_js():
    """
    Get the JavaScript code needed to inject stealth features into the page
    
    Returns:
        str: JavaScript code for stealth features
    """
    # Generate random but consistent fingerprint data
    webgl = generate_webgl_info()
    device = generate_device_info()
    
    # Read the stealth script from file if it exists
    stealth_script_path = Path(__file__).parent / "stealth.js"
    if stealth_script_path.exists():
        with open(stealth_script_path, 'r') as f:
            script = f.read()
    else:
        # Otherwise use our built-in script
        script = """
        // Stealth script to evade fingerprinting
        
        (function() {
            // Override navigator properties
            const navigatorProps = {
                webdriver: false,
                language: navigator.language,
                languages: navigator.languages,
                platform: "${platform}",
                hardwareConcurrency: ${hardwareConcurrency},
                deviceMemory: ${deviceMemory},
                userAgent: navigator.userAgent,
            };
            
            // WebGL fingerprint spoofing
            const webglVendor = "${webgl_vendor}";
            const webglRenderer = "${webgl_renderer}";
            
            // Override properties
            Object.keys(navigatorProps).forEach(key => {
                if (key === 'languages') return; // Skip languages array
                Object.defineProperty(navigator, key, {
                    get: () => navigatorProps[key]
                });
            });
            
            // Hide automation
            delete Object.getPrototypeOf(navigator).webdriver;
            
            // WebGL fingerprint spoofing
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
            
            // Apply WebGL proxy if WebGLRenderingContext exists
            if (typeof WebGLRenderingContext !== 'undefined') {
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = new Proxy(getParameter, getParameterProxyHandler);
            }
            
            // Create fake plugins array
            const mockPlugins = [
                { name: "Chrome PDF Plugin", filename: "internal-pdf-viewer" },
                { name: "Chrome PDF Viewer", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai" },
                { name: "Native Client", filename: "internal-nacl-plugin" }
            ];
            
            // Define plugins property to return our fake plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = mockPlugins.map(plugin => ({
                        name: plugin.name,
                        filename: plugin.filename,
                        description: "",
                        length: 1,
                        item: (index) => index === 0 ? plugin : null,
                        namedItem: (name) => name === plugin.name ? plugin : null,
                        refresh: () => {},
                        [0]: plugin,
                    }));
                    
                    // Add array-like properties
                    plugins.item = index => plugins[index] || null;
                    plugins.namedItem = name => plugins.find(p => p.name === name) || null;
                    plugins.refresh = () => {};
                    plugins.length = plugins.length;
                    
                    return plugins;
                }
            });
            
            // Override permissions
            if (typeof Permissions !== 'undefined' && Permissions.prototype.query) {
                const originalQuery = Permissions.prototype.query;
                Permissions.prototype.query = function(parameters) {
                    return Promise.resolve({
                        state: "granted",
                        onchange: null
                    });
                };
            }
            
            // Override battery API
            if ('getBattery' in navigator) {
                navigator.getBattery = function() {
                    return Promise.resolve({
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 1.0,
                        addEventListener: () => {},
                        removeEventListener: () => {}
                    });
                };
            }
            
            // Disguise user-agent platform if needed
            if (navigator.userAgent.includes('Linux') && navigatorProps.platform.includes('Win')) {
                if (typeof navigator.userAgentData !== 'undefined') {
                    Object.defineProperty(navigator, 'userAgentData', {
                        get: () => {
                            const originalData = navigator.userAgentData;
                            return new Proxy(originalData, {
                                get: (target, prop) => {
                                    if (prop === 'platform') return 'Windows';
                                    return Reflect.get(target, prop);
                                }
                            });
                        }
                    });
                }
            }
            
            // Anti-detection for getClientRects() and getBoundingClientRect()
            const originalGetClientRects = Element.prototype.getClientRects;
            Element.prototype.getClientRects = function() {
                const rects = originalGetClientRects.apply(this, arguments);
                // Add tiny random noise to measurements
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
            
            // Canvas fingerprint protection
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
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
            
            // Additional audio fingerprinting protection
            if (typeof AudioBuffer !== 'undefined') {
                const originalGetChannelData = AudioBuffer.prototype.getChannelData;
                AudioBuffer.prototype.getChannelData = function(channel) {
                    const data = originalGetChannelData.call(this, channel);
                    
                    // Only modify audio data occasionally to minimize impact on audio quality
                    if (Math.random() < 0.1) {
                        const noise = 0.0001;  // Very minimal noise
                        
                        // Apply noise to a small percentage of samples
                        for (let i = 0; i < data.length; i += 1000) {
                            if (Math.random() < 0.01) {
                                data[i] += (Math.random() * 2 - 1) * noise;
                            }
                        }
                    }
                    
                    return data;
                };
            }
            
            // Override WebRTC
            if (typeof RTCPeerConnection !== 'undefined') {
                const originalRTCPeerConnection = window.RTCPeerConnection;
                
                window.RTCPeerConnection = function(...args) {
                    if (args[0] && args[0].iceServers) {
                        args[0].iceServers = [];
                    }
                    
                    const pc = new originalRTCPeerConnection(...args);
                    
                    // Override createOffer
                    const originalCreateOffer = pc.createOffer.bind(pc);
                    pc.createOffer = function(offerOptions) {
                        const modifiedOptions = Object.assign({}, offerOptions || {});
                        modifiedOptions.offerToReceiveAudio = true;
                        modifiedOptions.offerToReceiveVideo = true;
                        return originalCreateOffer(modifiedOptions);
                    };
                    
                    return pc;
                };
                
                // Copy the prototype and statics
                Object.setPrototypeOf(window.RTCPeerConnection, originalRTCPeerConnection);
                window.RTCPeerConnection.prototype = originalRTCPeerConnection.prototype;
            }
            
            // Prevent iframe fingerprinting
            try {
                Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                    get: function() {
                        const result = this.realContentWindow || HTMLIFrameElement.prototype.contentWindow;
                        
                        if (this.src && this.src.startsWith('http') && 
                            !(this.src.includes(window.location.hostname))) {
                            Object.defineProperty(result, 'navigator', {
                                get: () => window.navigator,
                                configurable: true
                            });
                        }
                        
                        return result;
                    }
                });
            } catch(e) {
                // Iframe protection failed, but not critical
            }
            
            // Notify that we've applied stealth measures
            console.debug("Stealth protections applied");
        })();
        """
    
    # Replace placeholders with our generated values
    script = script.replace("${platform}", device['platform'])
    script = script.replace("${hardwareConcurrency}", str(device['hardwareConcurrency']))
    script = script.replace("${deviceMemory}", str(device['deviceMemory']))
    script = script.replace("${webgl_vendor}", webgl['vendor'])
    script = script.replace("${webgl_renderer}", webgl['renderer'])
    
    return script

async def apply_stealth_to_page(page):
    """
    Apply stealth techniques to a Playwright page
    
    Args:
        page: Playwright page object
    """
    try:
        # Apply stealth script
        stealth_js = get_stealth_js()
        await page.add_init_script(stealth_js)
        
        # Additional anti-automation detection script
        await page.add_init_script("""
        () => {
            // Remove automation flags in JavaScript properties
            const cleanAutomation = () => {
                // Remove automation controller flag
                if (window.navigator && navigator.hasOwnProperty('__webdriver_script_fn')) {
                    delete navigator.__webdriver_script_fn;
                }
                
                // Handle chrome driver detection
                const chromeKeys = Object.keys(window).filter(key => 
                    key.includes('cdc_') || 
                    key.includes('XPathResult') || 
                    key.includes('_chromedriver'));
                
                for (const key of chromeKeys) {
                    try {
                        delete window[key];
                    } catch (e) {}
                }
                
                // Prevent detection via error stack traces
                Error.prototype.toString = new Proxy(Error.prototype.toString, {
                    apply: (target, thisArg, args) => {
                        const result = target.apply(thisArg, args);
                        if (result.includes('playwright') || result.includes('puppeteer')) {
                            return result.replace(/playwright|puppeteer/g, 'mozilla');
                        }
                        return result;
                    }
                });
            };
            
            // Execute immediately and on any page load events
            cleanAutomation();
            document.addEventListener('DOMContentLoaded', cleanAutomation);
            window.addEventListener('load', cleanAutomation);
        }
        """)
        
        # Apply additional protections for WebRTC (IP leakage prevention)
        await page.add_init_script("""
        () => {
            // Disable WebRTC to prevent IP leaks
            if (typeof navigator.mediaDevices !== 'undefined') {
                try {
                    // Override getUserMedia to reject all requests
                    const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
                    navigator.mediaDevices.getUserMedia = function(constraints) {
                        if (constraints.video || constraints.audio) {
                            return Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
                        }
                        return originalGetUserMedia.apply(this, arguments);
                    };
                } catch (e) {}
            }
        }
        """)
        
        logger.info("Applied comprehensive stealth protections to page")
    except Exception as e:
        logger.error(f"Error applying stealth to page: {e}")
        
    return page 