import sys
import threading
import yaml
import time
import cv2
import uiautomator2 as u2
from adbutils import adb, AdbDevice

from bot.base.manifest import register_app
from bot.engine.scheduler import scheduler
from module.umamusume.manifest import UmamusumeManifest
from uvicorn import run


def _soft_recover_device(serial: str):
    """Attempt a non-destructive recovery of adb/uiautomator2 for a single device.

    Steps:
    - Remove adb forwards for the device (cleans stale 7912 bindings)
    - Kill/start adb server (what you usually do manually)
    - Wait for device to be ready again
    - Run uiautomator2 healthcheck to restart atx-agent if needed
    """
    try:
        print("   ♻️  Attempting auto-recovery (safe)…")
        # Restart adb server
        try:
            # Removes port forwarding on termination
            adb.server_kill()
        except Exception:
            pass

        # Ensure target device comes back online
        adb.connect(serial)
        adb.wait_for(serial, timeout=20)
        adb.shell(serial, ["echo", "pong"], timeout=5)

        # Light uiautomator2 warmup (avoid heavy healthcheck that may reinstall UIA APKs)
        try:
            d = u2.connect(serial)
            d.window_size()
            # Also ensure adb shell is responsive
            d.shell(["echo", "ok"], timeout=5)
            time.sleep(0.2)
        except Exception as e:
            print(f"   ⚠️  uiautomator2 warmup failed: {e}")
        print("   ✅ Auto-recovery step completed")
    except Exception as e:
        print(f"   ❌ Auto-recovery failed: {e}")


def _screenshot_probe(serial: str, samples=3, delay=0.5):
    """Try to take several screenshots via uiautomator2 and validate basic quality."""
    print("   🔌 Connecting to device…")
    d = u2.connect(serial)
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


def _finalize_services_light(serial: str, timeout_sec: float = 6.0) -> bool:
    """Warm up uiautomator2 lightly without risking APK installs, with timeout."""
    result = {"ok": False, "err": None}

    def _task():
        try:
            d = u2.connect(serial)
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


def check_umamusume_running(device: AdbDevice) -> bool:
    """Check if Umamusume is running on the device"""
    try:
        packages = device.list_packages()
        activities = {
            "com.cygames.umamusume": "jp.co.cygames.umamusume_activity.UmamusumeActivity",
            "jp.co.cygames.umamusume": "jp.co.cygames.umamusume_activity.UmamusumeActivity",
            "com.komoe.kmumamusumegp": "jp.co.cygames.umamusume_activity.UmamusumeActivity",
            "com.komoe.umamusumeofficial": "jp.co.cygames.umamusume_activity.UmamusumeActivity",
            "com.kakaogames.umamusume": "kr.co.kakaogames.umamusume_activity.UmamusumeActivity",
        }

        for package in packages:
            if package in activities.keys():
                if package is not device.app_current:
                    device.app_start(package, activities[package])
                return True

        print(f"❌ Umamusume not installed on device: {device.serial}")
        return False
    except:
        pass
    return False


def select_device() -> AdbDevice | None:
    """Let user select an ADB device"""
    print("🔍 Scanning for ADB devices...")
    devices = adb.device_list()

    if not devices:
        print("❌ No ADB devices found!")
        print("Please ensure:")
        print("1. Your emulator is running")
        print("2. ADB is enabled in emulator settings")
        print("3. USB debugging is enabled")
        return None

    print(f"\n📱 Found {len(devices)} device(s):")

    # Check which devices have Umamusume running
    umamusume_devices = []
    other_devices = []
    for i, device in enumerate(devices, 1):
        if check_umamusume_running(device):
            status = "🎮 Umamusume is Running"
            umamusume_devices.append(device)
        else:
            other_devices.append(device)
            status = "📱 Device Connected"
        print(f"{i}. {device.serial} - {status}")

    # Prioritize devices with Umamusume installed
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
                print(f"✅ Selected device: {selected_device.serial}")
                return selected_device
            else:
                print("❌ Invalid choice. Please try again.")
        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return None


def update_config(device_name: str):
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


def run_health_checks(selected_device: AdbDevice):
    """Run health checks after device selection"""
    print(" Running connection health checks...")

    # Test ADB connection
    try:
        devices = adb.device_list()
        if any(selected_device.serial == device.serial for device in devices):
            print("✅ ADB connection: OK")
        else:
            print("❌ ADB connection: FAILED")
            return False
    except Exception as e:
        print(f"❌ ADB health check failed: {e}")
        return False

    # Test device responsiveness
    try:
        adb.wait_for(selected_device.serial, timeout=10)
        selected_device.shell(["echo", "test"], timeout=10)
        print("✅ Device responsiveness: OK")
    except Exception as e:
        print(f"❌ Device health check failed: {e}")
        return False

    # Test Umamusume detection
    if check_umamusume_running(selected_device):
        print("✅ Umamusume detection: OK")
    else:
        print("⚠️  Umamusume not installed (this is OK)")
    
    # Test screenshot quality (THIS IS THE KEY TEST)
    print(" Testing screenshot quality…")
    try:
        _screenshot_probe(selected_device.serial)
    except Exception as e:
        # First failure -> try one auto-recovery cycle then retry once
        print(f"❌ Screenshot test failed: {e}")
        print("   🛠️  Running one-shot auto-recovery and retry…")
        _soft_recover_device(selected_device.serial)
        try:
            _screenshot_probe(selected_device.serial)
        except Exception as e2:
            print(f"❌ Screenshot test failed again after recovery: {e2}")
            return False

    print("✅ All health checks passed!")
    return True


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
    if not run_health_checks(selected_device):
        print("❌ Health checks failed. Please check your setup and try again.")
        sys.exit(1)

    # Final stabilization pass before starting services
    print("🔧 Finalizing device services…")
    _finalize_services_light(selected_device.serial)

    # Update config with selected device
    if not update_config(selected_device.serial):
        print("❌ Failed to update config. Exiting.")
        sys.exit(1)

    # Start the bot
    register_app(UmamusumeManifest)
    scheduler_thread = threading.Thread(target=scheduler.init, args=())
    scheduler_thread.start()
    print("🚀 UAT running on http://127.0.0.1:8071")
    run("bot.server.handler:server", host="127.0.0.1", port=8071, log_level="error")
