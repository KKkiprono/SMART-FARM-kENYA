from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify
import logging
from datetime import datetime
import json
from config import Config
from gemini_utils import GeminiProcessor
from sms_utils import SMSManager
import os

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sensor_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Gemini processor and SMS manager
gemini_processor = GeminiProcessor()
sms_manager = SMSManager()

@app.route('/submit-data', methods=['POST'])
def submit_data():
    """
    Endpoint to receive sensor data from Arduino and process it using Gemini AI
    
    Expected JSON format:
    {
        "temperature": 25.5,
        "humidity": 60.2,
        "light_intensity": 512,
        "gas_level": 150
    }
    """
    try:
        # Validate request content type
        if not request.is_json:
            logger.warning("Received non-JSON request")
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        # Get sensor data from request
        sensor_data = request.get_json()
        
        # Validate required fields
        required_fields = ['temperature', 'humidity', 'light_intensity', 'gas_level']
        missing_fields = [field for field in required_fields if field not in sensor_data]
        
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return jsonify({"error": f"Missing required fields: {missing_fields}"}), 400
        
        # Validate data types and ranges
        try:
            temperature = float(sensor_data['temperature'])
            humidity = float(sensor_data['humidity'])
            light_intensity = int(sensor_data['light_intensity'])
            gas_level = int(sensor_data['gas_level'])
            
            # Basic range validation
            if not (0 <= humidity <= 100):
                raise ValueError("Humidity must be between 0-100%")
            if not (0 <= light_intensity <= 1023):
                raise ValueError("Light intensity must be between 0-1023")
            if not (0 <= gas_level <= 1023):
                raise ValueError("Gas level must be between 0-1023")
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid sensor data format: {e}")
            return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
        
        # Log received sensor data
        logger.info(f"Received sensor data - Temp: {temperature}°C, Humidity: {humidity}%, "
                   f"Light: {light_intensity}, Gas: {gas_level}")
        
        # Process data with Gemini AI
        try:
            ai_decision = gemini_processor.process_sensor_data({
                'temperature': temperature,
                'humidity': humidity,
                'light_intensity': light_intensity,
                'gas_level': gas_level,
                'timestamp': datetime.now().isoformat()
            })
            
            # Log AI decision
            logger.info(f"AI Decision: {ai_decision}")
            
            # Send SMS alerts based on AI decision
            sms_result = {"success": False, "reason": "SMS disabled"}
            if Config.SMS_ENABLED:
                try:
                    sms_result = sms_manager.send_farmer_alert(ai_decision, {
                        'temperature': temperature,
                        'humidity': humidity,
                        'light_intensity': light_intensity,
                        'gas_level': gas_level
                    })
                    logger.info(f"SMS Alert Result: {sms_result}")
                except Exception as e:
                    logger.error(f"SMS alert failed: {e}")
                    sms_result = {"success": False, "error": str(e)}
            
            # Return the decision
            return jsonify({
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "sensor_data": {
                    "temperature": temperature,
                    "humidity": humidity,
                    "light_intensity": light_intensity,
                    "gas_level": gas_level
                },
                "decision": ai_decision,
                "sms_alert": sms_result
            }), 200
            
        except Exception as e:
            logger.error(f"Error processing with Gemini AI: {str(e)}")
            return jsonify({"error": "AI processing failed", "details": str(e)}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in submit_data: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Arduino Sensor Data Processor"
    }), 200

@app.route('/sms/test', methods=['POST'])
def send_test_sms():
    """Send a test SMS message"""
    try:
        if not Config.SMS_ENABLED:
            return jsonify({"error": "SMS service is disabled"}), 400
        
        result = sms_manager.send_test_message()
        
        if result['success']:
            return jsonify({
                "status": "success",
                "message": "Test SMS sent successfully",
                "details": result
            }), 200
        else:
            return jsonify({
                "status": "failed",
                "error": result.get('error', 'Unknown error'),
                "details": result
            }), 500
            
    except Exception as e:
        logger.error(f"Test SMS endpoint error: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/sms/status', methods=['GET'])
def sms_status():
    """Get SMS service status"""
    try:
        status = sms_manager.get_status()
        return jsonify({
            "sms_service": status,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"SMS status endpoint error: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API information"""
    return jsonify({
        "service": "Arduino Sensor Data Processor with SMS Alerts",
        "version": "2.0.0",
        "endpoints": {
            "/submit-data": "POST - Submit sensor data for AI processing",
            "/health": "GET - Health check",
            "/sms/test": "POST - Send test SMS message",
            "/sms/status": "GET - Get SMS service status",
            "/": "GET - API information"
        },
        "expected_data_format": {
            "temperature": "float (°C)",
            "humidity": "float (0-100%)",
            "light_intensity": "int (0-1023)",
            "gas_level": "int (0-1023)"
        },
        "sms_features": {
            "enabled": Config.SMS_ENABLED,
            "sandbox_mode": Config.AT_SANDBOX,
            "alerts": ["temperature_changes", "gas_alerts", "priority_escalation"]
        }
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("Starting Arduino Sensor Data Processor Flask App")
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.DEBUG
    )