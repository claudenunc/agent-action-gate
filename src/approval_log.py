from datetime import datetime
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
GENESIS_HASH = "0" * 64


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def approval_chain_path(root: Path = ROOT) -> Path:
    return Path(root) / "data" / "approval_chain.jsonl"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def entry_hash(prev_hash: str, entry: dict) -> str:
    payload = {
        "action_id": entry["action_id"],
        "decision": entry["decision"],
        "actor": entry["actor"],
        "timestamp_iso": entry["timestamp_iso"],
        "skill_name": entry["skill_name"],
        "args_sha256": entry["args_sha256"],
    }
    return sha256_text(prev_hash + canonical_json(payload))


def _read_entries(path: Path):
    if not path.exists():
        return []
    entries = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_no}: invalid JSON") from exc
    return entries


def append(action_id: str, actor: str, decision: str, skill_name: str, args: dict, root: Path = ROOT):
    path = approval_chain_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = _read_entries(path)
    prev_hash = entries[-1]["curr_hash"] if entries else GENESIS_HASH
    entry = {
        "action_id": action_id,
        "actor": actor,
        "timestamp_iso": datetime.utcnow().isoformat() + "Z",
        "decision": decision,
        "skill_name": skill_name,
        "args_sha256": sha256_text(canonical_json(args or {})),
        "prev_hash": prev_hash,
    }
    entry["curr_hash"] = entry_hash(prev_hash, entry)
    with path.open("a", encoding="utf-8") as f:
        f.write(canonical_json(entry) + "\n")
    return entry


def verify(root: Path = ROOT):
    path = approval_chain_path(root)
    try:
        entries = _read_entries(path)
    except ValueError as exc:
        return False, f"approval chain broken: {exc}"

    prev_hash = GENESIS_HASH
    for line_no, entry in enumerate(entries, start=1):
        required = {
            "action_id",
            "actor",
            "timestamp_iso",
            "decision",
            "skill_name",
            "args_sha256",
            "prev_hash",
            "curr_hash",
        }
        missing = sorted(required - set(entry))
        if missing:
            return False, f"approval chain broken at line {line_no}: missing {missing}"
        if entry["prev_hash"] != prev_hash:
            return False, f"approval chain broken at line {line_no}: prev_hash mismatch"
        expected = entry_hash(prev_hash, entry)
        if entry["curr_hash"] != expected:
            return False, f"approval chain broken at line {line_no}: curr_hash mismatch"
        prev_hash = entry["curr_hash"]

    return True, f"OK: approval chain intact ({len(entries)} entries)"
