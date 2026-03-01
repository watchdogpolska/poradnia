from guardian.conf import settings

JUDGEMENT_BOT_USERNAME = getattr(settings, "JUDGEMENT_BOT_USERNAME", "JudgementBot")
JUDGEMENT_BOT_EMAIL = getattr(
    settings, "JUDGEMENT_BOT_EMAIL", "judgementbot@judgement.bot"
)
