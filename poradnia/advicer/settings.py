from django.conf import settings

AI_ASSISTANT_USERNAME = getattr(settings, "AI_ASSISTANT_USERNAME", "AIAssistant")
AI_ASSISTANT_EMAIL = getattr(settings, "AI_ASSISTANT_EMAIL", "aiassistant@ai.assistant")
