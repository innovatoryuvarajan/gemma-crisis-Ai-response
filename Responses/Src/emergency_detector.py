import asyncio
import threading
from bleak import BleakClient, BleakScanner
from config import *

class EmergencyDetector:
    def __init__(self):
        self.ble_device = None
        self.is_monitoring = False
        print("🚨 Emergency Detector initialized")
    
    def detect_sos_in_text(self, text):
        """Detect SOS keywords in text"""
        text_lower = text.lower()
        
        # Check for explicit SOS keywords
        for keyword in SOS_KEYWORDS:
            if keyword in text_lower:
                return True, keyword
        
        # Check for high urgency situations
        for keyword in HIGH_URGENCY_KEYWORDS:
            if keyword in text_lower:
                return True, keyword
        
        return False, None
    
    async def find_ble_device(self):
        """Scan for SOS BLE device"""
        print("🔍 Scanning for BLE SOS device...")
        try:
            devices = await BleakScanner.discover(timeout=5.0)
            for device in devices:
                if device.name and BLE_DEVICE_NAME in device.name:
                    print(f"✅ Found SOS device: {device.name} ({device.address})")
                    return device
            print("⚠️ No SOS BLE device found")
            return None
        except Exception as e:
            print(f"❌ BLE scan error: {e}")
            return None
    
    async def trigger_ble_sos(self):
        """Trigger SOS signal via BLE"""
        if not self.ble_device:
            self.ble_device = await self.find_ble_device()
        
        if not self.ble_device:
            print("❌ Cannot trigger BLE SOS - no device found")
            return False
        
        try:
            async with BleakClient(self.ble_device.address) as client:
                print(f"🔵 Connected to {self.ble_device.name}")
                
                # Send SOS signal (adjust based on your BLE device protocol)
                sos_data = b"SOS_TRIGGER"
                await client.write_gatt_char(BLE_SERVICE_UUID, sos_data)
                
                print("✅ SOS signal sent via BLE")
                return True
                
        except Exception as e:
            print(f"❌ BLE SOS trigger error: {e}")
            return False
    
    def trigger_sos_sync(self):
        """Synchronous wrapper for BLE SOS trigger"""
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.trigger_ble_sos())
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_async)
        thread.start()
        thread.join(timeout=10)  # 10 second timeout
    
    def handle_emergency(self, text, detected_keyword):
        """Handle detected emergency situation"""
        print(f"🚨 EMERGENCY DETECTED: '{detected_keyword}' in text: {text}")
        
        # Trigger BLE SOS in background
        print("🔵 Triggering BLE SOS beacon...")
        threading.Thread(target=self.trigger_sos_sync, daemon=True).start()
        
        # Return emergency acknowledgment
        return f"Emergency detected: {detected_keyword}. SOS beacon activated. Help is being requested."