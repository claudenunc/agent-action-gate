import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    auto_approve_low: bool
    ifttt_webhook_key: str
    ifttt_event_name: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    email_from: str
    email_to: str
    sms_email_to: str


def _load_dotenv(root: Path) -> None:
    env_path = root / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def load_settings(root: Path) -> Settings:
    _load_dotenv(root)
    return Settings(
        auto_approve_low=os.environ.get("ACTION_GATE_AUTO_APPROVE_LOW", "false").lower() == "true",
        ifttt_webhook_key=os.environ.get("IFTTT_WEBHOOK_KEY", ""),
        ifttt_event_name=os.environ.get("IFTTT_EVENT_NAME", "agent_alert"),
        smtp_host=os.environ.get("SMTP_HOST", ""),
        smtp_port=int(os.environ.get("SMTP_PORT", "587") or "587"),
        smtp_username=os.environ.get("SMTP_USERNAME", ""),
        smtp_password=os.environ.get("SMTP_PASSWORD", ""),
        email_from=os.environ.get("EMAIL_FROM", ""),
        email_to=os.environ.get("EMAIL_TO", ""),
        sms_email_to=os.environ.get("SMS_EMAIL_TO", ""),
    )
