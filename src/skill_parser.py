import json
import re

PATTERN = re.compile(r"SKILL_REQUEST:\s*([a-zA-Z0-9_]+)\s*=\s*(\{.*?\})(?=\n|$)", re.DOTALL)

def parse_skill_requests(text: str):
    requests = []
    for m in PATTERN.finditer(text):
        skill_name = m.group(1)
        raw = m.group(2)
        try:
            args = json.loads(raw)
        except json.JSONDecodeError:
            continue
        requests.append({"skill_name": skill_name, "args": args, "raw": m.group(0)})
    return requests
