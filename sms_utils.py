import africastalking
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class SMSManager:
    """Africa's Talking SMS manager for farmer alerts"""
    
    def __init__(self):
        """Initialize the SMS manager with Africa's Talking credentials"""
        # Initialize Africa's Talking
        try:
            africastalking.initialize(
                username=os.getenv("AT_USERNAME"),
                api_key=os.getenv("AT_API_KEY")
            )
            self.sms = africastalking.SMS
            self.sms_enabled = True
            logger.info(f"SMS service initialized for {'sandbox' if Config.AT_SANDBOX else 'live'} environment")
        except Exception as e:
            logger.error(f"Failed to initialize Africa's Talking SMS: {e}")
            self.sms_enabled = False
            self.sms = None
        
        # State tracking to prevent spam
        self.last_state = {}
        self.last_alert_time = {}
        
        # Load previous state if exists
        self._load_state()
    
    def _load_state(self):
        """Load previous state from file to persist across restarts"""
        try:
            with open('sms_state.json', 'r') as f:
                data = json.load(f)
                self.last_state = data.get('last_state', {})
                self.last_alert_time = data.get('last_alert_time', {})
                logger.info("Loaded SMS state from file")
        except FileNotFoundError:
            logger.info("No previous SMS state found - starting fresh")
        except Exception as e:
            logger.warning(f"Failed to load SMS state: {e}")
    
    def _save_state(self):
        """Save current state to file"""
        try:
            with open('sms_state.json', 'w') as f:
                json.dump({
                    'last_state': self.last_state,
                    'last_alert_time': self.last_alert_time
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save SMS state: {e}")
    
    def _should_send_alert(self, alert_type: str, current_decision: Dict[str, Any]) -> bool:
        """
        Determine if an SMS alert should be sent based on state changes and timing
        
        Args:
            alert_type: Type of alert (temperature, gas, etc.)
            current_decision: Current AI decision
            
        Returns:
            Boolean indicating if alert should be sent
        """
        current_time = datetime.now()
        
        # Critical alerts (gas) should always be sent with minimum delay
        if alert_type == 'gas_alert' and current_decision.get('gas_alert', False):
            last_gas_alert = self.last_alert_time.get('gas_alert')
            if not last_gas_alert:
                return True
            
            # Send gas alerts maximum once every 5 minutes
            time_diff = (current_time - datetime.fromisoformat(last_gas_alert)).total_seconds()
            return time_diff >= Config.GAS_ALERT_COOLDOWN
        
        # For non-critical alerts, check for state changes
        if alert_type in self.last_state:
            last_decision = self.last_state[alert_type]
            
            # Check if there's a meaningful state change
            if alert_type == 'temperature':
                last_fan = last_decision.get('fan', 'unknown')
                last_led = last_decision.get('led', 'unknown')
                current_fan = current_decision.get('fan', 'unknown')
                current_led = current_decision.get('led', 'unknown')
                
                # Send alert if fan state or LED color changed
                return last_fan != current_fan or last_led != current_led
            
            elif alert_type == 'priority':
                last_priority = last_decision.get('priority', 'unknown')
                current_priority = current_decision.get('priority', 'unknown')
                
                # Send alert if priority increased to high or critical
                return (current_priority in ['high', 'critical'] and 
                       last_priority not in ['high', 'critical'])
        
        # First time alert or unknown state - send it
        return True
    
    def _format_temperature_message(self, decision: Dict[str, Any], sensor_data: Dict[str, Any]) -> str:
        """Format temperature-related SMS message"""
        temp = sensor_data['temperature']
        fan_state = decision.get('fan', 'unknown')
        led_color = decision.get('led', 'unknown')
        
        if temp >= Config.TEMP_HOT_THRESHOLD:
            if fan_state == 'on':
                return f"🌡️ HIGH TEMP ALERT: {temp}°C detected! Fan turned ON automatically. Red warning light activated. Please check your crops immediately."
            else:
                return f"🌡️ HIGH TEMPERATURE: {temp}°C recorded. Please monitor your crops closely."
        
        elif temp < Config.TEMP_COLD_THRESHOLD:
            return f"❄️ LOW TEMP ALERT: {temp}°C detected! Fan turned OFF. Blue indicator active. Consider protective measures for your crops."
        
        else:
            if self.last_state.get('temperature', {}).get('fan') == 'on':
                return f"✅ TEMP NORMALIZED: {temp}°C. Fan turned OFF automatically. Yellow indicator shows normal conditions."
            else:
                return f"✅ Temperature normal: {temp}°C. All systems operating normally."
    
    def _format_gas_message(self, decision: Dict[str, Any], sensor_data: Dict[str, Any]) -> str:
        """Format gas alert SMS message"""
        gas_level = sensor_data['gas_level']
        
        if decision.get('gas_alert', False):
            return f"🚨 GAS ALERT! Dangerous gas levels detected ({gas_level}/1023). IMMEDIATE ACTION REQUIRED! Check for gas leaks, ensure ventilation, and evacuate if necessary."
        else:
            return f"✅ Gas levels normalized ({gas_level}/1023). Safe to resume normal operations."
    
    def _format_priority_message(self, decision: Dict[str, Any], sensor_data: Dict[str, Any]) -> str:
        """Format priority-based SMS message"""
        priority = decision.get('priority', 'unknown')
        temp = sensor_data['temperature']
        gas = sensor_data['gas_level']
        humidity = sensor_data['humidity']
        
        if priority == 'critical':
            return f"🚨 CRITICAL ALERT! Multiple issues detected - Temp: {temp}°C, Gas: {gas}, Humidity: {humidity}%. Immediate attention required!"
        
        elif priority == 'high':
            return f"⚠️ HIGH PRIORITY: Environmental conditions need attention - Temp: {temp}°C, Gas: {gas}. Please check your setup."
        
        return f"📊 System Update: All sensors normal - Temp: {temp}°C, Humidity: {humidity}%, Gas: {gas}."
    
    def send_farmer_alert(self, decision: Dict[str, Any], sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send SMS alert to farmer based on AI decision and sensor data
        
        Args:
            decision: AI decision from Gemini
            sensor_data: Raw sensor data
            
        Returns:
            Dictionary with SMS sending result
        """
        if not self.sms_enabled:
            logger.warning("SMS service not enabled - skipping alert")
            return {"success": False, "reason": "SMS service not configured"}
        
        if not Config.AT_RECIPIENT_PHONE:
            logger.warning("No recipient phone number configured - skipping alert")
            return {"success": False, "reason": "No recipient phone number"}
        
        alerts_sent = []
        
        try:
            # Check for gas alerts (highest priority)
            if decision.get('gas_alert', False) and self._should_send_alert('gas_alert', decision):
                message = self._format_gas_message(decision, sensor_data)
                result = self._send_sms(message, 'gas_alert')
                if result['success']:
                    alerts_sent.append('gas_alert')
                    self.last_alert_time['gas_alert'] = datetime.now().isoformat()
            
            # Check for temperature state changes
            if self._should_send_alert('temperature', decision):
                message = self._format_temperature_message(decision, sensor_data)
                result = self._send_sms(message, 'temperature')
                if result['success']:
                    alerts_sent.append('temperature')
            
            # Check for priority level changes
            if self._should_send_alert('priority', decision) and decision.get('priority') in ['high', 'critical']:
                message = self._format_priority_message(decision, sensor_data)
                result = self._send_sms(message, 'priority')
                if result['success']:
                    alerts_sent.append('priority')
            
            # Update state tracking
            self.last_state['temperature'] = decision.copy()
            self.last_state['priority'] = decision.copy()
            self.last_state['gas_alert'] = decision.copy()
            self._save_state()
            
            if alerts_sent:
                logger.info(f"SMS alerts sent successfully: {alerts_sent}")
                return {
                    "success": True,
                    "alerts_sent": alerts_sent,
                    "count": len(alerts_sent)
                }
            else:
                logger.info("No SMS alerts needed - no state changes detected")
                return {
                    "success": True,
                    "alerts_sent": [],
                    "reason": "No state changes requiring alerts"
                }
                
        except Exception as e:
            logger.error(f"Error in SMS alert processing: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_sms(self, message: str, alert_type: str) -> Dict[str, Any]:
        """
        Send SMS using Africa's Talking API
        
        Args:
            message: SMS message content
            alert_type: Type of alert for logging
            
        Returns:
            Dictionary with sending result
        """
        try:
            # Prepare message with sender info if configured
            if Config.AT_SENDER_ID:
                sender = Config.AT_SENDER_ID
            else:
                sender = None
            
            # Send SMS
            response = self.sms.send(
                message=message,
                recipients=[Config.AT_RECIPIENT_PHONE],
                sender_id=sender
            )
            
            # Log the response
            logger.info(f"SMS sent ({alert_type}): {message[:50]}...")
            logger.info(f"Africa's Talking response: {response}")
            
            # Check if sending was successful
            if response['SMSMessageData']['Recipients']:
                recipient = response['SMSMessageData']['Recipients'][0]
                if recipient['status'] == 'Success':
                    logger.info(f"SMS delivered successfully to {Config.AT_RECIPIENT_PHONE}")
                    return {
                        "success": True,
                        "message": message,
                        "recipient": Config.AT_RECIPIENT_PHONE,
                        "cost": recipient.get('cost', 'Unknown'),
                        "message_id": recipient.get('messageId', 'Unknown')
                    }
                else:
                    logger.error(f"SMS delivery failed: {recipient.get('status', 'Unknown error')}")
                    return {
                        "success": False,
                        "error": recipient.get('status', 'Unknown error'),
                        "message": message
                    }
            else:
                logger.error("No recipients in SMS response")
                return {"success": False, "error": "No recipients in response"}
                
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return {"success": False, "error": str(e)}
    
    def send_test_message(self) -> Dict[str, Any]:
        """Send a test SMS message"""
        if not self.sms_enabled:
            return {"success": False, "error": "SMS service not enabled"}
        
        test_message = f"🧪 Test message from Arduino Sensor System at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. SMS alerts are working correctly!"
        
        return self._send_sms(test_message, 'test')
    
    def get_status(self) -> Dict[str, Any]:
        """Get SMS service status"""
        return {
            "sms_enabled": self.sms_enabled,
            "sandbox_mode": Config.AT_SANDBOX,
            "recipient_configured": bool(Config.AT_RECIPIENT_PHONE),
            "sender_id": Config.AT_SENDER_ID or "Default",
            "last_state": self.last_state,
            "gas_alert_cooldown": f"{Config.GAS_ALERT_COOLDOWN} seconds"
        }