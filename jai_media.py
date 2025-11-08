# jai_media.py
"""
Media control module for JAI.
Handles system volume, playback control, YouTube integration, and music streaming.
"""
import logging
import subprocess
import webbrowser
import re
import time
import threading
from typing import Optional, Dict, List

# Volume control (Windows)
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL, CoInitialize
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except Exception as e:
    PYCAW_AVAILABLE = False
    logging.warning("pycaw/comtypes not available: %s", e)


class MediaController:
    """Controls system media and volume."""
    
    def __init__(self):
        self.volume_interface = None
        if PYCAW_AVAILABLE:
            try:
                try:
                    CoInitialize()
                except Exception as e:
                    logging.warning("COM initialization warning: %s", e)
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
            except Exception as e:
                logging.error("Failed to initialize volume control: %s", e)
    
    def set_volume(self, level: int) -> str:
        """
        Set system volume (0-100).
        
        Args:
            level: Volume level (0-100)
            
        Returns:
            Status message
        """
        if not self.volume_interface:
            return "Volume control not available"
        
        try:
            # Clamp to 0-100
            level = max(0, min(100, level))
            # Convert to scalar (0.0 to 1.0)
            scalar = level / 100.0
            self.volume_interface.SetMasterVolumeLevelScalar(scalar, None)
            return f"Volume set to {level}%"
        except Exception as e:
            logging.error("Failed to set volume: %s", e)
            return f"Failed to set volume: {str(e)}"
    
    def get_volume(self) -> Optional[int]:
        """Get current system volume (0-100)."""
        if not self.volume_interface:
            return None
        
        try:
            scalar = self.volume_interface.GetMasterVolumeLevelScalar()
            return int(scalar * 100)
        except Exception as e:
            logging.error("Failed to get volume: %s", e)
            return None
    
    def mute(self) -> str:
        """Mute system audio."""
        if self.volume_interface:
            try:
                self.volume_interface.SetMute(1, None)
                return "Audio muted"
            except Exception as e:
                return f"Failed to mute: {str(e)}"
        # Fallback: simulate keyboard mute if volume interface not available
        try:
            import pyautogui
            pyautogui.press('volumemute')
            return "Audio muted"
        except ImportError:
            return "Volume control not available"
        except Exception as e:
            return f"Failed to mute: {str(e)}"
    
    def unmute(self) -> str:
        """Unmute system audio."""
        if self.volume_interface:
            try:
                self.volume_interface.SetMute(0, None)
                return "Audio unmuted"
            except Exception as e:
                return f"Failed to unmute: {str(e)}"
        # Fallback: simulate keyboard mute (toggle) to likely unmute
        try:
            import pyautogui
            pyautogui.press('volumemute')
            return "Audio unmuted"
        except ImportError:
            return "Volume control not available"
        except Exception as e:
            return f"Failed to unmute: {str(e)}"
    
    def is_muted(self) -> bool:
        """Check if audio is muted."""
        if not self.volume_interface:
            return False
        
        try:
            return bool(self.volume_interface.GetMute())
        except Exception:
            return False


class YouTubeController:
    """Controls YouTube playback via browser with advanced features."""
    
    def __init__(self, use_ytdlp: bool = True):
        self.last_search = None
        self.current_video = None
        self.use_ytdlp = use_ytdlp  # Can disable yt-dlp for reliability
    
    def _open_url(self, url: str) -> bool:
        """Robustly open a URL on Windows using Shell (more reliable than webbrowser.open)."""
        try:
            subprocess.Popen(["cmd", "/c", "start", "", url], shell=True)
            return True
        except Exception as e:
            logging.error("Open URL failed: %s", e)
            return False
    
    def search(self, query: str) -> str:
        """
        Search YouTube and open results in browser.
        
        Args:
            query: Search query
            
        Returns:
            Status message
        """
        try:
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            self._open_url(search_url)
            self.last_search = query
            return f"Searching YouTube for: {query}"
        except Exception as e:
            logging.error("YouTube search failed: %s", e)
            return f"Failed to search YouTube: {str(e)}"
    
    def play(self, query: str, auto_play: bool = True) -> str:
        """
        Search and play first YouTube result.
        Uses fast yt-dlp lookup with timeout protection.
        
        Args:
            query: Search query
            auto_play: If True, attempts to get direct video link
            
        Returns:
            Status message
        """
        # Clean up the query - remove common phrases
        query = self._clean_query(query)
        
        if not auto_play:
            # Simple search mode (fast and reliable)
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            self._open_url(search_url)
            self.current_video = query
            return f"Searching YouTube for: {query}"

        # If yt-dlp disabled, use instant search
        if not self.use_ytdlp:
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            self._open_url(search_url)
            self.current_video = query
            return f"Playing on YouTube: {query}. Opening search - click first result."

        # Try fast yt-dlp lookup with strict timeout
        result_container = {'url': None, 'error': None, 'done': False}

        def fetch_video_url():
            """Fetch video URL in background thread with timeout protection."""
            try:
                import yt_dlp
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'skip_download': True,
                    'socket_timeout': 3,
                    'default_search': 'ytsearch1',
                    'nocheckcertificate': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                    if info and 'entries' in info and len(info['entries']) > 0:
                        video_id = info['entries'][0]['id']
                        result_container['url'] = f"https://www.youtube.com/watch?v={video_id}"
                        result_container['done'] = True
                    else:
                        result_container['error'] = "No results"
                        result_container['done'] = True
            except Exception as e:
                result_container['error'] = str(e)
                result_container['done'] = True

        thread = threading.Thread(target=fetch_video_url, daemon=True)
        thread.start()
        thread.join(timeout=2.5)

        if result_container.get('url'):
            self._open_url(result_container['url'])
            self.current_video = query
            logging.info(f"Auto-playing YouTube video for: {query}")
            return f"Playing on YouTube: {query}"
        else:
            # Immediate fallback to search (don't wait for thread)
            logging.warning("yt-dlp timeout or failed, using instant search fallback")
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            self._open_url(search_url)
            self.current_video = query
            return f"Opening YouTube: {query}. Click the top result to play."
            
    def _clean_query(self, query: str) -> str:
        """Clean up search queries by removing common phrases."""
        # Remove common phrases that might be in the command
        phrases_to_remove = [
            'search', 'on youtube', 'play', 'the song', 'song', 'video',
            'youtube', 'please', 'can you', 'could you', 'would you',
            'for me', 'thanks', 'thank you'
        ]
        
        # Create a case-insensitive pattern
        pattern = re.compile('|'.join(map(re.escape, phrases_to_remove)), re.IGNORECASE)
        cleaned = pattern.sub('', query).strip()
        
        # Remove extra spaces
        cleaned = ' '.join(cleaned.split())
        
        return cleaned or query  # Return original if we end up with empty string
        
        # If yt-dlp disabled, use instant search
        if not self.use_ytdlp:
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            self.current_video = query
            return f"Playing on YouTube: {query}. Opening search - click first result."
        
        # Try fast yt-dlp lookup with aggressive timeout
        result_container = {'url': None, 'error': None, 'done': False}
        
        def fetch_video_url():
            """Fetch video URL in background thread with timeout protection."""
            try:
                import yt_dlp
                import signal
                
                # Set alarm for hard timeout (Unix-like systems)
                # For Windows, we rely on thread timeout
                
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'skip_download': True,
                    'socket_timeout': 3,  # Reduced to 3 seconds
                    'default_search': 'ytsearch1',
                    'nocheckcertificate': True,  # Skip SSL verification for speed
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                    if info and 'entries' in info and len(info['entries']) > 0:
                        video_id = info['entries'][0]['id']
                        result_container['url'] = f"https://www.youtube.com/watch?v={video_id}"
                        result_container['done'] = True
                    else:
                        result_container['error'] = "No results"
                        result_container['done'] = True
            except Exception as e:
                result_container['error'] = str(e)
                result_container['done'] = True
        
        # Start background thread with strict timeout
        thread = threading.Thread(target=fetch_video_url, daemon=True)
        thread.start()
        thread.join(timeout=2.5)  # Reduced to 2.5 seconds for faster response
        
        # Check if we got a result quickly
        if result_container.get('url'):
            webbrowser.open(result_container['url'])
            self.current_video = query
            logging.info(f"Auto-playing YouTube video for: {query}")
            return f"Playing on YouTube: {query}"
        else:
            # Immediate fallback to search (don't wait for thread)
            logging.warning(f"yt-dlp timeout or failed, using instant search fallback")
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            webbrowser.open(search_url)
            self.current_video = query
            return f"Opening YouTube: {query}. Click the top result to play."
    
    def play_music(self, song: str, artist: str = None) -> str:
        """
        Play music on YouTube.
        
        Args:
            song: Song name
            artist: Optional artist name
            
        Returns:
            Status message
        """
        try:
            if artist:
                query = f"{song} {artist} official audio"
            else:
                query = f"{song} official audio"
            return self.play(query)
        except Exception as e:
            return f"Failed to play music: {str(e)}"
    
    def open_url(self, url: str) -> str:
        """
        Open a specific YouTube URL.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Status message
        """
        try:
            webbrowser.open(url)
            return f"Opening: {url}"
        except Exception as e:
            return f"Failed to open URL: {str(e)}"
    
    def open_channel(self, channel_name: str) -> str:
        """
        Open a YouTube channel.
        
        Args:
            channel_name: Channel name to search for
            
        Returns:
            Status message
        """
        try:
            search_url = f"https://www.youtube.com/results?search_query={channel_name.replace(' ', '+')}+channel"
            webbrowser.open(search_url)
            return f"Opening YouTube channel: {channel_name}"
        except Exception as e:
            return f"Failed to open channel: {str(e)}"
    
    def play_playlist(self, playlist_name: str) -> str:
        """
        Search and open a YouTube playlist.
        
        Args:
            playlist_name: Playlist name
            
        Returns:
            Status message
        """
        try:
            search_url = f"https://www.youtube.com/results?search_query={playlist_name.replace(' ', '+')}+playlist"
            webbrowser.open(search_url)
            return f"Opening playlist: {playlist_name}"
        except Exception as e:
            return f"Failed to open playlist: {str(e)}"
    
    @staticmethod
    def open_liked_videos() -> str:
        """
        Open YouTube liked videos page.
        
        Returns:
            Status message
        """
        try:
            webbrowser.open("https://www.youtube.com/playlist?list=LL")
            return "Opening your liked videos on YouTube"
        except Exception as e:
            return f"Failed to open liked videos: {str(e)}"
    
    @staticmethod
    def open_watch_later() -> str:
        """
        Open YouTube watch later playlist.
        
        Returns:
            Status message
        """
        try:
            webbrowser.open("https://www.youtube.com/playlist?list=WL")
            return "Opening your watch later playlist"
        except Exception as e:
            return f"Failed to open watch later: {str(e)}"
    
    @staticmethod
    def open_subscriptions() -> str:
        """
        Open YouTube subscriptions feed.
        
        Returns:
            Status message
        """
        try:
            webbrowser.open("https://www.youtube.com/feed/subscriptions")
            return "Opening your YouTube subscriptions"
        except Exception as e:
            return f"Failed to open subscriptions: {str(e)}"
    
    @staticmethod
    def close_browser() -> str:
        """
        Close Chrome browser (where YouTube typically runs).
        
        Returns:
            Status message
        """
        try:
            # Try to close Chrome
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], 
                         capture_output=True, shell=True, timeout=5)
            return "Closed YouTube (Chrome browser)"
        except subprocess.TimeoutExpired:
            return "Browser close timed out"
        except Exception as e:
            logging.error("Failed to close browser: %s", e)
            return f"Failed to close browser: {str(e)}"


class MusicStreamingController:
    """Controls music streaming services."""
    
    SERVICES = {
        "spotify": "https://open.spotify.com/search/{query}",
        "apple music": "https://music.apple.com/search?term={query}",
        "soundcloud": "https://soundcloud.com/search?q={query}",
        "youtube music": "https://music.youtube.com/search?q={query}"
    }
    
    @staticmethod
    def play_on_service(query: str, service: str = "spotify") -> str:
        """
        Play music on a specific streaming service.
        
        Args:
            query: Song/artist to search for
            service: Streaming service name
            
        Returns:
            Status message
        """
        service_lower = service.lower()
        if service_lower not in MusicStreamingController.SERVICES:
            return f"Service '{service}' not supported. Available: {', '.join(MusicStreamingController.SERVICES.keys())}"
        
        try:
            url = MusicStreamingController.SERVICES[service_lower].format(query=query.replace(' ', '+'))
            webbrowser.open(url)
            return f"Opening {service}: {query}"
        except Exception as e:
            logging.error("Failed to open %s: %s", service, e)
            return f"Failed to open {service}: {str(e)}"
    
    @staticmethod
    def open_spotify() -> str:
        """Open Spotify app or web player."""
        try:
            # Try to open Spotify app
            subprocess.Popen(["spotify.exe"], shell=True)
            return "Opening Spotify"
        except Exception:
            # Fallback to web player
            webbrowser.open("https://open.spotify.com")
            return "Opening Spotify web player"


class PlaybackController:
    """Advanced playback controls using keyboard simulation."""
    
    @staticmethod
    def play_pause() -> str:
        """Toggle play/pause."""
        try:
            import pyautogui
            pyautogui.press('playpause')
            return "Toggled play/pause"
        except ImportError:
            return "Requires pyautogui. Install: pip install pyautogui"
        except Exception as e:
            return f"Failed: {str(e)}"
    
    @staticmethod
    def next_track() -> str:
        """Skip to next track."""
        try:
            import pyautogui
            pyautogui.press('nexttrack')
            return "Skipped to next track"
        except ImportError:
            return "Requires pyautogui"
        except Exception as e:
            return f"Failed: {str(e)}"
    
    @staticmethod
    def previous_track() -> str:
        """Go to previous track."""
        try:
            import pyautogui
            pyautogui.press('prevtrack')
            return "Went to previous track"
        except ImportError:
            return "Requires pyautogui"
        except Exception as e:
            return f"Failed: {str(e)}"
    
    @staticmethod
    def stop() -> str:
        """Stop playback."""
        try:
            import pyautogui
            pyautogui.press('stop')
            return "Stopped playback"
        except ImportError:
            return "Requires pyautogui"
        except Exception as e:
            return f"Failed: {str(e)}"
    
    @staticmethod
    def volume_up() -> str:
        """Increase volume."""
        try:
            import pyautogui
            pyautogui.press('volumeup')
            return "Volume increased"
        except ImportError:
            return "Requires pyautogui"
        except Exception as e:
            return f"Failed: {str(e)}"
    
    @staticmethod
    def volume_down() -> str:
        """Decrease volume."""
        try:
            import pyautogui
            pyautogui.press('volumedown')
            return "Volume decreased"
        except ImportError:
            return "Requires pyautogui"
        except Exception as e:
            return f"Failed: {str(e)}"


def handle_media_command(command: str) -> Optional[str]:
    """
    Handle media-related commands with enhanced music/YouTube controls.
    
    Args:
        command: User command
        
    Returns:
        Response string or None if not a media command
    """
    import os
    command_lower = command.lower().strip()
    media = MediaController()
    
    # Check if yt-dlp auto-play is enabled
    use_ytdlp = os.environ.get("USE_YTDLP_AUTOPLAY", "true").lower() in {"1", "true", "yes", "on"}
    youtube = YouTubeController(use_ytdlp=use_ytdlp)
    
    music = MusicStreamingController()
    playback = PlaybackController()
    
    # ===== VOLUME CONTROLS =====
    if "set volume to" in command_lower or ("volume" in command_lower and any(c.isdigit() for c in command)):
        try:
            match = re.search(r'(\d+)', command_lower)
            if match:
                level = int(match.group(1))
                return media.set_volume(level)
            else:
                current = media.get_volume()
                if current is not None:
                    return f"Current volume is {current}%"
                return "Please specify a volume level (0-100)"
        except Exception as e:
            return f"Volume command failed: {str(e)}"
    
    if "volume up" in command_lower or "increase volume" in command_lower:
        return playback.volume_up()
    
    if "volume down" in command_lower or "decrease volume" in command_lower:
        return playback.volume_down()
    
    if "mute" in command_lower and "unmute" not in command_lower:
        return media.mute()
    
    if "unmute" in command_lower:
        return media.unmute()
    
    # ===== YOUTUBE CONTROLS =====
    # Check for music/song search first
    if any(phrase in command_lower for phrase in ['search', 'play']) and \
       any(term in command_lower for term in ['song', 'music', 'track', 'artist']):
        # Extract the search query using word-boundary cleanup
        query = re.sub(r'\b(?:search|play|the|a|on|youtube|for|me|please)\b', ' ', command_lower)
        query = ' '.join(query.split())
        # Add 'official audio' for better music results
        query = f"{query} official audio"
        return youtube.play(query, auto_play=True)
        
    # Check for special playlists (before general play commands)
    if "liked videos" in command_lower or "liked songs" in command_lower or "like videos" in command_lower:
        return youtube.open_liked_videos()
    
    if "watch later" in command_lower:
        return youtube.open_watch_later()
    
    if "subscriptions" in command_lower or "subscription feed" in command_lower:
        return youtube.open_subscriptions()
    
    # General YouTube commands
    if "play" in command_lower and "youtube" in command_lower:
        # Extract query after "play" and before/after "youtube"
        match = re.search(r'play\s+(.+?)\s+(?:on\s+)?youtube', command_lower)
        if not match:
            match = re.search(r'youtube\s+(.+)', command_lower)
        if match:
            query = match.group(1).strip()
            return youtube.play(query)
        return "Please specify what to play on YouTube"
    
    if "search youtube" in command_lower or "youtube search" in command_lower:
        match = re.search(r'(?:search youtube for|youtube search)\s+(.+)', command_lower)
        if match:
            query = match.group(1).strip()
            return youtube.search(query)
        return "Please specify a search query"
    
    if "open youtube" in command_lower:
        # Check if it's asking for liked videos
        if "liked" in command_lower:
            return youtube.open_liked_videos()
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube"
    
    if "youtube channel" in command_lower or "open channel" in command_lower:
        match = re.search(r'(?:youtube channel|open channel)\s+(.+)', command_lower)
        if match:
            channel = match.group(1).strip()
            return youtube.open_channel(channel)
        return "Please specify a channel name"
    
    if "youtube playlist" in command_lower or "play playlist" in command_lower:
        match = re.search(r'(?:youtube playlist|play playlist)\s+(.+)', command_lower)
        if match:
            playlist = match.group(1).strip()
            return youtube.play_playlist(playlist)
        return "Please specify a playlist name"
    
    if "close youtube" in command_lower or "close browser" in command_lower:
        return youtube.close_browser()
    
    # ===== MUSIC STREAMING SERVICES =====
    if "play" in command_lower and any(service in command_lower for service in ["spotify", "apple music", "soundcloud"]):
        for service in music.SERVICES.keys():
            if service in command_lower:
                match = re.search(rf'play\s+(.+?)\s+(?:on\s+)?{service}', command_lower)
                if not match:
                    match = re.search(r'play\s+(.+)', command_lower)
                if match:
                    query = match.group(1).replace(f"on {service}", "").replace(service, "").strip()
                    return music.play_on_service(query, service)
                return f"Please specify what to play on {service}"
    
    if "open spotify" in command_lower or "start spotify" in command_lower:
        return music.open_spotify()
    
    # ===== MUSIC PLAYBACK (Generic - works with any player) =====
    if "play music" in command_lower or "play song" in command_lower:
        match = re.search(r'play (?:music|song)\s+(.+?)(?:\s+by\s+(.+))?$', command_lower)
        if match:
            song = match.group(1).strip()
            artist = match.group(2).strip() if match.group(2) else None
            return youtube.play_music(song, artist)
        return "Please specify a song name"
    
    # ===== PLAYBACK CONTROLS =====
    if ("pause" in command_lower) or (command_lower.strip() in ["play", "play pause", "resume"]):
        return playback.play_pause()
    
    if "next" in command_lower and ("track" in command_lower or "song" in command_lower or command_lower == "next"):
        return playback.next_track()
    
    if "previous" in command_lower and ("track" in command_lower or "song" in command_lower or command_lower == "previous"):
        return playback.previous_track()
    
    if "stop" in command_lower and ("music" in command_lower or "playback" in command_lower or command_lower == "stop"):
        return playback.stop()
    
    if "skip" in command_lower:
        return playback.next_track()
    
    return None


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test volume control
    media = MediaController()
    print(f"Current volume: {media.get_volume()}%")
    print(media.set_volume(50))
    print(f"Muted: {media.is_muted()}")
    
    # Test YouTube
    youtube = YouTubeController()
    # youtube.search("python tutorial")
