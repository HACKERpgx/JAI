#!/usr/bin/env python3
"""
Clean JAI web interface without animations - to replace the existing one
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import os

def get_clean_interface():
    """Return clean HTML without animations"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>JAI Assistant - Clean Interface</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; padding: 20px; 
            background: #f5f5f5; 
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
        }
        .logo { 
            font-size: 2em; 
            font-weight: bold; 
            color: #2563eb; 
            margin-bottom: 10px;
        }
        .chat-section { 
            margin-bottom: 20px; 
        }
        .messages { 
            height: 300px; 
            overflow-y: auto; 
            border: 1px solid #ddd; 
            padding: 10px; 
            margin-bottom: 10px; 
            background: #fafafa; 
        }
        .msg { 
            margin: 5px 0; 
            padding: 8px; 
            border-radius: 5px; 
            clear: both;
        }
        .msg.you { 
            background: #e3f2fd; 
            text-align: right; 
        }
        .msg.jai { 
            background: #f3e5f5; 
            text-align: left; 
        }
        .input-section { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 20px; 
        }
        .text-input { 
            flex: 1; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            font-size: 14px;
        }
        .send-btn { 
            padding: 10px 20px; 
            background: #2563eb; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 14px;
        }
        .voice-section { 
            text-align: center; 
            margin: 20px 0; 
        }
        .voice-btn { 
            padding: 15px 30px; 
            font-size: 1.1em; 
            background: #2563eb; 
            color: white; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            margin: 0 5px; 
            transition: all 0.2s;
        }
        .voice-btn:hover {
            background: #1d4ed8;
            transform: scale(1.05);
        }
        .voice-btn:disabled { 
            background: #ccc; 
            cursor: not-allowed; 
            transform: scale(1);
        }
        .status { 
            margin: 15px 0; 
            padding: 12px; 
            border-radius: 5px; 
            font-weight: bold; 
            font-size: 14px;
        }
        .status.recording { 
            background: #fff3cd; 
            color: #856404; 
            border: 2px solid #ffeaa7; 
        }
        .status.success { 
            background: #d4edda; 
            color: #155724; 
            border: 2px solid #c3e6cb; 
        }
        .status.error { 
            background: #f8d7da; 
            color: #721c24; 
            border: 2px solid #f5c6cb; 
        }
        .status.processing { 
            background: #e2e3e5; 
            color: #383d41; 
            border: 2px solid #d6d8db; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🤖 JAI Assistant</div>
            <p style="color: #666; margin: 0;">Clean Voice Interface - No Animations</p>
        </div>
        
        <div class="chat-section">
            <div id="messages" class="messages"></div>
            <div class="input-section">
                <input type="text" id="textInput" class="text-input" placeholder="Type your command or use voice..." />
                <button id="sendBtn" class="send-btn">Send</button>
            </div>
        </div>
        
        <div class="voice-section">
            <div id="voiceStatus" class="status">Ready - Click Start Recording</div>
            <button id="startRecBtn" class="voice-btn">🎤 Start</button>
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
                updateStatus('Requesting microphone...', 'processing');
                
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
                    updateStatus('Processing audio...', 'processing');
                    const blob = new Blob(audioChunks, { type: 'audio/webm' });
                    await sendAudio(blob);
                    
                    // Stop all tracks
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start();
                isRecording = true;
                
                startRecBtn.disabled = true;
                stopRecBtn.disabled = false;
                updateStatus('🎤 Recording - Speak clearly', 'recording');
                
            } catch (error) {
                updateStatus(`Microphone Error: ${error.message}`, 'error');
                console.error('Microphone error:', error);
            }
        }

        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                isRecording = false;
                startRecBtn.disabled = false;
                stopRecBtn.disabled = true;
                updateStatus('Ready - Click Start Recording', '');
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
                        updateStatus('✅ Success - Ready for next command', 'success');
                    }
                } else {
                    updateStatus(`Server Error: ${response.status}`, 'error');
                }
            } catch (error) {
                updateStatus(`Upload Error: ${error.message}`, 'error');
                console.error('Upload error:', error);
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
        addMessage('System', '🎤 JAI Ready - Use voice or text input');
        updateStatus('Ready - Click Start Recording or press Ctrl+M', '');
    </script>
</body>
</html>
    """

def add_clean_interface_to_app(app: FastAPI):
    """Replace the existing web interface with clean version"""
    
    @app.get("/", response_class=HTMLResponse)
    async def clean_web_interface():
        return HTMLResponse(content=get_clean_interface())
    
    return app

# Instructions to use
def main():
    print("🧹 JAI Clean Web Interface")
    print("=" * 50)
    print("This replaces the current web interface with a clean version")
    print("No animations, no SVG elements, no loading issues")
    print()
    print("📋 To apply:")
    print("1. Add this to jai_assistant.py:")
    print("   from jai_web_clean import add_clean_interface_to_app")
    print("   app = add_clean_interface_to_app(app)")
    print()
    print("2. Restart JAI server:")
    print("   python jai_assistant.py")
    print()
    print("3. Open browser:")
    print("   http://localhost:8080")
    print()
    print("✅ Features:")
    print("- Clean interface without animations")
    print("- Simple status messages")
    print("- Better button styling")
    print("- Clear error messages")
    print("- Same functionality, cleaner design")

if __name__ == "__main__":
    main()
