"""Executes registered skills.

This module deliberately does not maintain "trusted" memory or feed prior
output back into prompts. The gate's job is to mediate proposed side
effects, not to build agent context.
"""
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
import json
import smtplib
import urllib.request


class SkillError(RuntimeError):
    pass


class SkillExecutor:
    def __init__(self, root: Path, settings):
        self.root = Path(root)
        self.settings = settings
        self.registry_path = self.root / "skills" / "registry.json"
        self.registry = json.loads(self.registry_path.read_text(encoding="utf-8"))["skills"]
        self.audit_log_path = self.root / "data" / "audit_log.md"
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def list_skills(self):
        return self.registry

    def meta(self, skill_name: str):
        if skill_name not in self.registry:
            raise SkillError(f"Unknown skill: {skill_name}")
        return self.registry[skill_name]

    def can_auto_execute(self, skill_name: str) -> bool:
        meta = self.meta(skill_name)
        return (
            meta.get("risk") == "low"
            and (not meta.get("requires_approval"))
            and self.settings.auto_approve_low
        )

    def validate(self, skill_name: str, args: dict, agent: str, approved: bool = False):
        meta = self.meta(skill_name)
        allowed = meta.get("allowed_agents", [])
        if "any" not in allowed and agent not in allowed:
            raise SkillError(f"Agent '{agent}' is not allowed to use skill '{skill_name}'.")
        missing = [k for k in meta.get("required_args", []) if not args.get(k)]
        if missing:
            raise SkillError(f"Missing required args for {skill_name}: {missing}")
        if meta.get("requires_approval") and not approved:
            raise SkillError(f"Skill '{skill_name}' requires approval.")
        return meta

    def execute(self, skill_name: str, args: dict, agent: str = "caller", approved: bool = False):
        meta = self.validate(skill_name, args, agent, approved)
        if skill_name == "ifttt_notify":
            result = self._ifttt_notify(args["title"], args["message"], args.get("extra", ""))
        elif skill_name == "email_notify":
            result = self._email_notify(args["subject"], args["body"], args.get("to"))
        elif skill_name == "sms_email_notify":
            result = self._sms_email_notify(args["message"], args.get("to"))
        else:
            raise SkillError(f"Skill '{skill_name}' has no implementation.")
        self._audit(
            f"executed: {skill_name}",
            {
                "agent": agent,
                "risk": meta.get("risk"),
                "approved": approved,
                "args": args,
                "result": result,
            },
        )
        return result

    def _audit(self, title: str, body: dict):
        ts = datetime.utcnow().isoformat() + "Z"
        with self.audit_log_path.open("a", encoding="utf-8") as f:
            f.write(f"\n\n## {ts} — {title}\n\n```json\n{json.dumps(body, indent=2)}\n```\n")

    def _ifttt_notify(self, title: str, message: str, extra: str = ""):
        if not self.settings.ifttt_webhook_key:
            raise SkillError("IFTTT_WEBHOOK_KEY missing in .env")
        event = self.settings.ifttt_event_name or "agent_alert"
        url = f"https://maker.ifttt.com/trigger/{event}/with/key/{self.settings.ifttt_webhook_key}"
        payload = json.dumps({"value1": title, "value2": message, "value3": extra}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def _email_notify(self, subject: str, body: str, to: str = None):
        recipient = to or self.settings.email_to
        return self._send_email(subject, body, recipient)

    def _sms_email_notify(self, message: str, to: str = None):
        recipient = to or self.settings.sms_email_to
        if not recipient:
            raise SkillError("SMS_EMAIL_TO missing in .env or no 'to' arg supplied.")
        safe_message = message[:1400]
        return self._send_email("Agent SMS", safe_message, recipient)

    def _send_email(self, subject: str, body: str, recipient: str):
        required = [self.settings.smtp_host, self.settings.smtp_username, self.settings.smtp_password, self.settings.email_from]
        if not all(required):
            raise SkillError("SMTP settings missing in .env")
        if not recipient:
            raise SkillError("No email recipient set.")
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.settings.email_from
        msg["To"] = recipient
        msg.set_content(body)
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
            server.starttls()
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(msg)
        return f"email sent to {recipient}"
