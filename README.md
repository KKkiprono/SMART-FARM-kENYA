# Arduino Sensor Data Processor with Gemini AI + SMS Alerts

A Flask-based server application that receives sensor data from wireless Arduino devices, uses Google Gemini AI to make intelligent control decisions, and sends real-time SMS alerts to farmers via Africa's Talking API.

## 🚀 Features

- **REST API** for receiving Arduino sensor data via HTTP POST
- **Google Gemini AI Integration** for intelligent decision making
- **SMS Alerts via Africa's Talking** for real-time farmer notifications
- **Environmental Control Logic** for temperature, humidity, light, and gas monitoring
- **Intelligent Alert Management** prevents SMS spam with state tracking
- **Farmer-Friendly Messages** with emojis and clear action guidance
- **Comprehensive Logging** of sensor data, AI decisions, and SMS alerts
- **Configurable Thresholds** for all sensor parameters and alert cooldowns
- **Robust Error Handling** with fallback rule-based decisions
- **Health Check Endpoints** for monitoring system status
- **Sandbox/Live Environment** support for development and production

## 📊 Sensor Data Processing

The system processes four types of sensor data:
- **Temperature** (°C) - Controls fan and LED color
- **Humidity** (%) - Additional environmental context
- **Light Intensity** (0-1023) - Ambient light monitoring
- **Gas Level** (0-1023) - Safety gas detection

## 🧠 AI Decision Logic

### Temperature Control Rules:
- `≥ 30°C`: Start fan, turn on red LED (hot)
- `15°C - 30°C`: Stop fan, turn on yellow LED (normal)
- `< 15°C`: Stop fan, turn on blue LED (cold)

### Safety Rules:
- `Gas Level > 300`: Trigger gas alert (critical priority)

All decisions are processed through Google Gemini AI for intelligent reasoning and can fall back to rule-based logic if AI processing fails. Critical alerts automatically trigger SMS notifications to farmers with actionable information.

## 🛠️ Installation & Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd arduino-sensor-processor
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Required: Get your API key from Google AI Studio
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Customize thresholds
TEMP_HOT_THRESHOLD=30.0
TEMP_COLD_THRESHOLD=15.0
GAS_ALERT_THRESHOLD=300

# Flask settings
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
DEBUG=False
```

### 3. Get API Keys

**Google Gemini API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GEMINI_API_KEY`

**Africa's Talking API Key (for SMS):**
1. Sign up at [Africa's Talking](https://africastalking.com/)
2. Go to your dashboard and get your API key
3. For sandbox testing, use username: `sandbox`
4. Add credentials to your `.env` file:
   ```bash
   AT_USERNAME=sandbox
   AT_API_KEY=your_api_key_here
   AT_RECIPIENT_PHONE=+254712345678
   ```

### 4. Run the Server

```bash
python app.py
```

The server will start on `http://localhost:5000` by default.

## 📡 API Documentation

### POST /submit-data

Submit sensor data for AI processing.

**Request Format:**
```json
{
  "temperature": 25.5,
  "humidity": 60.2,
  "light_intensity": 512,
  "gas_level": 150
}
```

**Response Format:**
```json
{
  "status": "success",
  "timestamp": "2024-01-15T10:30:00.123456",
  "sensor_data": {
    "temperature": 25.5,
    "humidity": 60.2,
    "light_intensity": 512,
    "gas_level": 150
  },
  "decision": {
    "action": "stop fan",
    "led": "yellow",
    "fan": "off",
    "gas_alert": false,
    "reasoning": "Temperature is in normal range (15-30°C), no gas alert needed",
    "priority": "low"
  },
  "sms_alert": {
    "success": true,
    "alerts_sent": ["temperature"],
    "count": 1
  }
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "service": "Arduino Sensor Data Processor"
}
```

### POST /sms/test

Send a test SMS message to verify SMS functionality.

**Response:**
```json
{
  "status": "success",
  "message": "Test SMS sent successfully",
  "details": {
    "success": true,
    "message": "🧪 Test message from Arduino Sensor System...",
    "recipient": "+254712345678",
    "cost": "KES 0.8000",
    "message_id": "ATXid_sample123"
  }
}
```

### GET /sms/status

Get SMS service status and configuration.

**Response:**
```json
{
  "sms_service": {
    "sms_enabled": true,
    "sandbox_mode": true,
    "recipient_configured": true,
    "sender_id": "FARMIOT",
    "gas_alert_cooldown": "300 seconds"
  }
}
```

### GET /

API information and documentation.

## 🧪 Testing

### Automated Testing

Run the comprehensive test suite:

```bash
python test_requests.py
```

This will test:
- ✅ Health check endpoint
- ✅ All sensor data scenarios (normal, hot, cold, gas alert, extreme)
- ✅ SMS service status and configuration
- ✅ Error handling for invalid data
- ✅ Response format validation

**Note:** To test actual SMS sending, uncomment the test SMS section in `test_requests.py` and ensure you have valid Africa's Talking credentials.

### Manual Testing with curl

**Normal conditions:**
```bash
curl -X POST http://localhost:5000/submit-data \
  -H 'Content-Type: application/json' \
  -d '{"temperature": 22.5, "humidity": 45.0, "light_intensity": 400, "gas_level": 120}'
```

**Hot conditions (should trigger fan):**
```bash
curl -X POST http://localhost:5000/submit-data \
  -H 'Content-Type: application/json' \
  -d '{"temperature": 32.1, "humidity": 65.2, "light_intensity": 800, "gas_level": 180}'
```

**Gas alert conditions:**
```bash
curl -X POST http://localhost:5000/submit-data \
  -H 'Content-Type: application/json' \
  -d '{"temperature": 25.0, "humidity": 55.0, "light_intensity": 600, "gas_level": 450}'
```

**Test SMS functionality:**
```bash
# Check SMS status
curl -X GET http://localhost:5000/sms/status

# Send test SMS (requires valid credentials)
curl -X POST http://localhost:5000/sms/test
```

### Testing with Postman

1. Import the sample payloads from `sample_arduino_payload.json`
2. Set up POST requests to `http://localhost:5000/submit-data`
3. Use the provided test scenarios for comprehensive testing
4. Test SMS endpoints at `/sms/status` and `/sms/test`

## 📱 SMS Alert System

### Farmer-Friendly Messages

The system sends intelligent SMS alerts using Africa's Talking API with:

- **🌡️ Temperature Alerts**: "HIGH TEMP ALERT: 32.1°C detected! Fan turned ON automatically. Red warning light activated. Please check your crops immediately."
- **🚨 Gas Alerts**: "GAS ALERT! Dangerous gas levels detected (450/1023). IMMEDIATE ACTION REQUIRED! Check for gas leaks, ensure ventilation, and evacuate if necessary."
- **✅ Status Updates**: "TEMP NORMALIZED: 25.0°C. Fan turned OFF automatically. Yellow indicator shows normal conditions."
- **❄️ Cold Warnings**: "LOW TEMP ALERT: 12.3°C detected! Fan turned OFF. Blue indicator active. Consider protective measures for your crops."

### Smart Alert Management

- **State Tracking**: Prevents SMS spam by only sending alerts when conditions actually change
- **Gas Alert Cooldown**: Critical gas alerts limited to once every 5 minutes
- **Priority Escalation**: Alerts sent when conditions escalate to high/critical priority
- **Persistent State**: System remembers previous states across restarts

### Sample SMS Messages

See `sample_sms_messages.json` for complete examples of all alert types and scenarios.

## 🔧 Arduino Integration

### Expected Arduino Setup

Your Arduino should send HTTP POST requests with JSON payloads. Example Arduino code structure:

```cpp
// WiFi and HTTP libraries
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Sensor readings
float temperature = dht.readTemperature();
float humidity = dht.readHumidity();
int lightIntensity = analogRead(LIGHT_SENSOR_PIN);
int gasLevel = analogRead(GAS_SENSOR_PIN);

// Create JSON payload
StaticJsonDocument<200> doc;
doc["temperature"] = temperature;
doc["humidity"] = humidity;
doc["light_intensity"] = lightIntensity;
doc["gas_level"] = gasLevel;

String jsonString;
serializeJson(doc, jsonString);

// Send POST request
HTTPClient http;
http.begin("http://your-server:5000/submit-data");
http.addHeader("Content-Type", "application/json");
int httpResponseCode = http.POST(jsonString);
```

### Wireless Options

- **ESP8266/ESP32**: Built-in WiFi capability
- **Arduino + WiFi Shield**: Using WiFi expansion boards
- **Arduino + ESP8266**: Using ESP8266 as WiFi module
- **LoRa/LoRaWAN**: For long-range wireless communication

## 📁 Project Structure

```
arduino-sensor-processor/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── gemini_utils.py             # Gemini AI integration
├── sms_utils.py               # Africa's Talking SMS integration
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── sample_arduino_payload.json # Sample test data
├── sample_sms_messages.json   # Example SMS messages farmers receive
├── test_requests.py           # Automated test suite
├── README.md                  # This file
├── sensor_data.log           # Application logs (created at runtime)
└── sms_state.json            # SMS state tracking (created at runtime)
```

## 🔍 Logging

The application logs all activities to both console and `sensor_data.log`:

- Received sensor data with timestamps
- AI processing decisions and reasoning
- SMS alerts sent and delivery status
- Error conditions and fallback actions
- API request/response information
- State changes and cooldown periods

## ⚙️ Configuration Options

All settings can be customized via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | - | **Required** Google Gemini API key |
| `GEMINI_MODEL` | `gemini-pro` | Gemini model to use |
| `FLASK_HOST` | `0.0.0.0` | Flask server host |
| `FLASK_PORT` | `5000` | Flask server port |
| `TEMP_HOT_THRESHOLD` | `30.0` | Temperature for hot conditions (°C) |
| `TEMP_COLD_THRESHOLD` | `15.0` | Temperature for cold conditions (°C) |
| `GAS_ALERT_THRESHOLD` | `300` | Gas level for alerts (0-1023) |
| `HUMIDITY_HIGH_THRESHOLD` | `70.0` | High humidity threshold (%) |
| `HUMIDITY_LOW_THRESHOLD` | `30.0` | Low humidity threshold (%) |
| `LIGHT_BRIGHT_THRESHOLD` | `700` | Bright light threshold (0-1023) |
| `LIGHT_DIM_THRESHOLD` | `200` | Dim light threshold (0-1023) |
| `AT_USERNAME` | - | **Required** Africa's Talking username |
| `AT_API_KEY` | - | **Required** Africa's Talking API key |
| `AT_SENDER_ID` | - | Optional sender ID/shortcode |
| `AT_RECIPIENT_PHONE` | - | **Required** Farmer's phone number (+254...) |
| `AT_SANDBOX` | `True` | Use sandbox (True) or live (False) environment |
| `GAS_ALERT_COOLDOWN` | `300` | Minimum seconds between gas alerts |
| `SMS_ENABLED` | `True` | Enable/disable SMS functionality |

## 🚨 Error Handling

The system includes comprehensive error handling:

- **Invalid JSON**: Returns 400 with error message
- **Missing fields**: Validates required sensor data fields
- **Out-of-range values**: Validates sensor data ranges
- **AI processing failure**: Falls back to rule-based decisions
- **SMS delivery failure**: Logs errors and continues operation
- **Network issues**: Proper timeout and retry handling
- **Invalid phone numbers**: Validates format and provides clear errors

## 🔒 Security Considerations

- Keep your `GEMINI_API_KEY` and `AT_API_KEY` secure and never commit to version control
- Use environment variables for all sensitive configuration
- Consider implementing authentication for production deployments
- Monitor API usage to prevent abuse
- Use sandbox environment for testing to avoid SMS charges
- Validate phone numbers to prevent SMS to invalid recipients

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Troubleshooting

### Common Issues

**"GEMINI_API_KEY is required but not set"**
- Ensure you've set the API key in your `.env` file
- Verify the `.env` file is in the same directory as `app.py`

**"AT_API_KEY is required when SMS is enabled"**
- Sign up for Africa's Talking account
- Get your API key from the dashboard
- Add it to your `.env` file as `AT_API_KEY`
- Set `AT_USERNAME=sandbox` for testing

**"AI processing failed"**
- Check your internet connection
- Verify your Gemini API key is valid
- Check the logs for detailed error messages
- The system will fall back to rule-based decisions

**"SMS service not enabled"**
- Check that `SMS_ENABLED=True` in your `.env` file
- Verify all Africa's Talking credentials are set
- Check SMS service status at `/sms/status` endpoint

**Connection refused errors**
- Ensure the Flask server is running
- Check that the port (default 5000) is not blocked
- Verify the server host configuration

### Getting Help

- Check the application logs in `sensor_data.log`
- Run the test suite to verify functionality
- Review the API documentation above
- Check Google Gemini API status and quotas
- Verify Africa's Talking account balance and SMS credits
- Test SMS functionality with `/sms/test` endpoint