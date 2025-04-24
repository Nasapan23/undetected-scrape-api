"""
Fingerprint evasion techniques to prevent browser fingerprinting.
"""
import random
import string
from typing import Dict, Any, List, Optional
from loguru import logger

# JavaScript functions to modify browser attributes and prevent fingerprinting
FP_EVASION_SCRIPTS = {
    # Modify canvas fingerprinting by adding minimal noise
    "canvas_defender": """
    (function() {
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function(x, y, width, height) {
            const imageData = originalGetImageData.call(this, x, y, width, height);
            const pixels = imageData.data;
            
            // Apply very subtle noise to avoid detection but maintain visual integrity
            for (let i = 0; i < pixels.length; i += 4) {
                // Only modify a small percentage of pixels
                if (Math.random() < 0.02) {
                    // Add minor noise (-1, 0, or 1) to RGB values
                    pixels[i] = Math.max(0, Math.min(255, pixels[i] + (Math.random() > 0.5 ? 1 : -1)));
                    pixels[i+1] = Math.max(0, Math.min(255, pixels[i+1] + (Math.random() > 0.5 ? 1 : -1)));
                    pixels[i+2] = Math.max(0, Math.min(255, pixels[i+2] + (Math.random() > 0.5 ? 1 : -1)));
                    // Alpha remains unchanged
                }
            }
            
            return imageData;
        };
        
        // Modify toDataURL to add similar noise
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function() {
            // Small chance to leave original behavior, making detection harder
            if (Math.random() < 0.05) {
                return originalToDataURL.apply(this, arguments);
            }
            
            // Draw a transparent pixel with minor opacity
            const ctx = this.getContext('2d');
            const minimalAlpha = 0.005;  // Nearly invisible
            const originalFillStyle = ctx.fillStyle;
            ctx.fillStyle = `rgba(${Math.floor(Math.random()*255)}, ${Math.floor(Math.random()*255)}, ${Math.floor(Math.random()*255)}, ${minimalAlpha})`;
            ctx.fillRect(
                Math.floor(Math.random() * this.width), 
                Math.floor(Math.random() * this.height), 
                1, 1
            );
            ctx.fillStyle = originalFillStyle;
            
            return originalToDataURL.apply(this, arguments);
        };
    })();
    """,
    
    # Modify audio fingerprinting
    "audio_defender": """
    (function() {
        // Override AudioBuffer methods
        const originalGetChannelData = AudioBuffer.prototype.getChannelData;
        AudioBuffer.prototype.getChannelData = function(channel) {
            const data = originalGetChannelData.call(this, channel);
            
            // Only modify audio data occasionally to minimize impact on functionality
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
        
        // Override AnalyserNode methods if they exist
        if (typeof AnalyserNode !== 'undefined') {
            const originalGetFloatFrequencyData = AnalyserNode.prototype.getFloatFrequencyData;
            if (originalGetFloatFrequencyData) {
                AnalyserNode.prototype.getFloatFrequencyData = function(array) {
                    originalGetFloatFrequencyData.call(this, array);
                    
                    // Add minimal noise
                    for (let i = 0; i < array.length; i++) {
                        if (Math.random() < 0.05) {
                            array[i] += (Math.random() * 0.1 - 0.05);
                        }
                    }
                };
            }
        }
    })();
    """,
    
    # Font fingerprinting protection
    "font_defender": """
    (function() {
        // Store the original function
        const originalMeasureText = CanvasRenderingContext2D.prototype.measureText;
        
        // Override measureText to introduce minor variations
        CanvasRenderingContext2D.prototype.measureText = function(text) {
            const result = originalMeasureText.call(this, text);
            
            // Add a small amount of noise to the width
            const originalWidth = result.width;
            Object.defineProperty(result, 'width', {
                get: function() {
                    // Add very small random variation
                    return originalWidth + (Math.random() * 0.02 - 0.01) * originalWidth;
                }
            });
            
            return result;
        };
        
        // Override font enumeration if possible
        if (typeof window.queryLocalFonts === 'function') {
            const originalQueryLocalFonts = window.queryLocalFonts;
            window.queryLocalFonts = async function() {
                try {
                    const fonts = await originalQueryLocalFonts.apply(this, arguments);
                    
                    // Randomize order slightly and limit results
                    return fonts
                        .sort(() => Math.random() > 0.7 ? 1 : -1)
                        .slice(0, Math.floor(fonts.length * 0.9));
                } catch (e) {
                    return [];
                }
            };
        }
    })();
    """,
    
    # WebGL fingerprinting protection
    "webgl_defender": """
    (function() {
        // Additional WebGL modifications beyond the basic vendor/renderer changes
        
        const addNoise = (value, noise) => {
            if (typeof value === 'number') {
                return value + (Math.random() * 2 - 1) * noise;
            }
            return value;
        };
        
        // Override WebGL parameters that are commonly used for fingerprinting
        const createGetParameterProxy = (target) => {
            const original = target.getParameter;
            
            return function(parameter) {
                const result = original.call(this, parameter);
                
                // Add noise to MAX_VIEWPORT_DIMS
                if (parameter === this.MAX_VIEWPORT_DIMS) {
                    const dims = [...result];
                    // Tiny variations won't affect functionality
                    return [
                        Math.floor(dims[0] + (Math.random() < 0.5 ? 0 : 1)),
                        Math.floor(dims[1] + (Math.random() < 0.5 ? 0 : 1))
                    ];
                }
                
                // Add noise to floating point precision values
                if (parameter === this.ALIASED_LINE_WIDTH_RANGE ||
                    parameter === this.ALIASED_POINT_SIZE_RANGE ||
                    parameter === this.MAX_TEXTURE_MAX_ANISOTROPY_EXT) {
                    if (Array.isArray(result)) {
                        return result.map(v => addNoise(v, 0.01));
                    }
                    return addNoise(result, 0.01);
                }
                
                return result;
            };
        };
        
        // Apply to both WebGL contexts
        if (typeof WebGLRenderingContext !== 'undefined') {
            WebGLRenderingContext.prototype.getParameter = 
                createGetParameterProxy(WebGLRenderingContext.prototype);
        }
        
        if (typeof WebGL2RenderingContext !== 'undefined') {
            WebGL2RenderingContext.prototype.getParameter = 
                createGetParameterProxy(WebGL2RenderingContext.prototype);
        }
    })();
    """,
    
    # Battery API protection
    "battery_defender": """
    (function() {
        if (navigator.getBattery) {
            const originalGetBattery = navigator.getBattery;
            navigator.getBattery = function() {
                return originalGetBattery.call(this).then(battery => {
                    // Create a proxy that slightly modifies battery values
                    const originalLevel = battery.level;
                    const originalCharging = battery.charging;
                    const originalChargingTime = battery.chargingTime;
                    const originalDischargingTime = battery.dischargingTime;
                    
                    // Override properties with getters that add minor variations
                    Object.defineProperties(battery, {
                        'level': {
                            get: function() {
                                // Add small random variation to level
                                return Math.min(1, Math.max(0, originalLevel + (Math.random() * 0.02 - 0.01)));
                            }
                        },
                        'charging': {
                            get: function() {
                                // Small chance to flip charging state
                                return Math.random() < 0.05 ? !originalCharging : originalCharging;
                            }
                        },
                        'chargingTime': {
                            get: function() {
                                // Add noise to charging time
                                if (originalChargingTime === Infinity) return Infinity;
                                return originalChargingTime + Math.floor(Math.random() * 60);
                            }
                        },
                        'dischargingTime': {
                            get: function() {
                                // Add noise to discharging time
                                if (originalDischargingTime === Infinity) return Infinity;
                                return originalDischargingTime + Math.floor(Math.random() * 60);
                            }
                        }
                    });
                    
                    return battery;
                });
            };
        }
    })();
    """,
    
    # Hardware concurrency and device memory consistency
    "hardware_defender": """
    (function() {
        // This ensures consistent values for hardware concurrency and memory
        // throughout a session, avoiding detection of script modifications
        
        // Store initial values in session storage for consistency
        if (!sessionStorage.getItem('hwConcurrency')) {
            const hwConcurrency = navigator.hardwareConcurrency;
            sessionStorage.setItem('hwConcurrency', hwConcurrency);
        }
        
        if (!sessionStorage.getItem('deviceMemory') && 'deviceMemory' in navigator) {
            const deviceMemory = navigator.deviceMemory;
            sessionStorage.setItem('deviceMemory', deviceMemory);
        }
        
        // Apply slight modification to hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: function() {
                const baseValue = parseInt(sessionStorage.getItem('hwConcurrency')) || 4;
                return Math.max(2, baseValue + (Math.random() < 0.5 ? -1 : 0));
            }
        });
        
        // Apply slight modification to deviceMemory if it exists
        if ('deviceMemory' in navigator) {
            Object.defineProperty(navigator, 'deviceMemory', {
                get: function() {
                    const baseValue = parseFloat(sessionStorage.getItem('deviceMemory')) || 4;
                    const possibleValues = [2, 4, 8];
                    return possibleValues.find(v => v >= baseValue) || 4;
                }
            });
        }
    })();
    """
}

async def apply_fingerprint_evasion(page, evasion_types=None):
    """
    Apply fingerprint evasion scripts to prevent browser fingerprinting.
    
    Args:
        page: Playwright page object
        evasion_types: List of evasion types to apply. If None, all are applied.
                      Options: 'canvas', 'audio', 'font', 'webgl', 'battery', 'hardware'
    """
    try:
        if evasion_types is None:
            evasion_types = ['canvas', 'audio', 'font', 'webgl', 'battery', 'hardware']
        
        script_mapping = {
            'canvas': 'canvas_defender',
            'audio': 'audio_defender',
            'font': 'font_defender',
            'webgl': 'webgl_defender',
            'battery': 'battery_defender',
            'hardware': 'hardware_defender'
        }
        
        # Apply selected evasion scripts
        for evasion_type in evasion_types:
            script_key = script_mapping.get(evasion_type)
            if script_key and script_key in FP_EVASION_SCRIPTS:
                await page.add_init_script(FP_EVASION_SCRIPTS[script_key])
                logger.debug(f"Applied {evasion_type} fingerprint evasion")
        
        logger.info(f"Successfully applied fingerprint evasion techniques: {', '.join(evasion_types)}")
    except Exception as e:
        logger.error(f"Error applying fingerprint evasion scripts: {e}")

def generate_consistent_fingerprint(seed=None):
    """
    Generate consistent fingerprint values to use across sessions.
    
    Args:
        seed: Optional seed to ensure reproducibility
    
    Returns:
        Dict with consistent fingerprint values
    """
    if seed:
        random.seed(seed)
    
    # Generate a random identifier to be consistent within a session
    session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    # Common GPU vendor/renderer combinations
    gpu_combos = [
        ("Google Inc.", "ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc.", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc.", "ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc.", "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)"),
        ("Apple", "Apple M1"),
        ("Apple", "Apple M2"),
        ("Intel Inc.", "Intel Iris OpenGL Engine"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 980/PCIe/SSE2"),
    ]
    
    chosen_gpu = random.choice(gpu_combos)
    
    # Build the consistent fingerprint
    fingerprint = {
        "session_id": session_id,
        "user_agent_components": {
            "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
            "browser_version": f"{random.randint(100, 120)}.0.{random.randint(0, 9999)}.{random.randint(0, 99)}",
            "platform": random.choice(["Windows", "MacOS", "Linux"]),
            "platform_version": random.choice(["10.0", "11.0", "12.0", "10.15.7", "5.15.0"])
        },
        "hardware": {
            "device_memory": random.choice([2, 4, 8, 16]),
            "hardware_concurrency": random.randint(4, 16),
            "max_touch_points": random.choice([0, 0, 0, 0, 5, 10]),  # Mostly non-touch
            "screen_resolution": random.choice([
                [1920, 1080], [2560, 1440], [1366, 768], [1440, 900], [1536, 864]
            ]),
            "color_depth": random.choice([24, 30, 32, 48]),
            "pixel_ratio": random.choice([1, 1.25, 1.5, 2])
        },
        "browser_features": {
            "cookies_enabled": True,
            "local_storage_available": True,
            "session_storage_available": True,
            "indexed_db_available": True,
        },
        "webgl": {
            "vendor": chosen_gpu[0],
            "renderer": chosen_gpu[1],
            "unmasked_vendor": chosen_gpu[0],
            "unmasked_renderer": chosen_gpu[1],
        },
        "audio": {
            "audio_context_available": True,
            "oscillator_available": True,
            "worklet_available": random.choice([True, False]),
        },
        "fonts": {
            "count": random.randint(30, 200),
            "common_fonts_available": random.random() > 0.1,  # Usually true
        }
    }
    
    # Reset random seed if it was set
    if seed:
        random.seed(None)
        
    return fingerprint

async def apply_consistent_fingerprint(page, fingerprint=None):
    """
    Apply a consistent fingerprint to a Playwright page.
    
    Args:
        page: Playwright page object
        fingerprint: Optional pre-generated fingerprint. If None, a new one is generated.
    
    Returns:
        The fingerprint that was applied
    """
    try:
        if fingerprint is None:
            fingerprint = generate_consistent_fingerprint()
        
        # Apply the fingerprint values via JavaScript
        await page.add_init_script("""
        window.fingerprint = arguments[0];
        
        // Apply WebGL vendor/renderer
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // WebGL vendor (37445) and renderer (37446)
            if (parameter === 37445) {
                return window.fingerprint.webgl.vendor;
            }
            if (parameter === 37446) {
                return window.fingerprint.webgl.renderer;
            }
            
            // Unmasked vendor (37446) and renderer (37447) in WebGL extensions
            if (parameter === 37446) {
                return window.fingerprint.webgl.unmasked_vendor;
            }
            if (parameter === 37447) {
                return window.fingerprint.webgl.unmasked_renderer;
            }
            
            return originalGetParameter.apply(this, arguments);
        };
        
        // Apply hardware concurrency and device memory
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => window.fingerprint.hardware.hardware_concurrency
        });
        
        if ('deviceMemory' in navigator) {
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => window.fingerprint.hardware.device_memory
            });
        }
        
        // Apply screen properties
        Object.defineProperty(screen, 'width', {
            get: () => window.fingerprint.hardware.screen_resolution[0]
        });
        Object.defineProperty(screen, 'height', {
            get: () => window.fingerprint.hardware.screen_resolution[1]
        });
        Object.defineProperty(screen, 'colorDepth', {
            get: () => window.fingerprint.hardware.color_depth
        });
        Object.defineProperty(screen, 'pixelDepth', {
            get: () => window.fingerprint.hardware.color_depth
        });
        Object.defineProperty(window, 'devicePixelRatio', {
            get: () => window.fingerprint.hardware.pixel_ratio
        });
        """, fingerprint)
        
        logger.info("Successfully applied consistent fingerprint")
        return fingerprint
    except Exception as e:
        logger.error(f"Error applying consistent fingerprint: {e}")
        return None 