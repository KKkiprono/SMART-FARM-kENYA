import google.generativeai as genai
import json
import logging
from typing import Dict, Any, Optional
from config import Config # Assuming you need to import something from sms_utils.py

logger = logging.getLogger(__name__)

class GeminiProcessor:
    """Google Gemini AI processor for Arduino sensor data analysis"""
    
    def __init__(self):
        """Initialize the Gemini processor with API configuration"""
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required but not set in configuration")
        
        # Configure Gemini API
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Initialize the model
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
        # Generation configuration
        self.generation_config = genai.types.GenerationConfig(
            temperature=Config.AI_TEMPERATURE,
            max_output_tokens=Config.MAX_OUTPUT_TOKENS,
        )
        
        logger.info(f"Initialized Gemini processor with model: {Config.GEMINI_MODEL}")
        print("GEMINI_API_KEY from Config:", Config.GEMINI_API_KEY)
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for sensor data analysis"""
        return f"""You are an intelligent IoT sensor data processor for an Arduino-based environmental monitoring system. 
Your role is to analyze sensor readings and make precise control decisions based on predefined rules.

{Config.get_decision_rules()}

RESPONSE FORMAT:
You must respond with a valid JSON object containing exactly these fields:
{{
    "action": "string describing the main action (e.g., 'start fan', 'stop fan', 'trigger gas alert')",
    "led": "string describing LED color ('red', 'yellow', 'blue', or 'off')",
    "fan": "string describing fan state ('on' or 'off')",
    "gas_alert": "boolean indicating if gas alert should be triggered",
    "reasoning": "string explaining the decision logic",
    "priority": "string indicating urgency level ('low', 'medium', 'high', 'critical')"
}}

IMPORTANT RULES:
1. Always follow the temperature thresholds exactly as specified
2. Gas alerts take priority over temperature control
3. Provide clear reasoning for each decision
4. Respond only with valid JSON - no additional text
5. Consider all sensor readings in your analysis
6. Set priority based on safety concerns (gas alerts = critical, temperature extremes = high, normal conditions = low)
"""
    
    def _create_user_prompt(self, sensor_data: Dict[str, Any]) -> str:
        """Create the user prompt with current sensor data"""
        return f"""Analyze the following sensor readings and provide control decisions:

CURRENT SENSOR DATA:
- Temperature: {sensor_data['temperature']}°C
- Humidity: {sensor_data['humidity']}%
- Light Intensity: {sensor_data['light_intensity']} (0-1023 scale)
- Gas Level: {sensor_data['gas_level']} (0-1023 scale)
- Timestamp: {sensor_data['timestamp']}

Based on these readings and the predefined rules, determine the appropriate actions for:
1. Fan control (on/off)
2. LED color indication
3. Gas alert status
4. Overall system priority level

Provide your response as a JSON object following the specified format."""
    
    def process_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sensor data using Gemini AI and return control decisions
        
        Args:
            sensor_data: Dictionary containing sensor readings
            
        Returns:
            Dictionary containing AI-generated control decisions
        """
        try:
            # Create prompts
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(sensor_data)
            
            # Combine prompts for the model
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            logger.info("Sending sensor data to Gemini AI for processing")
            
            # Generate response from Gemini
            response = self.model.generate_content(
                full_prompt,
                generation_config=self.generation_config
            )
            
            # Extract and parse the response
            response_text = response.text.strip()
            logger.info(f"Received Gemini response: {response_text}")
            
            # Parse JSON response
            try:
                ai_decision = json.loads(response_text)
                
                # Validate required fields
                required_fields = ['action', 'led', 'fan', 'gas_alert', 'reasoning', 'priority']
                missing_fields = [field for field in required_fields if field not in ai_decision]
                
                if missing_fields:
                    logger.warning(f"AI response missing fields: {missing_fields}")
                    # Fallback to rule-based decision
                    return self._fallback_decision(sensor_data)
                
                # Validate field values
                if ai_decision['led'] not in ['red', 'yellow', 'blue', 'off']:
                    logger.warning(f"Invalid LED color: {ai_decision['led']}")
                    ai_decision['led'] = self._get_led_color_by_temp(sensor_data['temperature'])
                
                if ai_decision['fan'] not in ['on', 'off']:
                    logger.warning(f"Invalid fan state: {ai_decision['fan']}")
                    ai_decision['fan'] = 'on' if sensor_data['temperature'] >= Config.TEMP_HOT_THRESHOLD else 'off'
                
                if not isinstance(ai_decision['gas_alert'], bool):
                    logger.warning(f"Invalid gas_alert type: {type(ai_decision['gas_alert'])}")
                    ai_decision['gas_alert'] = sensor_data['gas_level'] > Config.GAS_ALERT_THRESHOLD
                
                if ai_decision['priority'] not in ['low', 'medium', 'high', 'critical']:
                    logger.warning(f"Invalid priority: {ai_decision['priority']}")
                    ai_decision['priority'] = self._get_priority(sensor_data)
                
                return ai_decision
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"Raw response: {response_text}")
                return self._fallback_decision(sensor_data)
                
        except Exception as e:
            logger.error(f"Error in Gemini AI processing: {str(e)}")
            return self._fallback_decision(sensor_data)
    
    def _fallback_decision(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback rule-based decision making when AI processing fails
        
        Args:
            sensor_data: Dictionary containing sensor readings
            
        Returns:
            Dictionary containing rule-based control decisions
        """
        logger.info("Using fallback rule-based decision making")
        
        temperature = sensor_data['temperature']
        gas_level = sensor_data['gas_level']
        
        # Determine fan and LED based on temperature
        if temperature >= Config.TEMP_HOT_THRESHOLD:
            action = "start fan"
            led = "red"
            fan = "on"
        elif temperature < Config.TEMP_COLD_THRESHOLD:
            action = "stop fan"
            led = "blue"
            fan = "off"
        else:
            action = "stop fan"
            led = "yellow"
            fan = "off"
        
        # Check gas alert
        gas_alert = gas_level > Config.GAS_ALERT_THRESHOLD
        if gas_alert:
            action = "trigger gas alert"
            
        # Determine priority
        priority = self._get_priority(sensor_data)
        
        return {
            "action": action,
            "led": led,
            "fan": fan,
            "gas_alert": gas_alert,
            "reasoning": f"Fallback rule-based decision: temp={temperature}°C, gas={gas_level}",
            "priority": priority
        }
    
    def _get_led_color_by_temp(self, temperature: float) -> str:
        """Get LED color based on temperature thresholds"""
        if temperature >= Config.TEMP_HOT_THRESHOLD:
            return "red"
        elif temperature < Config.TEMP_COLD_THRESHOLD:
            return "blue"
        else:
            return "yellow"
    
    def _get_priority(self, sensor_data: Dict[str, Any]) -> str:
        """Determine priority level based on sensor readings"""
        if sensor_data['gas_level'] > Config.GAS_ALERT_THRESHOLD:
            return "critical"
        elif (sensor_data['temperature'] >= Config.TEMP_HOT_THRESHOLD or 
              sensor_data['temperature'] < Config.TEMP_COLD_THRESHOLD):
            return "high"
        elif (sensor_data['humidity'] > Config.HUMIDITY_HIGH_THRESHOLD or 
              sensor_data['humidity'] < Config.HUMIDITY_LOW_THRESHOLD):
            return "medium"
        else:
            return "low"
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the Gemini API connection"""
        try:
            test_prompt = "Respond with a JSON object: {\"status\": \"connected\", \"model\": \"" + Config.GEMINI_MODEL + "\"}"
            response = self.model.generate_content(test_prompt)
            
            return {
                "success": True,
                "response": response.text.strip(),
                "model": Config.GEMINI_MODEL
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": Config.GEMINI_MODEL
            }