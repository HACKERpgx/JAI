# JAI Assistant Troubleshooting Guide

## 🔧 Common Issues & Solutions

### **Issue: "JAI server timed out. Please try again."**

**Symptoms:**
- Voice client shows timeout error
- Server stops responding after YouTube commands
- "Cannot connect to JAI server" messages

**Causes:**
1. yt-dlp taking too long to fetch video info
2. Network latency
3. Server process crashed

**Solutions:**

#### **Quick Fix: Disable yt-dlp Auto-Play**
Edit `.env` file and change:
```env
USE_YTDLP_AUTOPLAY=false
```

This will:
- ✅ Make YouTube commands instant (no delays)
- ✅ Prevent server timeouts
- ❌ Require manual click on first search result

#### **Restart JAI Server**
```powershell
# Stop current server (Ctrl+C)
# Then restart:
python jai_assistant.py
```

#### **Check Server Status**
```powershell
# In a new terminal:
curl http://localhost:8001/docs
# Should show FastAPI documentation page
```

---

### **Issue: YouTube Opens Search Instead of Video**

**Symptoms:**
- Message: "Opening YouTube: [song]. Click the top result to play."
- Search results page opens instead of direct video

**Causes:**
1. yt-dlp timeout (2.5 seconds)
2. Slow network connection
3. YouTube rate limiting
4. `USE_YTDLP_AUTOPLAY=false` in .env

**Solutions:**

#### **Enable yt-dlp (if disabled)**
Edit `.env`:
```env
USE_YTDLP_AUTOPLAY=true
```

#### **Check Network Speed**
```powershell
# Test YouTube connectivity
ping youtube.com
```

#### **Accept the Fallback**
- This is normal behavior when yt-dlp times out
- Just click the first search result (takes 1 second)
- Video will still load quickly

---

### **Issue: "Cannot connect to JAI server"**

**Symptoms:**
- All commands fail with connection error
- Voice client can't reach server

**Causes:**
1. Server not running
2. Server crashed
3. Port 8001 blocked
4. Wrong server URL

**Solutions:**

#### **Check if Server is Running**
```powershell
# Check if process exists
Get-Process -Name python | Where-Object {$_.MainWindowTitle -like "*jai*"}

# Or check port
netstat -ano | findstr :8001
```

#### **Restart Server**
```powershell
cd "C:\Users\Abdul Rahman\Documents\JAI_Assistant"
python jai_assistant.py
```

#### **Check Server Logs**
```powershell
Get-Content jai_assistant.log -Tail 20
```

---

### **Issue: Commands Work But Server Crashes After**

**Symptoms:**
- First command works
- Subsequent commands timeout
- Server becomes unresponsive

**Causes:**
1. yt-dlp blocking main thread
2. Memory leak
3. Threading issues

**Solutions:**

#### **Disable yt-dlp Auto-Play**
Edit `.env`:
```env
USE_YTDLP_AUTOPLAY=false
```

#### **Restart Server Regularly**
```powershell
# Create a restart script: restart_jai.ps1
while ($true) {
    python jai_assistant.py
    Start-Sleep -Seconds 2
}
```

---

### **Issue: Volume Control Not Working**

**Symptoms:**
- "Volume control not available"
- CoInitialize errors in logs

**Causes:**
1. pycaw not installed
2. COM initialization issue
3. No audio device

**Solutions:**

#### **Reinstall pycaw**
```powershell
pip uninstall pycaw
pip install pycaw
```

#### **Check Audio Device**
- Ensure speakers/headphones are connected
- Check Windows sound settings

---

### **Issue: Playback Controls (Play/Pause) Not Working**

**Symptoms:**
- "Requires pyautogui" error
- Controls don't affect media player

**Causes:**
1. pyautogui not installed
2. No media player running
3. Media player doesn't support media keys

**Solutions:**

#### **Install pyautogui**
```powershell
pip install pyautogui
```

#### **Test Media Keys**
- Open Spotify/YouTube
- Press media keys on keyboard manually
- If they don't work, player doesn't support them

---

### **Issue: "Close YouTube" Doesn't Work**

**Symptoms:**
- Browser stays open
- No error message

**Causes:**
1. YouTube not in Chrome
2. Different browser being used
3. Process name different

**Solutions:**

#### **Check Browser**
Edit `jai_controls.py` to match your browser:
```python
# For Firefox:
"youtube": "firefox.exe",

# For Edge:
"youtube": "msedge.exe",
```

#### **Manual Close**
```powershell
# Close Chrome manually:
taskkill /F /IM chrome.exe
```

---

## 🚀 Performance Optimization

### **For Fastest Response (Recommended)**

Edit `.env`:
```env
USE_YTDLP_AUTOPLAY=false
```

**Pros:**
- ✅ Instant response (< 1 second)
- ✅ No timeouts
- ✅ Server stays responsive

**Cons:**
- ❌ Must click first search result manually

### **For Auto-Play (Slower but Convenient)**

Edit `.env`:
```env
USE_YTDLP_AUTOPLAY=true
```

**Pros:**
- ✅ Videos auto-play 70-80% of time
- ✅ No manual clicking needed

**Cons:**
- ❌ 2-5 second delay
- ❌ Occasional timeouts on slow networks

---

## 📊 Diagnostic Commands

### **Test Media Controls**
```powershell
python test_media_controls.py
```

### **Test YouTube Play**
```powershell
python test_youtube_play.py
```

### **Check Server Health**
```powershell
# View recent logs
Get-Content jai_assistant.log -Tail 50

# Check for errors
Get-Content jai_assistant.log | Select-String "ERROR"
```

### **Test Single Command**
```powershell
python -c "from jai_media import handle_media_command; print(handle_media_command('play test on youtube'))"
```

---

## 🔍 Debug Mode

### **Enable Verbose Logging**

Edit `jai_assistant.py`:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

### **Monitor Server in Real-Time**
```powershell
# Terminal 1: Run server
python jai_assistant.py

# Terminal 2: Watch logs
Get-Content jai_assistant.log -Wait -Tail 10
```

---

## 💡 Best Practices

1. **Keep Server Running**
   - Don't restart unnecessarily
   - Use `Ctrl+C` to stop gracefully

2. **Use Text Mode for Testing**
   - Faster than voice mode
   - Easier to debug

3. **Monitor Logs**
   - Check logs after issues
   - Look for ERROR or WARNING messages

4. **Update Regularly**
   - Keep yt-dlp updated: `pip install --upgrade yt-dlp`
   - Update other packages: `pip install --upgrade -r requirements.txt`

5. **Network Matters**
   - Faster internet = better auto-play success
   - Use wired connection if possible

---

## 📞 Quick Reference

| Problem | Quick Fix |
|---------|-----------|
| Server timeout | Set `USE_YTDLP_AUTOPLAY=false` |
| Can't connect | Restart server |
| Volume not working | Reinstall pycaw |
| Playback controls fail | Install pyautogui |
| Close YouTube fails | Check browser name in code |

---

## ✅ Health Check Checklist

Before reporting issues, verify:

- [ ] Server is running (`python jai_assistant.py`)
- [ ] Port 8001 is accessible
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured correctly
- [ ] Network connection working
- [ ] No errors in `jai_assistant.log`

---

**Still having issues? Check the logs and restart the server!**
