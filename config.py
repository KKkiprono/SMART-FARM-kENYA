import os
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    """Configuration class for the Arduino Sensor Data Processor"""
    
    # Flask Configuration
    FLASK_HOST: str = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT: int = int(os.getenv('FLASK_PORT', '5000'))
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Google Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-pro')
    
    # Temperature Thresholds (°C)
    TEMP_HOT_THRESHOLD: float = float(os.getenv('TEMP_HOT_THRESHOLD', '30.0'))
    TEMP_COLD_THRESHOLD: float = float(os.getenv('TEMP_COLD_THRESHOLD', '15.0'))
    
    # Gas Level Threshold
    GAS_ALERT_THRESHOLD: int = int(os.getenv('GAS_ALERT_THRESHOLD', '300'))
    
    # Light Intensity Thresholds
    LIGHT_BRIGHT_THRESHOLD: int = int(os.getenv('LIGHT_BRIGHT_THRESHOLD', '700'))
    LIGHT_DIM_THRESHOLD: int = int(os.getenv('LIGHT_DIM_THRESHOLD', '200'))
    
    # Humidity Thresholds (%)
    HUMIDITY_HIGH_THRESHOLD: float = float(os.getenv('HUMIDITY_HIGH_THRESHOLD', '70.0'))
    HUMIDITY_LOW_THRESHOLD: float = float(os.getenv('HUMIDITY_LOW_THRESHOLD', '30.0'))
    
    # AI Processing Configuration
    AI_TEMPERATURE: float = float(os.getenv('AI_TEMPERATURE', '0.3'))  # Lower = more deterministic
    MAX_OUTPUT_TOKENS: int = int(os.getenv('MAX_OUTPUT_TOKENS', '256'))
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []
        
        # Check required API key
        if not cls.GEMINI_API_KEY:
            issues.append("GEMINI_API_KEY is required but not set")
        
        # Validate temperature thresholds
        if cls.TEMP_COLD_THRESHOLD >= cls.TEMP_HOT_THRESHOLD:
            issues.append(f"TEMP_COLD_THRESHOLD ({cls.TEMP_COLD_THRESHOLD}) must be less than TEMP_HOT_THRESHOLD ({cls.TEMP_HOT_THRESHOLD})")
        
        # Validate light thresholds
        if cls.LIGHT_DIM_THRESHOLD >= cls.LIGHT_BRIGHT_THRESHOLD:
            issues.append(f"LIGHT_DIM_THRESHOLD ({cls.LIGHT_DIM_THRESHOLD}) must be less than LIGHT_BRIGHT_THRESHOLD ({cls.LIGHT_BRIGHT_THRESHOLD})")
        
        # Validate humidity thresholds
        if cls.HUMIDITY_LOW_THRESHOLD >= cls.HUMIDITY_HIGH_THRESHOLD:
            issues.append(f"HUMIDITY_LOW_THRESHOLD ({cls.HUMIDITY_LOW_THRESHOLD}) must be less than HUMIDITY_HIGH_THRESHOLD ({cls.HUMIDITY_HIGH_THRESHOLD})")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "config": {
                "flask_host": cls.FLASK_HOST,
                "flask_port": cls.FLASK_PORT,
                "debug": cls.DEBUG,
                "gemini_model": cls.GEMINI_MODEL,
                "temp_thresholds": {
                    "hot": cls.TEMP_HOT_THRESHOLD,
                    "cold": cls.TEMP_COLD_THRESHOLD
                },
                "gas_threshold": cls.GAS_ALERT_THRESHOLD,
                "light_thresholds": {
                    "bright": cls.LIGHT_BRIGHT_THRESHOLD,
                    "dim": cls.LIGHT_DIM_THRESHOLD
                },
                "humidity_thresholds": {
                    "high": cls.HUMIDITY_HIGH_THRESHOLD,
                    "low": cls.HUMIDITY_LOW_THRESHOLD
                }
            }
        }
    
    @classmethod
    def get_decision_rules(cls) -> str:
        """Get decision rules as formatted string for AI prompt"""
        return f"""
DECISION RULES:
Temperature Control:
- If temperature >= {cls.TEMP_HOT_THRESHOLD}°C: start fan, turn on red LED (hot condition)
- If {cls.TEMP_COLD_THRESHOLD}°C <= temperature < {cls.TEMP_HOT_THRESHOLD}°C: stop fan, turn on yellow LED (normal condition)
- If temperature < {cls.TEMP_COLD_THRESHOLD}°C: stop fan, turn on blue LED (cold condition)

Gas Safety:
- If gas_level > {cls.GAS_ALERT_THRESHOLD}: trigger gas alert (immediate safety concern)

Additional Context:
- Light intensity range: 0-1023 (0=dark, 1023=very bright)
- Humidity range: 0-100%
- Gas level range: 0-1023 (higher values indicate more gas detected)
- Bright light threshold: {cls.LIGHT_BRIGHT_THRESHOLD}
- Dim light threshold: {cls.LIGHT_DIM_THRESHOLD}
- High humidity threshold: {cls.HUMIDITY_HIGH_THRESHOLD}%
- Low humidity threshold: {cls.HUMIDITY_LOW_THRESHOLD}%
"""