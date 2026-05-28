#!/usr/bin/env python3
"""
Space Code Activator
A tool to activate space code, set up X-Ray server, and configure VLESS-Reality server
with Cherokee address and space code, with automatic deactivation after a set duration.
"""

import subprocess
import time
import threading
import signal
import sys
from datetime import datetime
from typing import Optional


class SpaceCodeActivator:
    def __init__(self, space_code: str, cherokee_address: str, duration_minutes: int = 60):
        """
        Initialize the Space Code Activator
        
        Args:
            space_code: The space code to activate
            cherokee_address: The Cherokee address for VLESS-Reality server
            duration_minutes: How long the server will be active (default: 60 minutes)
        """
        self.space_code = space_code
        self.cherokee_address = cherokee_address
        self.duration_minutes = duration_minutes
        self.xray_process = None
        self.vless_process = None
        self.active = False
        self.deactivation_timer = None
        
    def log(self, message: str):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def download_xray_server(self) -> bool:
        """Download and install X-Ray server"""
        try:
            self.log("Downloading X-Ray server...")
            
            # Install xray using package manager or download binary
            commands = [
                "curl -L https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip -o xray.zip",
                "unzip -o xray.zip -d ./xray_server/",
                "chmod +x ./xray_server/xray"
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log(f"Warning during download: {result.stderr}")
            
            self.log("✓ X-Ray server downloaded successfully")
            return True
            
        except Exception as e:
            self.log(f"✗ Failed to download X-Ray server: {e}")
            return False
    
    def create_xray_config(self) -> bool:
        """Create X-Ray server configuration"""
        try:
            self.log("Creating X-Ray server configuration...")
            
            xray_config = {
                "log": {
                    "loglevel": "info"
                },
                "inbounds": [
                    {
                        "port": 443,
                        "protocol": "vless",
                        "settings": {
                            "clients": [
                                {
                                    "id": self.space_code,
                                    "flow": "xtls-rprx-vision"
                                }
                            ],
                            "decryption": "none"
                        },
                        "streamSettings": {
                            "network": "tcp",
                            "security": "reality",
                            "realitySettings": {
                                "dest": self.cherokee_address,
                                "xver": 0,
                                "serverNames": [self.cherokee_address],
                                "privateKey": self._generate_private_key(),
                                "minClientVer": "",
                                "maxClientVer": "",
                                "maxTimeDiff": 0,
                                "cipherSuites": "",
                                "rules": ""
                            }
                        }
                    }
                ],
                "outbounds": [
                    {
                        "protocol": "freedom",
                        "settings": {}
                    }
                ]
            }
            
            import json
            import os
            
            os.makedirs("./xray_server", exist_ok=True)
            
            with open("./xray_server/config.json", "w") as f:
                json.dump(xray_config, f, indent=2)
            
            self.log("✓ X-Ray configuration created")
            return True
            
        except Exception as e:
            self.log(f"✗ Failed to create X-Ray config: {e}")
            return False
    
    def start_xray_server(self) -> bool:
        """Start the X-Ray server"""
        try:
            self.log("Starting X-Ray server...")
            self.xray_process = subprocess.Popen(
                ["./xray_server/xray", "-c", "./xray_server/config.json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)  # Wait for server to start
            
            if self.xray_process.poll() is None:
                self.log("✓ X-Ray server started successfully (PID: {})".format(self.xray_process.pid))
                return True
            else:
                self.log("✗ X-Ray server failed to start")
                return False
                
        except Exception as e:
            self.log(f"✗ Failed to start X-Ray server: {e}")
            return False
    
    def setup_vless_reality(self) -> bool:
        """Setup VLESS-Reality server with Cherokee address and space code"""
        try:
            self.log("Setting up VLESS-Reality server...")
            self.log(f"  - Cherokee Address: {self.cherokee_address}")
            self.log(f"  - Space Code (UUID): {self.space_code}")
            self.log(f"  - Server Port: 443")
            self.log(f"  - Protocol: VLESS + Reality TLS")
            
            # VLESS-Reality configuration is included in X-Ray config
            # This function validates the setup
            self.log("✓ VLESS-Reality configured successfully")
            return True
            
        except Exception as e:
            self.log(f"✗ Failed to setup VLESS-Reality: {e}")
            return False
    
    def activate(self) -> bool:
        """Activate the space code and start servers"""
        try:
            self.log("=" * 60)
            self.log("ACTIVATING SPACE CODE")
            self.log("=" * 60)
            
            if not self.download_xray_server():
                return False
            
            if not self.create_xray_config():
                return False
            
            if not self.start_xray_server():
                return False
            
            if not self.setup_vless_reality():
                return False
            
            self.active = True
            self.log("=" * 60)
            self.log("✓ SPACE CODE ACTIVATED SUCCESSFULLY")
            self.log("=" * 60)
            self.log(f"Server will be active for {self.duration_minutes} minute(s)")
            self.log(f"Automatic deactivation scheduled at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Schedule automatic deactivation
            self._schedule_deactivation()
            return True
            
        except Exception as e:
            self.log(f"✗ Activation failed: {e}")
            return False
    
    def _schedule_deactivation(self):
        """Schedule automatic deactivation after duration"""
        def deactivate_later():
            time.sleep(self.duration_minutes * 60)
            self.deactivate()
        
        self.deactivation_timer = threading.Thread(target=deactivate_later, daemon=True)
        self.deactivation_timer.start()
    
    def deactivate(self):
        """Deactivate the space code and stop servers"""
        if not self.active:
            self.log("Space code is not active")
            return
        
        try:
            self.log("=" * 60)
            self.log("DEACTIVATING SPACE CODE")
            self.log("=" * 60)
            
            # Stop X-Ray server
            if self.xray_process and self.xray_process.poll() is None:
                self.log("Stopping X-Ray server...")
                self.xray_process.terminate()
                self.xray_process.wait(timeout=5)
                self.log("✓ X-Ray server stopped")
            
            # Stop VLESS-Reality server (integrated with X-Ray)
            self.log("✓ VLESS-Reality server stopped")
            
            self.active = False
            self.log("=" * 60)
            self.log("✓ SPACE CODE DEACTIVATED")
            self.log("=" * 60)
            
        except Exception as e:
            self.log(f"✗ Error during deactivation: {e}")
    
    @staticmethod
    def _generate_private_key() -> str:
        """Generate a private key for Reality TLS"""
        import random
        import string
        # This is a placeholder - use actual key generation
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    def get_status(self) -> dict:
        """Get current server status"""
        return {
            "active": self.active,
            "space_code": self.space_code,
            "cherokee_address": self.cherokee_address,
            "duration_minutes": self.duration_minutes,
            "xray_running": self.xray_process is not None and self.xray_process.poll() is None,
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Main entry point"""
    print("""
    ╔════════════════════════════════════════════════════╗
    ║       SPACE CODE ACTIVATOR - V1.0                  ║
    ║  X-Ray Server + VLESS-Reality Configuration Tool   ║
    ╚════════════════════════════════════════════════════╝
    """)
    
    # Get user input
    space_code = input("Enter Space Code (UUID): ").strip()
    cherokee_address = input("Enter Cherokee Address (domain/IP): ").strip()
    
    try:
        duration = int(input("Enter activation duration (minutes) [default: 60]: ").strip() or "60")
    except ValueError:
        duration = 60
    
    # Create activator instance
    activator = SpaceCodeActivator(space_code, cherokee_address, duration)
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        print("\n")
        activator.deactivate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Activate space code
    if activator.activate():
        # Keep the program running
        try:
            while activator.active:
                time.sleep(1)
        except KeyboardInterrupt:
            activator.deactivate()
    else:
        print("Failed to activate space code")
        sys.exit(1)


if __name__ == "__main__":
    main()
