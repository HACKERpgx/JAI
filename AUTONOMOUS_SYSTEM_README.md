# JAI Autonomous System

A fully autonomous AI system capable of understanding user intent, planning actions, executing them across supported tools and services, handling errors gracefully, and continuously improving through feedback.

## 🚀 Features

### Core Autonomous Capabilities
- **Intent Understanding**: Advanced NLP for understanding user requests
- **Smart Planning**: Multi-step task planning with dependency resolution
- **Intelligent Execution**: Execute tasks across multiple services and tools
- **Error Recovery**: Automatic error handling with multiple recovery strategies
- **Continuous Learning**: Machine learning-based improvement from user feedback

### Supported Integrations
- **Email Services**: Gmail integration for sending/receiving emails
- **Calendar Management**: Create, update, and manage calendar events
- **Media Control**: Play music, videos, and manage playlists
- **Weather Information**: Real-time weather data and forecasts
- **Web Services**: REST API, Webhook, and WebSocket integrations
- **Voice Interface**: Speech-to-text and text-to-speech capabilities

### Learning & Adaptation
- **User Preferences**: Learn and adapt to user preferences
- **Pattern Recognition**: Identify and learn from usage patterns
- **Feedback Integration**: Continuous improvement through user feedback
- **Auto-Training**: Automated model training and optimization

## 🛠️ Installation & Setup

### Prerequisites
```bash
pip install -r requirements.txt
pip install -r requirements-autonomous.txt  # Additional dependencies
```

### Environment Configuration
Create `.env` file with:
```env
# Core JAI Configuration
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key

# Gmail Integration (Optional)
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_SECRET

# Weather API (Optional)
WEATHER_API_KEY=your_weather_api_key

# Autonomous System
JAI_AUTONOMOUS_ENABLED=true
JAI_LEARNING_ENABLED=true
JAI_ERROR_RECOVERY_ENABLED=true
```

### Database Setup
The system automatically creates SQLite databases:
- `jai_autonomous_feedback.json` - User feedback data
- `jai_user_preferences.json` - User preferences
- `jai_learning_data/` - Machine learning data
- `jai_integrations.json` - External integrations

## 🌐 Web Interface

### Accessing the Autonomous Interface
1. Start the web server:
```bash
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8080
```

2. Open your browser to:
   - **Main Interface**: `http://localhost:8080/`
   - **Autonomous Dashboard**: `http://localhost:8080/autonomous`

### Dashboard Features
- **System Status**: Real-time monitoring of autonomous operations
- **Task Management**: View active tasks and execution history
- **Performance Metrics**: Success rates, response times, error statistics
- **Learning Insights**: View learned patterns and user preferences
- **Feedback System**: Rate and provide feedback on task performance
- **Integration Management**: Configure external service integrations

## 🔧 API Reference

### Autonomous Processing
```http
POST /api/autonomous/process
Content-Type: application/json

{
  "text": "Send email to john@example.com about the meeting tomorrow",
  "autonomous": true,
  "context": {}
}
```

### System Control
```http
POST /api/autonomous/enable
POST /api/autonomous/disable
POST /api/autonomous/emergency-stop
```

### Statistics & Monitoring
```http
GET /api/autonomous/statistics
GET /api/autonomous/active-tasks
GET /api/autonomous/task-history
GET /api/autonomous/learning-insights
```

### Feedback & Learning
```http
POST /api/autonomous/feedback
{
  "task_id": "task_123",
  "rating": 5,
  "comment": "Perfect execution!"
}

POST /api/autonomous/train
```

### External Integrations
```http
GET /api/integrations
POST /api/integrations
{
  "name": "Slack Webhook",
  "type": "webhook",
  "auth_type": "api_key",
  "endpoint": "https://hooks.slack.com/...",
  "auth_data": {"api_key": "xoxb-..."}
}
```

## 🧠 Learning System

### How JAI Learns
1. **Explicit Feedback**: User ratings and comments on task performance
2. **Implicit Learning**: Analysis of user behavior and corrections
3. **Pattern Recognition**: Identifying recurring patterns in requests
4. **Preference Adaptation**: Learning user preferences over time

### Training Data
- **Feedback History**: All user feedback with ratings and comments
- **Usage Patterns**: Time-based usage analysis and preferences
- **Error Analysis**: Common errors and successful recovery strategies
- **Intent Patterns**: Learned patterns for intent classification

### Model Improvement
```python
# Manual training
from jai_learning_system import learning_system
await learning_system.auto_improve()

# View learning insights
insights = learning_system.get_learning_insights()
print(insights)
```

## 🔌 Integration Examples

### Gmail Integration
```python
# Send email autonomously
result = await jai_autonomous.process_request(
    "Send email to team@company.com about the project update",
    context={"priority": "high"}
)
```

### Calendar Integration
```python
# Schedule meeting
result = await jai_autonomous.process_request(
    "Schedule team meeting for tomorrow at 2 PM with John and Sarah"
)
```

### Webhook Integration
```python
# Add Slack webhook
import requests

webhook_config = {
    "name": "Slack Notifications",
    "type": "webhook",
    "auth_type": "api_key",
    "endpoint": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "auth_data": {"api_key": "your_token"}
}

response = requests.post(
    "http://localhost:8080/api/integrations",
    json=webhook_config
)
```

## 🛡️ Error Handling & Recovery

### Recovery Strategies
1. **Exponential Backoff**: Retry with increasing delays
2. **Token Refresh**: Automatic authentication token renewal
3. **Fallback Services**: Switch to backup services when primary fails
4. **Resource Cleanup**: Clean up and retry resource-related errors
5. **Graceful Degradation**: Continue with reduced functionality

### Error Categories
- **Network**: Connection issues, timeouts
- **Authentication**: Invalid/expired credentials
- **Permission**: Access rights issues
- **Resource**: Memory, disk, or quota limits
- **External Service**: Third-party service failures

## 📊 Performance Monitoring

### Key Metrics
- **Success Rate**: Percentage of successfully completed tasks
- **Response Time**: Average time to process requests
- **Error Rate**: Frequency of errors by category
- **Learning Progress**: Improvement in accuracy over time
- **Integration Health**: Status of external service connections

### Monitoring Dashboard
Real-time monitoring includes:
- Active task execution
- System resource usage
- API response times
- Error trends and patterns
- Learning model performance

## 🔒 Security Considerations

### Authentication
- **API Keys**: Secure storage of external service credentials
- **OAuth2**: Standard OAuth2 flow for supported services
- **Token Management**: Automatic token refresh and rotation

### Data Privacy
- **Local Storage**: All learning data stored locally
- **Encryption**: Sensitive data encrypted at rest
- **Access Control**: User-specific data isolation

## 🚀 Advanced Usage

### Custom Task Handlers
```python
from jai_autonomous import TaskExecutor

class CustomHandler(TaskExecutor):
    async def handle_custom_service(self, action: str, params: dict):
        # Custom implementation
        return {"success": True, "result": "Custom action completed"}

# Register custom handler
jai_autonomous.task_executor.handlers['custom'] = CustomHandler()
```

### Autonomous Workflows
```python
# Create complex multi-step workflows
workflow_request = """
Plan and execute a complete project kickoff:
1. Schedule kickoff meeting for next week
2. Send calendar invites to all team members
3. Create project documentation template
4. Set up Slack channel for project communication
5. Send summary email to stakeholders
"""

result = await jai_autonomous.process_request(workflow_request)
```

## 🐛 Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed
2. **Authentication Failures**: Check API keys and credentials
3. **Database Issues**: Verify write permissions for data directory
4. **Network Errors**: Check internet connectivity for external services

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# View detailed error information
from jai_error_handler import error_handler
stats = error_handler.get_error_statistics()
print(stats)
```

### Performance Optimization
- **Caching**: Enable response caching for repeated requests
- **Batch Processing**: Group similar operations for efficiency
- **Resource Management**: Monitor and optimize memory usage
- **Connection Pooling**: Reuse connections for external services

## 🤝 Contributing

### Development Setup
```bash
git clone https://github.com/HACKERpgx/JAI.git
cd JAI
pip install -r requirements.txt
pip install -r requirements-autonomous.txt
```

### Testing
```bash
# Run autonomous system tests
python -m pytest tests/test_autonomous.py

# Test individual components
python test_autonomous_integration.py
```

## 📝 License

This project is part of the JAI (Just Another Intelligence) system. See main LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review error logs in `jai_autonomous.log`
3. Create an issue on the GitHub repository
4. Include system logs and configuration details

---

**JAI Autonomous System** - Transforming AI assistance into true autonomy. 🚀
