#!/usr/bin/env python3
"""
Simple web interface that runs on the same JAI server port 8080
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

# Add this to your existing jai_assistant.py
# This creates a simple web interface on port 8080

def create_web_interface(app: FastAPI):
    """Add web interface to existing JAI app"""
    
    # HTML template for the interface
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>JAI Assistant - Voice Interface</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .logo { font-size: 2em; font-weight: bold; color: #2563eb; }
        .chat-section { margin-bottom: 20px; }
        .messages { height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; background: #fafafa; }
        .msg { margin: 5px 0; padding: 8px; border-radius: 5px; }
        .msg.you { background: #e3f2fd; text-align: right; }
        .msg.jai { background: #f3e5f5; text-align: left; }
        .input-section { display: flex; gap: 10px; margin-bottom: 20px; }
        .text-input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .send-btn { padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .voice-section { text-align: center; margin: 20px 0; }
        .voice-btn { padding: 15px 30px; font-size: 1.2em; background: #ff4444; color: white; border: none; border-radius: 10px; cursor: pointer; margin: 0 10px; }
        .voice-btn:disabled { background: #ccc; cursor: not-allowed; }
        .status { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .status.recording { background: #fff3cd; color: #856404; }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🤖 JAI Assistant</div>
            <p>Voice Interface on Port 8080</p>
        </div>
        
        <div class="chat-section">
            <div id="messages" class="messages"></div>
            <div class="input-section">
                <input type="text" id="textInput" class="text-input" placeholder="Type your command or use voice..." />
                <button id="sendBtn" class="send-btn">Send</button>
            </div>
        </div>
        
        <div class="voice-section">
            <div id="voiceStatus" class="status">Click Start Recording to begin</div>
            <button id="startRecBtn" class="voice-btn">🎤 Start Recording</button>
            <button id="stopRecBtn" class="voice-btn" disabled>⏹️ Stop</button>
        </div>
    </div>

    <script>
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;

        const messages = document.getElementById('messages');
        const textInput = document.getElementById('textInput');
        const sendBtn = document.getElementById('sendBtn');
        const startRecBtn = document.getElementById('startRecBtn');
        const stopRecBtn = document.getElementById('stopRecBtn');
        const voiceStatus = document.getElementById('voiceStatus');

        function addMessage(who, text) {
            const div = document.createElement('div');
            div.className = `msg ${who.toLowerCase()}`;
            div.textContent = `${who}: ${text}`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }

        function updateStatus(message, type = '') {
            voiceStatus.textContent = message;
            voiceStatus.className = `status ${type}`;
        }

        async function sendText() {
            const text = textInput.value.trim();
            if (!text) return;
            
            addMessage('You', text);
            textInput.value = '';
            
            try {
                const response = await fetch('/api/text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    addMessage('JAI', data.response || 'No response');
                } else {
                    addMessage('JAI', `Error: ${response.status}`);
                }
            } catch (error) {
                addMessage('JAI', `Error: ${error.message}`);
            }
        }

        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: { 
                        echoCancellation: true, 
                        noiseSuppression: true 
                    } 
                });
                
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = event => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = async () => {
                    updateStatus('Processing...', 'recording');
                    const blob = new Blob(audioChunks, { type: 'audio/webm' });
                    await sendAudio(blob);
                    
                    // Stop all tracks
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start();
                isRecording = true;
                
                startRecBtn.disabled = true;
                stopRecBtn.disabled = false;
                updateStatus('🎤 Recording... Speak now!', 'recording');
                
            } catch (error) {
                updateStatus(`❌ Error: ${error.message}`, 'error');
            }
        }

        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                isRecording = false;
                startRecBtn.disabled = false;
                stopRecBtn.disabled = true;
            }
        }

        async function sendAudio(blob) {
            try {
                const formData = new FormData();
                formData.append('file', blob, 'voice.webm');
                formData.append('lang', 'en-US');
                
                const response = await fetch('/api/voice', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.transcript) {
                        addMessage('You', data.transcript);
                    }
                    if (data.response) {
                        addMessage('JAI', data.response);
                        updateStatus('✅ Success!', 'success');
                    }
                } else {
                    updateStatus(`❌ Error: ${response.status}`, 'error');
                }
            } catch (error) {
                updateStatus(`❌ Upload Error: ${error.message}`, 'error');
            }
        }

        // Event listeners
        sendBtn.addEventListener('click', sendText);
        textInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendText();
        });
        
        startRecBtn.addEventListener('click', startRecording);
        stopRecBtn.addEventListener('click', stopRecording);

        // Keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'm') {
                e.preventDefault();
                if (!isRecording) {
                    startRecording();
                } else {
                    stopRecording();
                }
            }
        });

        // Welcome message
        addMessage('System', '🎤 JAI Voice Interface Ready! Click Start Recording or press Ctrl+M');
    </script>
</body>
</html>
    """
    
    # Add the web interface route
    @app.get("/", response_class=HTMLResponse)
    async def web_interface():
        return HTMLResponse(content=html_content)
    
    # Serve static files if needed
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
    
    return app

# Usage: Add this to the end of jai_assistant.py
# if __name__ == "__main__":
#     app = create_web_interface(app)
#     uvicorn.run(app, host="0.0.0.0", port=8080)
"""

def main():
    print("🌐 JAI Web Interface for Port 8080")
    print("=" * 50)
    print("This adds a web interface to your existing JAI server on port 8080")
    print()
    print("📋 Instructions:")
    print("1. Add this code to the end of jai_assistant.py:")
    print("   from jai_web_interface import create_web_interface")
    print("   app = create_web_interface(app)")
    print()
    print("2. Restart your JAI server:")
    print("   python jai_assistant.py")
    print()
    print("3. Open browser to: http://localhost:8080")
    print()
    print("🎯 Features:")
    print("- Text input and send")
    print("- Voice recording with microphone button")
    print("- Keyboard shortcut (Ctrl+M)")
    print("- Real-time chat interface")
    print("- All on the same port as JAI server (8080)")

if __name__ == "__main__":
    main()
