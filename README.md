# Arduino Sensor Data Processor with Gemini AI

A Flask-based server application that receives sensor data from wireless Arduino devices and uses Google Gemini AI to make intelligent control decisions for environmental monitoring and automation.

## 🚀 Features

- **REST API** for receiving Arduino sensor data via HTTP POST
- **Google Gemini AI Integration** for intelligent decision making
- **Environmental Control Logic** for temperature, humidity, light, and gas monitoring
- **Comprehensive Logging** of sensor data and AI decisions
- **Configurable Thresholds** for all sensor parameters
- **Robust Error Handling** with fallback rule-based decisions
- **Health Check Endpoints** for monitoring system status

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

All decisions are processed through Google Gemini AI for intelligent reasoning and can fall back to rule-based logic if AI processing fails.

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

### 3. Get Google Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GEMINI_API_KEY`

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
- ✅ Error handling for invalid data
- ✅ Response format validation

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

### Testing with Postman

1. Import the sample payloads from `sample_arduino_payload.json`
2. Set up POST requests to `http://localhost:5000/submit-data`
3. Use the provided test scenarios for comprehensive testing

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
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── sample_arduino_payload.json # Sample test data
├── test_requests.py           # Automated test suite
├── README.md                  # This file
└── sensor_data.log           # Application logs (created at runtime)
```

## 🔍 Logging

The application logs all activities to both console and `sensor_data.log`:

- Received sensor data with timestamps
- AI processing decisions and reasoning
- Error conditions and fallback actions
- API request/response information

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

## 🚨 Error Handling

The system includes comprehensive error handling:

- **Invalid JSON**: Returns 400 with error message
- **Missing fields**: Validates required sensor data fields
- **Out-of-range values**: Validates sensor data ranges
- **AI processing failure**: Falls back to rule-based decisions
- **Network issues**: Proper timeout and retry handling

## 🔒 Security Considerations

- Keep your `GEMINI_API_KEY` secure and never commit it to version control
- Use environment variables for all sensitive configuration
- Consider implementing authentication for production deployments
- Monitor API usage to prevent abuse

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

**"AI processing failed"**
- Check your internet connection
- Verify your Gemini API key is valid
- Check the logs for detailed error messages
- The system will fall back to rule-based decisions

**Connection refused errors**
- Ensure the Flask server is running
- Check that the port (default 5000) is not blocked
- Verify the server host configuration

### Getting Help

- Check the application logs in `sensor_data.log`
- Run the test suite to verify functionality
- Review the API documentation above
- Check Google Gemini API status and quotas