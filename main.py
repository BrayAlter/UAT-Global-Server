import sys
import threading
import subprocess
import os
import yaml
import time
import cv2

from bot.base.manifest import register_app
from bot.engine.scheduler import scheduler
from module.umamusume.manifest import UmamusumeManifest
from uvicorn import run


def _get_adb_path():
    """Resolve bundled adb path."""
    return os.path.join("deps", "adb", "adb.exe")


def _run_adb(args, timeout=10, capture_output=True, text=True):
    """Run an adb command with the bundled binary and return CompletedProcess."""
    adb_path = _get_adb_path()
    return subprocess.run([adb_path] + args, capture_output=capture_output, text=text, timeout=timeout)


def _soft_recover_device(device_id):
    """Attempt a non-destructive recovery of adb/uiautomator2 for a single device.

    Steps:
    - Remove adb forwards for the device (cleans stale 7912 bindings)
    - Kill/start adb server (what you usually do manually)
    - Wait for device to be ready again
    - Run uiautomator2 healthcheck to restart atx-agent if needed
    """
    try:
        print("   ♻️  Attempting auto-recovery (safe)…")
        # Best-effort forward removal (ignore failures)
        try:
            _run_adb(["-s", device_id, "forward", "--remove-all"], timeout=5)
        except Exception:
            pass

        # Restart adb server
        try:
            _run_adb(["kill-server"], timeout=5)
        except Exception:
            pass
        _run_adb(["start-server"], timeout=10)

        # Ensure target device comes back online
        _run_adb(["-s", device_id, "wait-for-device"], timeout=20)

        # Ping device quickly
        pong = _run_adb(["-s", device_id, "shell", "echo", "pong"], timeout=5)
        if pong.returncode != 0:
            print("   ⚠️  Device not responsive yet; will still try healthcheck…")

        # Light uiautomator2 warmup (avoid heavy healthcheck that may reinstall UIA APKs)
        try:
            import uiautomator2 as u2
            d = u2.connect(device_id)
            # Warm up a simple RPC that doesn't require UIAutomator service
            _ = d.window_size()
            # Also ensure adb shell is responsive
            _run_adb(["-s", device_id, "shell", "echo", "ok"], timeout=5)
            time.sleep(0.2)
        except Exception as e:
            print(f"   ⚠️  uiautomator2 warmup failed: {e}")
        print("   ✅ Auto-recovery step completed")
    except Exception as e:
        print(f"   ❌ Auto-recovery failed: {e}")


def _screenshot_probe(device_id, samples=3, delay=0.5):
    """Try to take several screenshots via uiautomator2 and validate basic quality."""
    import uiautomator2 as u2
    print("   🔌 Connecting to device…")
    d = u2.connect(device_id)
    print("   ✅ Device connected successfully")

    screenshots = []
    print("   Taking screenshots (this may take a moment)…")
    for i in range(samples):
        print(f"      Screenshot {i+1}/{samples}…")
        img = d.screenshot(format='opencv')
        if img is not None:
            screenshots.append(img)
            print(f"      ✅ Screenshot {i+1}: {img.shape[1]}x{img.shape[0]} pixels")
        else:
            print(f"      ❌ Screenshot {i+1}: FAILED")
        time.sleep(delay)

    if len(screenshots) < samples:
        raise RuntimeError("insufficient_screenshots")

    print("   🔍 Analyzing screenshot quality…")
    if screenshots[0].std() < 5:
        raise RuntimeError("corrupted_static_image")

    print("   🔄 Checking for display pipeline issues…")
    diff1 = cv2.absdiff(screenshots[0], screenshots[1]).mean()
    diff2 = cv2.absdiff(screenshots[1], screenshots[2]).mean()
    if diff1 < 1 and diff2 < 1:
        raise RuntimeError("display_stuck")

    print("✅ Screenshot quality: OK")


def _finalize_services_light(device_id: str, timeout_sec: float = 6.0) -> bool:
    """Warm up uiautomator2 lightly without risking APK installs, with timeout."""
    result = {"ok": False, "err": None}

    def _task():
        try:
            import uiautomator2 as u2
            d = u2.connect(device_id)
            _ = d.window_size()
            time.sleep(0.2)
            result["ok"] = True
        except Exception as e:  # noqa: BLE001
            result["err"] = e

    t = threading.Thread(target=_task, daemon=True)
    t.start()
    t.join(timeout=timeout_sec)
    if t.is_alive():
        print("⚠️  Finalization timed out; continuing without it")
        return False
    if not result["ok"]:
        print(f"⚠️  Could not finalize device services: {result['err']}")
        return False
    print("✅ Device services ready")
    return True


def get_adb_devices():
    """Get list of connected ADB devices"""
    try:
        # Use the adb from deps directory
        adb_path = _get_adb_path()
        
        if not os.path.exists(adb_path):
            print("❌ ADB not found in deps/adb/ directory")
            return []
        
        # First try to get devices
        result = subprocess.run([adb_path, "devices"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"❌ ADB error: {result.stderr}")
            return []
        
        devices = []
        lines = result.stdout.strip().split('\n')[1:]  # Skip header line
        
        for line in lines:
            if line.strip() and '\t' in line:
                device_id, status = line.split('\t')
                if status == 'device':
                    devices.append(device_id)
        
        # If no devices found, try restarting ADB server
        if not devices:
            print("🔄 No devices found, restarting ADB server...")
            subprocess.run([adb_path, "kill-server"], capture_output=True, timeout=5)
            subprocess.run([adb_path, "start-server"], capture_output=True, timeout=10)
            
            # Try again after restart
            result = subprocess.run([adb_path, "devices"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]
                for line in lines:
                    if line.strip() and '\t' in line:
                        device_id, status = line.split('\t')
                        if status == 'device':
                            devices.append(device_id)
        
        return devices
    except Exception as e:
        print(f"❌ Error getting ADB devices: {e}")
        return []


def check_umamusume_running(device_id):
    """Check if Umamusume is running on the device"""
    try:
        adb_path = _get_adb_path()
        cmd = [adb_path, "-s", device_id, "shell", "dumpsys", "activity", "activities"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Look for Umamusume package in running activities
            output = result.stdout.lower()
            umamusume_packages = [
                "com.cygames.umamusume",
                "jp.co.cygames.umamusume",
                "umamusume"
            ]
            return any(pkg in output for pkg in umamusume_packages)
    except:
        pass
    return False


def select_device():
    """Let user select an ADB device"""
    print("🔍 Scanning for ADB devices...")
    devices = get_adb_devices()
    
    if not devices:
        print("❌ No ADB devices found!")
        print("Please ensure:")
        print("1. Your emulator is running")
        print("2. ADB is enabled in emulator settings")
        print("3. USB debugging is enabled")
        return None
    
    print(f"\n📱 Found {len(devices)} device(s):")
    
    # Check which devices have Umamusume running
    device_info = []
    for i, device_id in enumerate(devices, 1):
        has_umamusume = check_umamusume_running(device_id)
        status = "🎮 Umamusume Running" if has_umamusume else "📱 Device Connected"
        device_info.append((device_id, has_umamusume))
        print(f"{i}. {device_id} - {status}")
    
    # Prioritize devices with Umamusume running
    umamusume_devices = [d for d, has_uma in device_info if has_uma]
    other_devices = [d for d, has_uma in device_info if not has_uma]
    
    if umamusume_devices:
        print(f"\n🎯 Recommended devices (Umamusume detected):")
        for i, device_id in enumerate(umamusume_devices, 1):
            print(f"  {i}. {device_id}")
    
    while True:
        try:
            choice = input(f"\nSelect device (1-{len(devices)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(devices):
                selected_device = devices[choice_num - 1]
                print(f"✅ Selected device: {selected_device}")
                return selected_device
            else:
                print("❌ Invalid choice. Please try again.")
        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return None


def update_config(device_name):
    """Update config.yaml with selected device"""
    try:
        with open("config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        config['bot']['auto']['adb']['device_name'] = device_name
        
        with open("config.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ Updated config.yaml with device: {device_name}")
        return True
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False


def run_health_checks():
    """Run health checks after device selection"""
    print(" Running connection health checks...")
    
    # Test ADB connection
    try:
        adb_path = _get_adb_path()
        result = subprocess.run([adb_path, "devices"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and selected_device in result.stdout:
            print("✅ ADB connection: OK")
        else:
            print("❌ ADB connection: FAILED")
            return False
    except Exception as e:
        print(f"❌ ADB health check failed: {e}")
        return False
    
    # Test device responsiveness
    try:
        result = subprocess.run([adb_path, "-s", selected_device, "shell", "echo", "test"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Device responsiveness: OK")
        else:
            print("❌ Device responsiveness: FAILED")
            return False
    except Exception as e:
        print(f"❌ Device health check failed: {e}")
        return False
    
    # Test Umamusume detection
    if check_umamusume_running(selected_device):
        print("✅ Umamusume detection: OK")
    else:
        print("⚠️  Umamusume not running (this is OK)")
    
        
    print("✅ All health checks passed!")
    return True


def app_keepalive_loop(device_id):
    package = "com.cygames.umamusume"
    while True:
        try:
            state = _run_adb(["-s", device_id, "get-state"], timeout=5)
            if state.returncode == 0 and "device" in (state.stdout or ""):
                _run_adb(["-s", device_id, "shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"], timeout=5)
        except Exception:
            pass
        time.sleep(10)

if __name__ == '__main__':
    if sys.version_info.minor != 10 or sys.version_info.micro != 9:
        print("\033[33m{}\033[0m".format("Warning: Python version is incorrect, may not run properly"))
        print("Recommended Python version: 3.10.9  Current: " + sys.version)
    
    # Device selection
    selected_device = select_device()
    if selected_device is None:
        print("❌ No device selected. Exiting.")
        sys.exit(1)
    
    # Run health checks
    if not run_health_checks():
        print("❌ Health checks failed. Please check your setup and try again.")
        sys.exit(1)
    
    # Final stabilization pass before starting services
    print("🔧 Finalizing device services…")
    _finalize_services_light(selected_device)

    # Update config with selected device
    if not update_config(selected_device):
        print("❌ Failed to update config. Exiting.")
        sys.exit(1)

    keepalive_thread = threading.Thread(target=app_keepalive_loop, args=(selected_device,), daemon=True)
    keepalive_thread.start()

    # Start the bot
    register_app(UmamusumeManifest)
    scheduler_thread = threading.Thread(target=scheduler.init, args=())
    scheduler_thread.start()
    print("🚀 UAT running on http://127.0.0.1:8071")
    run("bot.server.handler:server", host="127.0.0.1", port=8071, log_level="error")

