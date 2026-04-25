from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

DANGEROUS_KEYWORDS = [
    "ignore previous instructions",
    "override rules",
    "disable safety",
    "send secrets",
    "exfiltrate",
    "customer database",
    "api key",
    "token",
    "password",
    "private key",
    "credential",
    "env file",
    ".env",
    "ssh key",
    "delete logs",
    "modify audit",
    "bypass approval",
]


def canonical_args(args_dict: dict) -> str:
    return json.dumps(args_dict or {}, sort_keys=True, separators=(",", ":"))


def registry_risk(skill_name: str) -> str:
    path = ROOT / "skills" / "registry.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return "low"
    return data.get("skills", {}).get(skill_name, {}).get("risk", "low")


def classify(skill_name: str, args_dict: dict):
    haystack = f"{skill_name} {canonical_args(args_dict)}".lower()
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in haystack:
            return "high", f"matched dangerous keyword: {keyword}"
    risk = registry_risk(skill_name)
    if risk in {"low", "medium", "high"}:
        return risk, None
    return "low", None
