(function(){
  const apiBaseInput = document.getElementById('apiBase');
  const saveBaseBtn = document.getElementById('saveBase');
  const healthBtn = document.getElementById('healthBtn');
  const healthStatus = document.getElementById('healthStatus');
  const messages = document.getElementById('messages');
  const textInput = document.getElementById('textInput');
  const sendBtn = document.getElementById('sendBtn');
  const startRecBtn = document.getElementById('startRecBtn');
  const stopRecBtn = document.getElementById('stopRecBtn');
  const voiceLang = document.getElementById('voiceLang');
  const voiceStatus = document.getElementById('voiceStatus');

  const LS_KEY = 'jai_api_base';
  function getBase(){ return apiBaseInput.value.trim() || 'http://localhost:8080'; }
  function setBase(v){ apiBaseInput.value = v; }
  function loadBase(){ setBase(localStorage.getItem(LS_KEY) || 'http://localhost:8080'); }
  function saveBase(){ localStorage.setItem(LS_KEY, getBase()); }

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
    addMsg('You', text);
    textInput.value = '';
    try{
      const res = await fetch(getBase() + '/api/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if(!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      addMsg('JAI', data.response || '');
    }catch(e){
      addMsg('JAI', 'Error contacting server');
    }
  }

  // --- Voice recording ---
  let mediaRecorder = null;
  let audioChunks = [];

  function setVoiceUI(recording){
    if(recording){
      startRecBtn.disabled = true;
      stopRecBtn.disabled = false;
      voiceStatus.textContent = 'Recording…';
    }else{
      startRecBtn.disabled = false;
      stopRecBtn.disabled = true;
      if(!voiceStatus.textContent.startsWith('Uploading')){
        voiceStatus.textContent = '';
      }
    }
  }

  async function startRecording(){
    try{
      if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){
        voiceStatus.textContent = 'Mic not supported in this browser';
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const options = (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported('audio/webm;codecs=opus'))
        ? { mimeType: 'audio/webm;codecs=opus' }
        : {};
      mediaRecorder = new MediaRecorder(stream, options);
      audioChunks = [];
      mediaRecorder.ondataavailable = e => { if(e.data && e.data.size > 0) audioChunks.push(e.data); };
      mediaRecorder.onstop = async () => {
        try{
          const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
          voiceStatus.textContent = 'Uploading…';
          await sendAudio(blob);
        }catch(err){
          addMsg('JAI', 'Voice error');
        }finally{
          // stop tracks
          if (mediaRecorder && mediaRecorder.stream){
            mediaRecorder.stream.getTracks().forEach(t => t.stop());
          }
          mediaRecorder = null;
          setVoiceUI(false);
        }
      };
      mediaRecorder.start(100);
      setVoiceUI(true);
    }catch(err){
      voiceStatus.textContent = 'Mic permission denied';
    }
  }

  async function sendAudio(blob){
    try{
      const fd = new FormData();
      const fname = (blob.type && blob.type.includes('ogg')) ? 'voice.ogg' : 'voice.webm';
      fd.append('file', blob, fname);
      fd.append('lang', (voiceLang && voiceLang.value) || 'en-US');
      const res = await fetch(getBase() + '/api/voice', { method: 'POST', body: fd });
      const data = await res.json();
      if(data && (data.transcript || data.response)){
        if(data.transcript){ addMsg('You', data.transcript); }
        if(data.response){ addMsg('JAI', data.response); }
        voiceStatus.textContent = 'Done';
      }else{
        addMsg('JAI', (data && data.error) ? ('Voice: ' + data.error) : 'Voice: no response');
        voiceStatus.textContent = 'Error';
      }
    }catch(err){
      addMsg('JAI', 'Upload failed');
      voiceStatus.textContent = 'Error';
    }
  }

  function stopRecording(){
    try{
      if(mediaRecorder && mediaRecorder.state !== 'inactive'){
        mediaRecorder.stop();
      }
    }catch(_){}
  }

  saveBaseBtn.addEventListener('click', function(){ saveBase(); checkHealth(); });
  healthBtn.addEventListener('click', checkHealth);
  sendBtn.addEventListener('click', sendText);
  textInput.addEventListener('keydown', function(e){ if(e.key === 'Enter') sendText(); });
  if(startRecBtn) startRecBtn.addEventListener('click', startRecording);
  if(stopRecBtn) stopRecBtn.addEventListener('click', stopRecording);

  loadBase();
  checkHealth();
})();
