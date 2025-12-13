import subprocess
import logging

try:
    import win32gui, win32con
except Exception:
    win32gui = None
    win32con = None

def _restore_focus_by_title(substrings):
    if win32gui is None:
        return False
    found = {"ok": False}
    def _cb(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = (win32gui.GetWindowText(hwnd) or "").lower()
            if any(s in title for s in substrings):
                try:
                    if win32gui.IsIconic(hwnd):
                        win32gui.ShowWindow(hwnd, 9)
                    win32gui.SetForegroundWindow(hwnd)
                    found["ok"] = True
                    return False
                except Exception:
                    return True
            return True
        except Exception:
            return True
    try:
        win32gui.EnumWindows(_cb, None)
    except Exception:
        return False
    return found["ok"]


def handle_control_command(command, lang="en"):
    command = command.lower().strip()
    user_name = "Abdul Rahman"
    
    # Open applications
    if "open" in command:
        apps = {
            "youtube": "https://www.youtube.com",
            "google meet": "https://meet.google.com",
            "meet": "https://meet.google.com",
            "google chrome": "start chrome",
            "chrome": "start chrome",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "file explorer": "explorer.exe",
            "vscode": "code.exe",
            "control panel": "control.exe",
            "recycle bin": "shell:RecycleBinFolder",
            "microsoft store": "ms-windows-store:"
        }
        for app_name, app_cmd in apps.items():
            if app_name in command:
                try:
                    if app_cmd.startswith("http"):
                        # Open URL in default browser
                        subprocess.Popen(["cmd", "/c", "start", app_cmd], shell=True)
                    elif app_cmd.startswith("start "):
                        # Use cmd to start application
                        subprocess.Popen(["cmd", "/c", app_cmd], shell=True)
                    else:
                        subprocess.Popen(app_cmd, shell=True)
                    response = f"Opening {app_name}, {user_name}."
                    logging.info("Opened %s", app_name)
                    return response
                except Exception as e:
                    logging.error("Failed to open %s: %s", app_name, e)
                    return f"Failed to open {app_name}, {user_name}."
    
    # Minimize all windows / Show desktop
    if ("minimize all" in command) or ("minimize windows" in command) or ("show desktop" in command) or (command.strip() in ["minimize", "desktop", "minimize all windows"]):
        try:
            subprocess.run([
                "powershell", "-NoProfile", "-Command",
                "(New-Object -ComObject Shell.Application).MinimizeAll()"
            ], capture_output=True, shell=True, timeout=5)
            response = f"Minimizing all windows, {user_name}."
            logging.info("Minimized all windows")
            return response
        except Exception as e:
            logging.error("Failed to minimize all windows: %s", e)
            return f"Failed to minimize all windows, {user_name}."

    # Restore minimized windows
    if ("restore windows" in command) or ("undo minimize" in command) or ("restore all" in command) or ("show windows" in command):
        try:
            subprocess.run([
                "powershell", "-NoProfile", "-Command",
                "(New-Object -ComObject Shell.Application).UndoMinimizeAll()"
            ], capture_output=True, shell=True, timeout=5)
            response = f"Restoring windows, {user_name}."
            logging.info("Restored all windows")
            return response
        except Exception as e:
            logging.error("Failed to restore windows: %s", e)
            return f"Failed to restore windows, {user_name}."

    # Restore/focus Chrome specifically
    if ("restore" in command or "focus" in command or "bring" in command) and ("chrome" in command or "google chrome" in command):
        try:
            if _restore_focus_by_title(["google chrome", "chrome"]):
                response = f"Restoring Chrome, {user_name}."
                logging.info("Restored/focused Chrome window")
                return response
            # Fallback: start Chrome if no window found
            subprocess.Popen(["cmd", "/c", "start", "chrome"], shell=True)
            response = f"Opening Chrome, {user_name}."
            logging.info("Started Chrome as fallback")
            return response
        except Exception as e:
            logging.error("Failed to restore Chrome: %s", e)
            return f"Failed to restore Chrome, {user_name}."

    # Specific Windows Settings pages
    settings_map = {
        "display": "ms-settings:display",
        "sound": "ms-settings:sound",
        "bluetooth": "ms-settings:bluetooth",
        "network": "ms-settings:network-status",
        "wifi": "ms-settings:network-wifi",
        "wi-fi": "ms-settings:network-wifi",
        "personalization": "ms-settings:personalization",
        "background": "ms-settings:personalization-background",
        "apps": "ms-settings:appsfeatures",
        "privacy": "ms-settings:privacy",
        "time": "ms-settings:dateandtime",
        "language": "ms-settings:regionlanguage",
        "update": "ms-settings:windowsupdate",
        "gaming": "ms-settings:gaming-gamebar",
        "storage": "ms-settings:storagesense",
        "about": "ms-settings:about"
    }
    for key, uri in settings_map.items():
        if f"{key} settings" in command or (key in command and "settings" in command):
            try:
                subprocess.run(["cmd", "/c", "start", uri], capture_output=True, shell=True, timeout=5)
                response = f"Opening {key.title()} settings, {user_name}."
                logging.info("Opened Settings page: %s", key)
                return response
            except Exception as e:
                logging.error("Failed to open %s settings: %s", key, e)
                return f"Failed to open {key} settings, {user_name}."

    # Open Windows Settings
    if (
        "system settings" in command
        or "windows settings" in command
        or "open settings" in command
        or "show settings" in command
        or command.strip() == "settings"
    ):
        try:
            subprocess.run(["cmd", "/c", "start", "ms-settings:"], capture_output=True, shell=True, timeout=5)
            response = f"Opening Settings, {user_name}."
            logging.info("Opened Windows Settings")
            return response
        except Exception as e:
            logging.error("Failed to open Settings: %s", e)
            return f"Failed to open Settings, {user_name}."

    # Screenshot capture - save to Downloads
    if (
        "screenshot" in command
        or "screen shot" in command
        or "screen capture" in command
        or "take a screenshot" in command
        or command.strip() in ["screenshot", "snap"]
    ):
        try:
            ps_script = "; ".join([
                "$ErrorActionPreference='Stop'",
                "$path = Join-Path $env:USERPROFILE 'Downloads'",
                "$file = 'screenshot_{0}.png' -f (Get-Date -Format 'yyyyMMdd_HHmmss')",
                "$full = Join-Path $path $file",
                "Add-Type -AssemblyName System.Windows.Forms",
                "Add-Type -AssemblyName System.Drawing",
                "$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen",
                "$bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)",
                "$gfx = [System.Drawing.Graphics]::FromImage($bmp)",
                "$gfx.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bmp.Size)",
                "$bmp.Save($full, [System.Drawing.Imaging.ImageFormat]::Png)",
                "Write-Output $full"
            ])
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, shell=True, timeout=10, text=True
            )
            if result.returncode == 0:
                saved_path = result.stdout.strip().splitlines()[-1]
                try:
                    subprocess.Popen(["explorer.exe", "/select," + saved_path], shell=True)
                except Exception:
                    pass
                response = f"Screenshot saved to Downloads: {saved_path}"
                logging.info("Screenshot saved: %s", saved_path)
                return response
            else:
                logging.error("Screenshot failed: %s", result.stderr)
                return "Failed to take screenshot."
        except Exception as e:
            logging.error("Screenshot error: %s", e)
            return f"Failed to take screenshot: {e}"

    # Close applications
    if "close" in command:
        close_apps = {
            "youtube": "chrome.exe",  # YouTube runs in browser
            "browser": "chrome.exe",
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "file explorer": "explorer.exe",
            "vscode": "code.exe"
        }
        for app_name, process_name in close_apps.items():
            if app_name in command:
                try:
                    subprocess.run(["taskkill", "/F", "/IM", process_name], 
                                 capture_output=True, shell=True, timeout=5)
                    response = f"Closing {app_name}, {user_name}."
                    logging.info("Closed %s", app_name)
                    return response
                except Exception as e:
                    logging.error("Failed to close %s: %s", app_name, e)
                    return f"Failed to close {app_name}, {user_name}."
    
    # Placeholder for other control commands
    return None