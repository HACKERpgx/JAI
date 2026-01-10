(function(){
  // Configuration
  const LS_KEY = 'jai_api_base';
  let apiBase = 'http://localhost:8080';
  let autonomousMode = false;
  let selectedRating = 0;
  let performanceData = [];
  let taskHistory = [];

  // DOM Elements
  const elements = {
    apiBase: document.getElementById('apiBase'),
    saveBase: document.getElementById('saveBase'),
    healthBtn: document.getElementById('healthBtn'),
    healthStatus: document.getElementById('healthStatus'),
    enableAutonomous: document.getElementById('enableAutonomous'),
    disableAutonomous: document.getElementById('disableAutonomous'),
    emergencyStop: document.getElementById('emergencyStop'),
    refreshData: document.getElementById('refreshData'),
    systemStatus: document.getElementById('systemStatus'),
    activeTasks: document.getElementById('activeTasks'),
    successRate: document.getElementById('successRate'),
    learningProgress: document.getElementById('learningProgress'),
    learningProgressBar: document.getElementById('learningProgressBar'),
    totalTasks: document.getElementById('totalTasks'),
    avgResponseTime: document.getElementById('avgResponseTime'),
    errorRate: document.getElementById('errorRate'),
    uptime: document.getElementById('uptime'),
    activeTasksList: document.getElementById('activeTasksList'),
    taskHistory: document.getElementById('taskHistory'),
    learnedPatterns: document.getElementById('learnedPatterns'),
    userPreferences: document.getElementById('userPreferences'),
    accuracyImprovement: document.getElementById('accuracyImprovement'),
    taskSelect: document.getElementById('taskSelect'),
    ratingStars: document.getElementById('ratingStars'),
    feedbackComment: document.getElementById('feedbackComment'),
    submitFeedback: document.getElementById('submitFeedback'),
    trainModel: document.getElementById('trainModel'),
    exportData: document.getElementById('exportData'),
    messages: document.getElementById('messages'),
    textInput: document.getElementById('textInput'),
    sendBtn: document.getElementById('sendBtn'),
    startRecBtn: document.getElementById('startRecBtn'),
    stopRecBtn: document.getElementById('stopRecBtn'),
    voiceLang: document.getElementById('voiceLang'),
    voiceStatus: document.getElementById('voiceStatus')
  };

  // Initialize
  function init() {
    loadApiBase();
    setupEventListeners();
    startMonitoring();
    loadTaskHistory();
  }

  function loadApiBase() {
    const saved = localStorage.getItem(LS_KEY);
    if (saved) {
      apiBase = saved;
      elements.apiBase.value = saved;
    }
  }

  function saveApiBase() {
    apiBase = elements.apiBase.value.trim() || 'http://localhost:8080';
    localStorage.setItem(LS_KEY, apiBase);
    addMessage('System', 'API base URL saved');
  }

  function setupEventListeners() {
    elements.saveBase.addEventListener('click', saveApiBase);
    elements.healthBtn.addEventListener('click', checkHealth);
    elements.enableAutonomous.addEventListener('click', enableAutonomousMode);
    elements.disableAutonomous.addEventListener('click', disableAutonomousMode);
    elements.emergencyStop.addEventListener('click', emergencyStop);
    elements.refreshData.addEventListener('click', refreshAllData);
    elements.submitFeedback.addEventListener('click', submitFeedback);
    elements.trainModel.addEventListener('click', trainModel);
    elements.exportData.addEventListener('click', exportLearningData);
    elements.sendBtn.addEventListener('click', sendMessage);
    elements.textInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendMessage();
    });

    // Rating stars
    elements.ratingStars.querySelectorAll('.star').forEach(star => {
      star.addEventListener('click', function() {
        selectedRating = parseInt(this.dataset.rating);
        updateRatingStars();
      });
    });

    // Voice recording (simplified)
    elements.startRecBtn.addEventListener('click', startRecording);
    elements.stopRecBtn.addEventListener('click', stopRecording);
  }

  async function checkHealth() {
    elements.healthStatus.textContent = 'Checking…';
    try {
      const res = await fetch(`${apiBase}/api/health`);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      elements.healthStatus.textContent = data.ok ? ('OK ' + (data.time || '')) : 'Not OK';
    } catch (e) {
      elements.healthStatus.textContent = 'Error';
      addMessage('System', `Health check failed: ${e.message}`);
    }
  }

  async function enableAutonomousMode() {
    try {
      const res = await fetch(`${apiBase}/api/autonomous/enable`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      if (data.success) {
        autonomousMode = true;
        updateSystemStatus('Active', 'active');
        addMessage('System', 'Autonomous mode enabled');
      } else {
        addMessage('System', `Failed to enable autonomous mode: ${data.message}`);
      }
    } catch (e) {
      addMessage('System', `Error enabling autonomous mode: ${e.message}`);
    }
  }

  async function disableAutonomousMode() {
    try {
      const res = await fetch(`${apiBase}/api/autonomous/disable`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      if (data.success) {
        autonomousMode = false;
        updateSystemStatus('Idle', 'idle');
        addMessage('System', 'Autonomous mode disabled');
      } else {
        addMessage('System', `Failed to disable autonomous mode: ${data.message}`);
      }
    } catch (e) {
      addMessage('System', `Error disabling autonomous mode: ${e.message}`);
    }
  }

  async function emergencyStop() {
    try {
      const res = await fetch(`${apiBase}/api/autonomous/emergency-stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      autonomousMode = false;
      updateSystemStatus('Stopped', 'error');
      addMessage('System', 'Emergency stop activated - all autonomous tasks halted');
    } catch (e) {
      addMessage('System', `Error during emergency stop: ${e.message}`);
    }
  }

  async function refreshAllData() {
    await Promise.all([
      updateSystemMetrics(),
      updateActiveTasks(),
      updateTaskHistory(),
      updateLearningInsights()
    ]);
    addMessage('System', 'Data refreshed');
  }

  async function updateSystemMetrics() {
    try {
      const res = await fetch(`${apiBase}/api/autonomous/statistics`);
      const data = await res.json();
      
      elements.totalTasks.textContent = data.total_tasks || 0;
      elements.activeTasks.textContent = data.active_tasks || 0;
      elements.successRate.textContent = `${Math.round(data.success_rate || 0)}%`;
      elements.errorRate.textContent = `${Math.round(100 - (data.success_rate || 0))}%`;
      elements.avgResponseTime.textContent = `${Math.round(data.avg_response_time || 0)}ms`;
      elements.uptime.textContent = `${Math.round((data.uptime || 0) / 3600)}h`;
      
      // Update learning progress
      const progress = Math.min(100, (data.feedback_count || 0) * 2);
      elements.learningProgress.textContent = `${progress}%`;
      elements.learningProgressBar.style.width = `${progress}%`;
      
      // Store performance data for chart
      performanceData.push({
        timestamp: Date.now(),
        successRate: data.success_rate || 0,
        activeTasks: data.active_tasks || 0
      });
      
      // Keep only last 50 data points
      if (performanceData.length > 50) {
        performanceData = performanceData.slice(-50);
      }
      
      updatePerformanceChart();
      
    } catch (e) {
      console.error('Error updating metrics:', e);
    }
  }

  async function updateActiveTasks() {
    try {
      const res = await fetch(`${apiBase}/api/autonomous/active-tasks`);
      const tasks = await res.json();
      
      if (tasks.length === 0) {
        elements.activeTasksList.innerHTML = '<p style="color: #6c757d; text-align: center;">No active tasks</p>';
        return;
      }
      
      elements.activeTasksList.innerHTML = tasks.map(task => `
        <div class="task-item ${task.status}">
          <div style="font-weight: bold;">${task.intent}</div>
          <div style="font-size: 12px; color: #6c757d;">
            Status: ${task.status} | Created: ${new Date(task.created_at).toLocaleTimeString()}
          </div>
        </div>
      `).join('');
      
    } catch (e) {
      console.error('Error updating active tasks:', e);
    }
  }

  async function updateTaskHistory() {
    try {
      const res = await fetch(`${apiBase}/api/autonomous/task-history`);
      const tasks = await res.json();
      
      taskHistory = tasks.slice(0, 10); // Keep last 10 for feedback
      
      if (tasks.length === 0) {
        elements.taskHistory.innerHTML = '<p style="color: #6c757d; text-align: center;">No recent tasks</p>';
        elements.taskSelect.innerHTML = '<option value="">Choose a recent task...</option>';
        return;
      }
      
      elements.taskHistory.innerHTML = tasks.slice(0, 10).map(task => `
        <div class="task-item ${task.status === 'completed' ? '' : 'failed'}">
          <div style="font-weight: bold;">${task.intent}</div>
          <div style="font-size: 12px; color: #6c757d;">
            ${task.status} | ${new Date(task.completed_at || task.created_at).toLocaleTimeString()}
          </div>
        </div>
      `).join('');
      
      // Update task select for feedback
      elements.taskSelect.innerHTML = '<option value="">Choose a recent task...</option>' +
        tasks.slice(0, 20).map(task => 
          `<option value="${task.id}">${task.intent} - ${new Date(task.created_at).toLocaleTimeString()}</option>`
        ).join('');
      
    } catch (e) {
      console.error('Error updating task history:', e);
    }
  }

  async function updateLearningInsights() {
    try {
      const res = await fetch(`${apiBase}/api/autonomous/learning-insights`);
      const data = await res.json();
      
      elements.learnedPatterns.textContent = data.total_patterns || 0;
      elements.userPreferences.textContent = data.total_preferences || 0;
      elements.accuracyImprovement.textContent = `${Math.round(data.accuracy_improvement || 0)}%`;
      
    } catch (e) {
      console.error('Error updating learning insights:', e);
    }
  }

  function updateSystemStatus(status, className) {
    elements.systemStatus.innerHTML = `
      <span class="status-indicator status-${className}"></span>
      ${status}
    `;
  }

  function updateRatingStars() {
    elements.ratingStars.querySelectorAll('.star').forEach((star, index) => {
      star.classList.toggle('active', index < selectedRating);
    });
  }

  async function submitFeedback() {
    const taskId = elements.taskSelect.value;
    if (!taskId) {
      addMessage('System', 'Please select a task to provide feedback for');
      return;
    }
    
    if (selectedRating === 0) {
      addMessage('System', 'Please provide a rating');
      return;
    }
    
    try {
      const res = await fetch(`${apiBase}/api/autonomous/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: taskId,
          rating: selectedRating,
          comment: elements.feedbackComment.value
        })
      });
      
      const data = await res.json();
      if (data.success) {
        addMessage('System', 'Feedback submitted successfully - thank you for helping JAI learn!');
        // Reset form
        elements.taskSelect.value = '';
        elements.feedbackComment.value = '';
        selectedRating = 0;
        updateRatingStars();
      } else {
        addMessage('System', `Failed to submit feedback: ${data.message}`);
      }
    } catch (e) {
      addMessage('System', `Error submitting feedback: ${e.message}`);
    }
  }

  async function trainModel() {
    try {
      addMessage('System', 'Starting model training...');
      const res = await fetch(`${apiBase}/api/autonomous/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await res.json();
      if (data.success) {
        addMessage('System', `Model training completed. Accuracy improved by ${data.improvement}%`);
        updateLearningInsights();
      } else {
        addMessage('System', `Model training failed: ${data.message}`);
      }
    } catch (e) {
      addMessage('System', `Error during model training: ${e.message}`);
    }
  }

  async function exportLearningData() {
    try {
      const res = await fetch(`${apiBase}/api/autonomous/export-data`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `jai_learning_data_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
      addMessage('System', 'Learning data exported successfully');
    } catch (e) {
      addMessage('System', `Error exporting data: ${e.message}`);
    }
  }

  async function sendMessage() {
    const text = elements.textInput.value.trim();
    if (!text) return;
    
    addMessage('You', text);
    elements.textInput.value = '';
    
    try {
      const res = await fetch(`${apiBase}/api/autonomous/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, autonomous: autonomousMode })
      });
      
      const data = await res.json();
      addMessage('JAI', data.message);
      
      if (data.task_id) {
        addMessage('System', `Task created with ID: ${data.task_id}`);
        // Refresh data after a short delay
        setTimeout(refreshAllData, 1000);
      }
      
    } catch (e) {
      addMessage('System', `Error processing request: ${e.message}`);
    }
  }

  function addMessage(who, text) {
    const div = document.createElement('div');
    div.className = 'msg ' + (who === 'You' ? 'you' : 'jai');
    div.textContent = `${who}: ${text}`;
    elements.messages.appendChild(div);
    elements.messages.scrollTop = elements.messages.scrollHeight;
  }

  function startMonitoring() {
    // Update metrics every 5 seconds
    setInterval(updateSystemMetrics, 5000);
    // Update tasks every 10 seconds
    setInterval(() => {
      updateActiveTasks();
      updateTaskHistory();
    }, 10000);
    // Update learning insights every 30 seconds
    setInterval(updateLearningInsights, 30000);
    
    // Initial load
    refreshAllData();
  }

  function loadTaskHistory() {
    // Load from localStorage for persistence
    const saved = localStorage.getItem('jai_task_history');
    if (saved) {
      try {
        taskHistory = JSON.parse(saved);
      } catch (e) {
        console.error('Error loading task history:', e);
      }
    }
  }

  function updatePerformanceChart() {
    const canvas = document.getElementById('performanceCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth;
    const height = canvas.height = canvas.offsetHeight;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    if (performanceData.length < 2) return;
    
    // Draw simple line chart
    ctx.strokeStyle = '#007bff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    const xStep = width / (performanceData.length - 1);
    const yScale = height / 100;
    
    performanceData.forEach((point, index) => {
      const x = index * xStep;
      const y = height - (point.successRate * yScale);
      
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    ctx.stroke();
    
    // Draw axes
    ctx.strokeStyle = '#ddd';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, height - 1);
    ctx.lineTo(width, height - 1);
    ctx.stroke();
  }

  // Voice recording (simplified implementation)
  let mediaRecorder;
  let audioChunks = [];

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        await sendVoiceInput(audioBlob);
      };
      
      mediaRecorder.start();
      elements.startRecBtn.disabled = true;
      elements.stopRecBtn.disabled = false;
      elements.voiceStatus.textContent = 'Recording...';
      
    } catch (e) {
      addMessage('System', `Error starting recording: ${e.message}`);
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      elements.startRecBtn.disabled = false;
      elements.stopRecBtn.disabled = true;
      elements.voiceStatus.textContent = 'Processing...';
    }
  }

  async function sendVoiceInput(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('language', elements.voiceLang.value);
    
    try {
      const res = await fetch(`${apiBase}/api/voice`, {
        method: 'POST',
        body: formData
      });
      
      const data = await res.json();
      if (data.text) {
        elements.textInput.value = data.text;
        elements.voiceStatus.textContent = 'Voice processed';
        addMessage('Voice', data.text);
      } else {
        elements.voiceStatus.textContent = 'Voice recognition failed';
      }
    } catch (e) {
      elements.voiceStatus.textContent = 'Error processing voice';
      addMessage('System', `Error processing voice: ${e.message}`);
    }
  }

  // Initialize the application
  init();
})();
