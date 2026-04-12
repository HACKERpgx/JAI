(function(){
  // Global variables for elements
  let apiBaseInput, saveBaseBtn, healthBtn, healthStatus, messages, textInput, sendBtn;
  let startRecBtn, stopRecBtn, voiceLang, voiceStatus;
  let isRecording = false;

  const LS_KEY = 'jai_api_base';
  const SESSION_KEY = 'jai_session_id';
  const MESSAGES_KEY = 'jai_messages';
  const SYNC_CHANNEL = 'jai_sync_channel';
  
  // Cross-tab sync variables
  let currentSessionId = null;
  let lastMessageTimestamp = null;
  let syncPollingInterval = null;
  
  // Initialize all DOM element references
  function initializeElements() {
    apiBaseInput = document.getElementById('apiBase');
    saveBaseBtn = document.getElementById('saveBase');
    healthBtn = document.getElementById('healthBtn');
    healthStatus = document.getElementById('healthStatus');
    messages = document.getElementById('messages');
    textInput = document.getElementById('textInput');
    sendBtn = document.getElementById('sendBtn');
    startRecBtn = document.getElementById('startRecBtn');
    stopRecBtn = document.getElementById('stopRecBtn');
    voiceLang = document.getElementById('voiceLang');
    voiceStatus = document.getElementById('voiceStatus');
    
    // Log element initialization
    console.log('Elements initialized:', {
      apiBaseInput: !!apiBaseInput,
      saveBaseBtn: !!saveBaseBtn,
      healthBtn: !!healthBtn,
      startRecBtn: !!startRecBtn,
      stopRecBtn: !!stopRecBtn,
      voiceLang: !!voiceLang,
      voiceStatus: !!voiceStatus
    });
  }
  
  function getBase(){ return apiBaseInput ? apiBaseInput.value.trim() : 'https://j-ai.top'; }
  function setBase(v){ apiBaseInput.value = v; }
  function loadBase(){ setBase(localStorage.getItem(LS_KEY) || 'https://j-ai.top'); }
  function saveBase(){ localStorage.setItem(LS_KEY, getBase()); }

  // Cross-tab synchronization functions
  function initializeSession() {
    currentSessionId = localStorage.getItem(SESSION_KEY) || generateSessionId();
    localStorage.setItem(SESSION_KEY, currentSessionId);
    return currentSessionId;
  }

  function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  function saveMessagesToStorage(messages) {
    try {
      localStorage.setItem(MESSAGES_KEY, JSON.stringify({
        sessionId: currentSessionId,
        messages: messages,
        lastUpdated: Date.now()
      }));
    } catch (e) {
      console.error('Failed to save messages to localStorage:', e);
    }
  }

  function loadMessagesFromStorage() {
    try {
      const stored = localStorage.getItem(MESSAGES_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        if (data.sessionId === currentSessionId) {
          return data.messages || [];
        }
      }
    } catch (e) {
      console.error('Failed to load messages from localStorage:', e);
    }
    return [];
  }

  function triggerSyncEvent(messageData) {
    // Use localStorage event to notify other tabs
    const syncData = {
      type: 'message_added',
      sessionId: currentSessionId,
      message: messageData,
      timestamp: Date.now()
    };
    
    localStorage.setItem(SYNC_CHANNEL, JSON.stringify(syncData));
    // Remove the item to trigger the storage event in other tabs
    localStorage.removeItem(SYNC_CHANNEL);
  }

  function handleStorageEvent(event) {
    if (event.key === SYNC_CHANNEL && event.newValue) {
      try {
        const syncData = JSON.parse(event.newValue);
        if (syncData.type === 'message_added' && syncData.sessionId === currentSessionId) {
          // Another tab added a message, fetch latest from server
          fetchLatestMessages();
        }
      } catch (e) {
        console.error('Failed to parse sync data:', e);
      }
    }
  }

  async function fetchLatestMessages() {
    if (!currentSessionId) return;
    
    try {
      const response = await fetch(getBase() + '/api/messages/' + currentSessionId);
      if (response.ok) {
        const data = await response.json();
        if (data.messages && data.messages.length > 0) {
          updateMessagesDisplay(data.messages);
          saveMessagesToStorage(data.messages);
        }
      }
    } catch (e) {
      console.error('Failed to fetch latest messages:', e);
    }
  }

  function updateMessagesDisplay(serverMessages) {
    if (!serverMessages || !Array.isArray(serverMessages)) return;
    
    // Clear current messages
    messages.innerHTML = '';
    
    // Add messages from server
    serverMessages.forEach(msg => {
      const who = msg.role === 'user' ? 'You' : 'JAI';
      addMsg(who, msg.content);
    });
  }

  function startSyncPolling() {
    // Poll for new messages every 5 seconds
    if (syncPollingInterval) {
      clearInterval(syncPollingInterval);
    }
    
    syncPollingInterval = setInterval(() => {
      fetchLatestMessages();
    }, 5000);
  }

  function stopSyncPolling() {
    if (syncPollingInterval) {
      clearInterval(syncPollingInterval);
      syncPollingInterval = null;
    }
  }

  function addMsg(who, text){
    const div = document.createElement('div');
    div.className = 'msg ' + (who === 'You' ? 'you' : 'jai');
    div.textContent = (who + ': ' + text);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  async function checkHealth(){
    healthStatus.textContent = 'Checking…';
    try{
      const res = await fetch(getBase() + '/api/health');
      if(!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      healthStatus.textContent = data.ok ? ('OK ' + (data.time || '')) : 'Not OK';
    }catch(e){
      healthStatus.textContent = 'Error';
    }
  }

  async function sendText(){
    const text = textInput.value.trim();
    if(!text) return;
    
    if (!currentSessionId) {
      initializeSession();
    }
    
    addMsg('You', text);
    textInput.value = '';
    
    try{
      const res = await fetch(getBase() + '/api/text', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Session-ID': currentSessionId
        },
        body: JSON.stringify({ text })
      });
      if(!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      
      // Update session ID if server returned a new one
      if (data.sessionId && data.sessionId !== currentSessionId) {
        currentSessionId = data.sessionId;
        localStorage.setItem(SESSION_KEY, currentSessionId);
      }
      
      addMsg('JAI', data.response || '');
      
      // Trigger sync event for other tabs
      triggerSyncEvent({
        role: 'user',
        content: text,
        timestamp: Date.now()
      });
      
      // Also trigger for the assistant response
      setTimeout(() => {
        triggerSyncEvent({
          role: 'assistant',
          content: data.response || '',
          timestamp: Date.now()
        });
      }, 100);
      
    }catch(e){
      addMsg('JAI', 'Error contacting server');
    }
  }

  // --- Voice recording ---
  let mediaRecorder = null;
  let audioChunks = [];

  function setVoiceUI(recording){
    isRecording = recording;
    
    if(recording){
      startRecBtn.disabled = true;
      startRecBtn.classList.add('recording');
      stopRecBtn.disabled = false;
      voiceStatus.textContent = 'Recording…';
      voiceStatus.className = 'status voice-status recording';
    }else{
      startRecBtn.disabled = false;
      startRecBtn.classList.remove('recording');
      stopRecBtn.disabled = true;
      if(!voiceStatus.textContent.startsWith('Uploading') && !voiceStatus.textContent.startsWith('Processing')){
        voiceStatus.textContent = '';
        voiceStatus.className = 'status';
      }
    }
  }

  async function startRecording(){
    try{
      console.log('Starting recording...');
      
      // Check browser support
      if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){
        voiceStatus.textContent = 'Mic not supported in this browser';
        voiceStatus.className = 'status voice-status error';
        addMsg('System', 'Microphone not supported in this browser. Please try Chrome or Firefox.');
        return;
      }

      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      console.log('Microphone access granted');
      
      // Create media recorder with best supported format
      const options = (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported('audio/webm;codecs=opus'))
        ? { mimeType: 'audio/webm;codecs=opus' }
        : (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported('audio/webm'))
        ? { mimeType: 'audio/webm' }
        : {};
      
      mediaRecorder = new MediaRecorder(stream, options);
      audioChunks = [];
      
      mediaRecorder.ondataavailable = e => { 
        if(e.data && e.data.size > 0) {
          audioChunks.push(e.data);
          console.log('Audio chunk received:', e.data.size, 'bytes');
        }
      };
      
      mediaRecorder.onstop = async () => {
        console.log('Recording stopped, processing audio...');
        try{
          const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
          console.log('Audio blob created:', blob.size, 'bytes');
          
          voiceStatus.textContent = 'Processing…';
          voiceStatus.className = 'status voice-status processing';
          
          await sendAudio(blob);
        }catch(err){
          console.error('Error processing audio:', err);
          addMsg('JAI', 'Voice processing error: ' + err.message);
          voiceStatus.textContent = 'Error';
          voiceStatus.className = 'status voice-status error';
        }finally{
          // Stop all tracks
          if (mediaRecorder && mediaRecorder.stream){
            mediaRecorder.stream.getTracks().forEach(t => {
              t.stop();
              console.log('Audio track stopped');
            });
          }
          mediaRecorder = null;
          setVoiceUI(false);
        }
      };
      
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event.error);
        addMsg('JAI', 'Recording error: ' + event.error.message);
        setVoiceUI(false);
      };
      
      // Start recording
      mediaRecorder.start(100);
      console.log('Recording started');
      setVoiceUI(true);
      addMsg('System', '🎤 Listening... Speak now!');
      
    }catch(err){
      console.error('Error starting recording:', err);
      if(err.name === 'NotAllowedError'){
        voiceStatus.textContent = 'Mic permission denied';
        addMsg('System', '🎤 Microphone access denied. Please allow microphone access and try again.');
      }else if(err.name === 'NotFoundError'){
        voiceStatus.textContent = 'No microphone found';
        addMsg('System', '🎤 No microphone found. Please connect a microphone.');
      }else{
        voiceStatus.textContent = 'Mic error';
        addMsg('System', '🎤 Microphone error: ' + err.message);
      }
      voiceStatus.className = 'status voice-status error';
      setVoiceUI(false);
    }
  }

  async function sendAudio(blob){
    try{
      console.log('Sending audio to server...');
      
      if (!currentSessionId) {
        initializeSession();
      }
      
      const fd = new FormData();
      const fname = (blob.type && blob.type.includes('ogg')) ? 'voice.ogg' : 'voice.webm';
      fd.append('file', blob, fname);
      fd.append('lang', (voiceLang && voiceLang.value) || 'en-US');
      
      const response = await fetch(getBase() + '/api/voice', { 
        method: 'POST', 
        headers: {
          'X-Session-ID': currentSessionId
        },
        body: fd,
        timeout: 30000 // 30 second timeout
      });
      
      if(!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Server response:', data);
      
      // Update session ID if server returned a new one
      if (data.sessionId && data.sessionId !== currentSessionId) {
        currentSessionId = data.sessionId;
        localStorage.setItem(SESSION_KEY, currentSessionId);
      }
      
      if(data && (data.transcript || data.response)){
        if(data.transcript){ 
          addMsg('You', data.transcript);
          
          // Trigger sync event for transcript
          triggerSyncEvent({
            role: 'user',
            content: data.transcript,
            timestamp: Date.now()
          });
        }
        if(data.response){ 
          addMsg('JAI', data.response); 
          
          // Trigger sync event for response
          triggerSyncEvent({
            role: 'assistant',
            content: data.response,
            timestamp: Date.now()
          });
          
          // Trigger text-to-speech if available
          if(window.speechSynthesis && data.response) {
            speakResponse(data.response);
          }
        }
        voiceStatus.textContent = 'Done';
        voiceStatus.className = 'status voice-status success';
        
        // Clear status after 3 seconds
        setTimeout(() => {
          voiceStatus.textContent = '';
          voiceStatus.className = 'status';
        }, 3000);
        
      }else{
        const errorMsg = (data && data.error) ? ('Voice: ' + data.error) : 'Voice: no response';
        addMsg('JAI', errorMsg);
        voiceStatus.textContent = 'Error';
        voiceStatus.className = 'status voice-status error';
      }
    }catch(err){
      console.error('Error sending audio:', err);
      addMsg('JAI', 'Upload failed: ' + err.message);
      voiceStatus.textContent = 'Upload failed';
      voiceStatus.className = 'status voice-status error';
    }
  }

  function stopRecording(){
    try{
      console.log('Stopping recording...');
      if(mediaRecorder && mediaRecorder.state !== 'inactive'){
        mediaRecorder.stop();
        addMsg('System', '⏹️ Processing your voice...');
      }else{
        console.warn('No active recording to stop');
      }
    }catch(err){
      console.error('Error stopping recording:', err);
      setVoiceUI(false);
    }
  }

  // Text-to-speech function
  function speakResponse(text) {
    try {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 0.8;
      
      // Get available voices and use a good one
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(voice => 
        voice.name.includes('Google') || 
        voice.name.includes('Microsoft') || 
        voice.name.includes('Samantha')
      ) || voices[0];
      
      if(preferredVoice) {
        utterance.voice = preferredVoice;
      }
      
      utterance.onstart = () => {
        console.log('Speaking started');
      };
      
      utterance.onend = () => {
        console.log('Speaking ended');
      };
      
      utterance.onerror = (event) => {
        console.error('Speech error:', event.error);
      };
      
      window.speechSynthesis.speak(utterance);
      
    } catch(err) {
      console.error('Text-to-speech error:', err);
    }
  }

  // Load voices when ready
  function loadVoices() {
    if(window.speechSynthesis) {
      window.speechSynthesis.getVoices();
    }
  }

  // Load voices immediately and when they change
  if(window.speechSynthesis) {
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }

  // Event listeners - ensure elements exist before binding
  function initializeEventListeners() {
    // Basic event listeners
    if(saveBaseBtn) saveBaseBtn.addEventListener('click', function(){ saveBase(); checkHealth(); });
    if(healthBtn) healthBtn.addEventListener('click', checkHealth);
    if(sendBtn) sendBtn.addEventListener('click', sendText);
    if(textInput) textInput.addEventListener('keydown', function(e){ if(e.key === 'Enter') sendText(); });
    
    // Voice recording event listeners
    if(startRecBtn) {
      console.log('Binding start recording button');
      startRecBtn.addEventListener('click', function(e) {
        console.log('Start recording button clicked');
        e.preventDefault();
        startRecording();
      });
      
      // Add keyboard shortcut (Ctrl+M to start recording)
      document.addEventListener('keydown', function(e) {
        if(e.ctrlKey && e.key === 'm') {
          e.preventDefault();
          if(!isRecording) {
            startRecording();
          } else {
            stopRecording();
          }
        }
      });
    } else {
      console.error('Start recording button not found');
    }
    
    if(stopRecBtn) {
      console.log('Binding stop recording button');
      stopRecBtn.addEventListener('click', function(e) {
        console.log('Stop recording button clicked');
        e.preventDefault();
        stopRecording();
      });
    } else {
      console.error('Stop recording button not found');
    }
    
    // Add visual feedback for button clicks
    document.querySelectorAll('button').forEach(button => {
      button.addEventListener('click', function() {
        this.style.transform = 'scale(0.95)';
        setTimeout(() => {
          this.style.transform = 'scale(1)';
        }, 100);
      });
    });
  }

  // Prevent Google Translate from translating the page
  function preventGoogleTranslate() {
    // Add meta tag to prevent translation
    const meta = document.createElement('meta');
    meta.name = 'google';
    meta.content = 'notranslate';
    document.head.appendChild(meta);
    
    // Add class to body to prevent translation
    document.body.classList.add('notranslate');
    
    // Mark all important elements as notranslate
    const elementsToProtect = [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      '.logo', '.brand', '.header',
      'button', 'label', 'input[placeholder]',
      'option', 'select'
    ];
    
    elementsToProtect.forEach(selector => {
      document.querySelectorAll(selector).forEach(element => {
        if (!element.hasAttribute('translate')) {
          element.setAttribute('translate', 'no');
        }
      });
    });
    
    // Override Google Translate if it tries to activate
    if (typeof google !== 'undefined' && google.translate) {
      google.translate.TranslateElement({autoDisplay: false}, 'google_translate_element');
    }
    
    // Mutation observer to catch dynamically added elements
    const observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        mutation.addedNodes.forEach(function(node) {
          if (node.nodeType === 1) { // Element node
            if (node.tagName && ['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'BUTTON', 'LABEL'].includes(node.tagName)) {
              node.setAttribute('translate', 'no');
            }
            // Check child elements
            const childElements = node.querySelectorAll ? node.querySelectorAll('h1, h2, h3, h4, h5, h6, button, label, input, option, select') : [];
            childElements.forEach(el => el.setAttribute('translate', 'no'));
          }
        });
      });
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    console.log('Google Translate prevention activated');
  }

  // Initialize everything when DOM is ready
  function initializeApp() {
    console.log('Initializing JAI Web App...');
    
    // Prevent Google Translate from translating the page
    preventGoogleTranslate();
    
    // First, initialize all element references
    initializeElements();
    
    // Check if all required elements exist
    const requiredElements = ['apiBase', 'saveBase', 'healthBtn', 'healthStatus', 'messages', 'textInput', 'sendBtn', 'startRecBtn', 'stopRecBtn', 'voiceLang', 'voiceStatus'];
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    
    if(missingElements.length > 0) {
      console.error('Missing required elements:', missingElements);
      addMsg('System', '⚠️ Some UI elements are missing. Voice features may not work properly.');
    } else {
      console.log('All required elements found');
    }
    
    // Initialize session and cross-tab sync
    initializeSession();
    
    // Set up storage event listener for cross-tab sync
    window.addEventListener('storage', handleStorageEvent);
    
    // Load existing messages from storage or server
    const storedMessages = loadMessagesFromStorage();
    if (storedMessages.length > 0) {
      updateMessagesDisplay(storedMessages);
    } else {
      // Try to fetch from server if we have a session
      fetchLatestMessages();
    }
    
    // Start polling for new messages
    startSyncPolling();
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Load settings
    loadBase();
    checkHealth();
    
    // Show welcome message
    addMsg('System', '🎤 Voice mode ready! Click the microphone button or press Ctrl+M to start recording.');
    addMsg('System', '🔄 Cross-tab synchronization enabled - messages will sync across all open tabs.');
    
    console.log('JAI Web App initialized successfully with cross-tab sync');
  }

  // Wait for DOM to be ready
  if(document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
  } else {
    initializeApp();
  }
})();
