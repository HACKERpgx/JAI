# Music & YouTube Controls - JAI Assistant

## Overview
JAI Assistant now includes comprehensive music and YouTube controls with support for multiple streaming services and advanced playback management.

---

## 🎵 Music Playback Commands

### Generic Music Commands
These work with any active music player (Spotify, YouTube, Windows Media Player, etc.):

- **"play"** / **"pause"** / **"resume"** - Toggle play/pause
- **"next"** / **"next track"** / **"next song"** / **"skip"** - Skip to next track
- **"previous"** / **"previous track"** / **"previous song"** - Go to previous track
- **"stop"** / **"stop music"** / **"stop playback"** - Stop playback

### Play Specific Songs
- **"play music [song name]"** - Play a song on YouTube
- **"play song [song name]"** - Play a song on YouTube
- **"play music [song] by [artist]"** - Play specific song by artist

**Examples:**
```
"play music Bohemian Rhapsody"
"play song Shape of You by Ed Sheeran"
"play music Blinding Lights"
```

---

## 🎬 YouTube Controls

### Basic YouTube Commands
- **"open youtube"** - Open YouTube homepage
- **"play [query] on youtube"** - Play video on YouTube
- **"search youtube for [query]"** - Search YouTube
- **"youtube search [query]"** - Search YouTube

### Advanced YouTube Features
- **"youtube channel [name]"** - Open a YouTube channel
- **"open channel [name]"** - Open a YouTube channel
- **"youtube playlist [name]"** - Open a playlist
- **"play playlist [name]"** - Open a playlist

### YouTube Personal Playlists
- **"liked videos"** / **"liked songs"** - Open your liked videos
- **"watch later"** - Open your watch later playlist
- **"subscriptions"** - Open your subscriptions feed

**Examples:**
```
"play Despacito on youtube"
"search youtube for python tutorial"
"youtube channel MrBeast"
"play playlist chill vibes"
"open youtube and play liked videos"
"show me my watch later"
"open subscriptions"
```

---

## 🎧 Streaming Services

### Spotify
- **"play [song/artist] on spotify"** - Play on Spotify
- **"open spotify"** / **"start spotify"** - Open Spotify app/web

### Apple Music
- **"play [song/artist] on apple music"** - Play on Apple Music

### SoundCloud
- **"play [song/artist] on soundcloud"** - Play on SoundCloud

### YouTube Music
- **"play [song/artist] on youtube music"** - Play on YouTube Music

**Examples:**
```
"play The Weeknd on spotify"
"play Levitating on apple music"
"open spotify"
```

---

## 🔊 Volume Controls

### System Volume
- **"set volume to [0-100]"** - Set specific volume level
- **"volume [0-100]"** - Set specific volume level
- **"volume up"** / **"increase volume"** - Increase volume
- **"volume down"** / **"decrease volume"** - Decrease volume
- **"mute"** - Mute audio
- **"unmute"** - Unmute audio

**Examples:**
```
"set volume to 50"
"volume 75"
"volume up"
"mute"
```

---

## 🎮 How It Works

### Playback Controls
JAI uses Windows media keys to control playback. This works with:
- ✅ Spotify
- ✅ YouTube (in browser)
- ✅ Windows Media Player
- ✅ VLC Media Player
- ✅ iTunes/Apple Music
- ✅ Most other media players

### YouTube Integration
- Opens YouTube in your default browser
- Searches for the requested content
- User clicks the first result or selects from search results

### Streaming Services
- Opens the service in your default browser
- Searches for the requested song/artist
- User can select from search results

---

## 🛠️ Technical Details

### Classes Added to `jai_media.py`

1. **`YouTubeController`**
   - Enhanced with playlist and channel support
   - Tracks last search and current video
   - Music-specific search optimization

2. **`MusicStreamingController`**
   - Multi-service support (Spotify, Apple Music, SoundCloud, YouTube Music)
   - Direct app launching for Spotify
   - Web fallback for all services

3. **`PlaybackController`**
   - Keyboard simulation for media keys
   - Volume up/down controls
   - Stop functionality

4. **`MediaController`** (existing, unchanged)
   - System volume control via pycaw
   - Mute/unmute functionality

### Integration
- Media commands are handled **before** AI processing for instant response
- No API calls needed - all local/browser-based
- Works offline (except streaming services)

---

## 📋 Dependencies

All required packages are already in `requirements.txt`:
- `pyautogui==0.9.54` - Keyboard simulation for media keys
- `pycaw==20240210` - Windows volume control
- `requests==2.32.3` - HTTP requests (if needed)

---

## 🚀 Quick Start

1. **Start JAI Server:**
   ```powershell
   python jai_assistant.py
   ```

2. **Start Voice Client:**
   ```powershell
   python voice_client.py
   ```

3. **Try Commands:**
   - "play Imagine Dragons on spotify"
   - "play Bohemian Rhapsody on youtube"
   - "next track"
   - "set volume to 60"
   - "pause"

---

## 💡 Tips

1. **For best results with YouTube:**
   - Include artist name for better search results
   - Use "official audio" or "official video" for original versions

2. **Playback controls work globally:**
   - No need to specify which app
   - Controls whatever is currently playing

3. **Volume controls:**
   - "set volume to X" for precise control
   - "volume up/down" for quick adjustments
   - "mute" for instant silence

4. **Streaming services:**
   - First time may require login
   - Browser will remember your session
   - Spotify app opens if installed, otherwise web player

---

## 🐛 Troubleshooting

### Playback controls not working?
- Install pyautogui: `pip install pyautogui`
- Make sure a media player is open and playing

### Volume control not working?
- Install pycaw: `pip install pycaw`
- Windows only - requires audio device

### YouTube not opening?
- Check default browser settings
- Ensure internet connection

### Spotify app not opening?
- Install Spotify desktop app
- Falls back to web player automatically

---

## 🎯 Future Enhancements

Potential additions:
- [ ] Direct YouTube API integration for auto-play
- [ ] Spotify API for direct playback control
- [ ] Queue management
- [ ] Playlist creation
- [ ] Lyrics fetching
- [ ] Now playing information
- [ ] Music recommendations

---

## 📝 Example Conversation

```
You: "activate aj"
AJ: "Yes, I'm here!"

You: "play some music"
AJ: "Please specify a song name"

You: "play Blinding Lights by The Weeknd"
AJ: "Playing on YouTube: Blinding Lights The Weeknd official audio"

You: "volume 50"
AJ: "Volume set to 50%"

You: "next"
AJ: "Skipped to next track"

You: "pause"
AJ: "Toggled play/pause"
```

---

**Enjoy your enhanced music experience with JAI! 🎵**
