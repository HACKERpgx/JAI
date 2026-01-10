import subprocess
import logging
import re

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


# --- Helpers for terminal and color/action parsing ---
def _best_terminal() -> str:
    """Return 'ps' for PowerShell as the default/best terminal on Windows."""
    return "ps"


_CMD_COLOR_MAP = {
    # standard
    "black": "0", "blue": "1", "green": "2", "aqua": "3", "cyan": "3",
    "red": "4", "purple": "5", "magenta": "5", "yellow": "6", "brown": "6",
    "white": "7", "grey": "8", "gray": "8",
    # bright/light
    "light gray": "7", "lightgrey": "7", "lightgray": "7",
    "light blue": "9", "lightblue": "9",
    "light green": "a", "lightgreen": "a",
    "light aqua": "b", "lightaqua": "b", "light cyan": "b", "lightcyan": "b",
    "light red": "c", "lightred": "c",
    "light purple": "d", "lightpurple": "d", "light magenta": "d", "lightmagenta": "d",
    "light yellow": "e", "lightyellow": "e",
    "bright white": "f", "brightwhite": "f",
}

_PS_COLOR_MAP = {
    # PowerShell ConsoleColor names
    "black": "Black",
    "darkblue": "DarkBlue", "blue": "Blue",
    "darkgreen": "DarkGreen", "green": "Green",
    "darkcyan": "DarkCyan", "cyan": "Cyan", "aqua": "Cyan",
    "darkred": "DarkRed", "red": "Red",
    "darkmagenta": "DarkMagenta", "magenta": "Magenta", "purple": "Magenta",
    "darkyellow": "DarkYellow", "yellow": "Yellow", "brown": "DarkYellow",
    "gray": "Gray", "grey": "Gray", "darkgray": "DarkGray",
    "white": "White",
}


def _norm_color_name(s: str) -> str:
    return (s or "").strip().lower()


def _extract_color_commands(user_cmd: str, target: str) -> list[str]:
    """Build color-set commands for the given target ('cmd' or 'ps')."""
    cmds: list[str] = []
    try:
        s = user_cmd.lower()
        # foreground-only like: change color to red / set color blue
        m_fg = re.search(r"\b(?:change|set)\s+(?:text\s+)?color\s+(?:to\s+)?([a-z\s]+)\b", s)
        # explicit foreground/background like: set foreground red / set background black
        m_fg2 = re.search(r"\b(?:set|change)\s+(?:text\s+)?(?:foreground|text)\s+color\s+(?:to\s+)?([a-z\s]+)\b", s)
        m_bg = re.search(r"\b(?:set|change)\s+background\s+(?:color\s+)?(?:to\s+)?([a-z\s]+)\b", s)

        fg_name = _norm_color_name(m_fg.group(1)) if m_fg else None
        if m_fg2:
            fg_name = _norm_color_name(m_fg2.group(1))
        bg_name = _norm_color_name(m_bg.group(1)) if m_bg else None

        if not fg_name and not bg_name:
            return cmds

        if target == "cmd":
            # default black background if only fg requested
            bg_hex = _CMD_COLOR_MAP.get(bg_name, "0") if bg_name else "0"
            fg_hex = _CMD_COLOR_MAP.get(fg_name, None) if fg_name else None
            if not fg_hex:
                # default to bright white if only background specified
                fg_hex = "f"
            cmds.append(f"color {bg_hex}{fg_hex}".upper())
        else:
            ps_segs = []
            if fg_name:
                ps_color = _PS_COLOR_MAP.get(fg_name, "Green")
                ps_segs.append(f"$host.UI.RawUI.ForegroundColor = '{ps_color}'")
            if bg_name:
                ps_color = _PS_COLOR_MAP.get(bg_name, "Black")
                ps_segs.append(f"$host.UI.RawUI.BackgroundColor = '{ps_color}'")
                # Optional: refresh to apply bg more clearly
                ps_segs.append("Clear-Host")
            if ps_segs:
                cmds.append("; ".join(ps_segs))
    except Exception:
        return []
    return cmds


def _collect_actions(user_cmd: str, target: str) -> list[str]:
    """Collect terminal actions from a natural command string for target shell."""
    s = (user_cmd or "").lower()
    actions: list[str] = []

    # 1) pip upgrade
    if re.search(r"\b(update|upgrade)\s+pip\b", s):
        actions.append("python -m pip install --upgrade pip")

    # 2) install package(s)
    pkgs = re.findall(r"\b(?:install|download)\s+([a-z0-9_\-.]+)\b", s)
    for p in pkgs:
        # avoid generic words
        if p in {"library", "package", "packages", "libraries"}:
            continue
        actions.append(f"python -m pip install {p}")

    # 3) update/upgrade all packages
    if re.search(r"\b(update|upgrade)\s+(all\s+)?(libraries|packages|modules)\b", s):
        if target == "ps":
            actions.append(
                "python -m pip list --outdated --format=freeze | ForEach-Object { $_.Split('==')[0] } | ForEach-Object { python -m pip install -U $_ }"
            )
        else:
            actions.append(
                "for /F \"tokens=1 delims==\" %i in ('python -m pip list --outdated --format=freeze') do python -m pip install -U %i"
            )

    # 4) colors
    actions.extend(_extract_color_commands(s, target))

    return [a for a in actions if a]


def handle_control_command(command, lang="en"):
    command = command.lower().strip()
    user_name = "Abdul Rahman"
    
    # Terminal actions even without explicit "open ..."
    # e.g., "update all libraries", "upgrade pip", "install pyaudio", "change color to green"
    try:
        target = _best_terminal()
        actions_implicit = _collect_actions(command, target)
        if actions_implicit:
            if target == "cmd":
                cmdline = " && ".join(actions_implicit)
                subprocess.Popen(["cmd.exe", "/k", cmdline], shell=False)
                return f"Opening Command Prompt and executing: {cmdline}"
            else:
                ps_cmd = "; ".join(actions_implicit)
                subprocess.Popen(["powershell", "-NoExit", "-Command", ps_cmd], shell=False)
                return f"Opening PowerShell and executing: {ps_cmd}"
    except Exception as e:
        logging.error("Implicit terminal action error: %s", e)
    
    # Open Command Prompt / PowerShell/Terminal with optional actions (colors, pip upgrades, installs)
    # Examples:
    # - "open cmd"
    # - "open command prompt and change color to green"
    # - "open powershell and download pyaudio library"
    # - "open cmd and install pyaudio"
    # - "open terminal and update all libraries"
    # - "open cmd, upgrade pip and install pyaudio"
    try:
        open_cmd = any(p in command for p in ["open cmd", "open command prompt", "open command line"]) 
        open_ps = any(p in command for p in ["open powershell", "open power shell"]) 
        open_term = any(p in command for p in ["open terminal", "open the terminal", "open shell"]) 

        if open_cmd or open_ps or open_term:
            target = "cmd" if open_cmd else ("ps" if open_ps else _best_terminal())
            actions = _collect_actions(command, target)

            if target == "cmd":
                if actions:
                    cmdline = " && ".join(actions)
                    subprocess.Popen(["cmd.exe", "/k", cmdline], shell=False)
                    return f"Opening Command Prompt and executing: {cmdline}"
                subprocess.Popen(["cmd.exe"], shell=False)
                return f"Opening Command Prompt, {user_name}."
            else:
                if actions:
                    ps_cmd = "; ".join(actions)
                    subprocess.Popen(["powershell", "-NoExit", "-Command", ps_cmd], shell=False)
                    return f"Opening PowerShell and executing: {ps_cmd}"
                subprocess.Popen(["powershell"], shell=False)
                return f"Opening PowerShell, {user_name}."
    except Exception as e:
        logging.error("Terminal open/exec error: %s", e)
        # Fall through to other handlers
    
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