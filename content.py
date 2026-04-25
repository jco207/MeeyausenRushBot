import re
from pathlib import Path

CONTENT_FILE = Path(__file__).parent / "Rush-content.md"


def load_items() -> list[dict]:
    text = CONTENT_FILE.read_text(encoding="utf-8")
    items = []

    for line in text.splitlines():
        line = line.strip()

        m = re.match(r'^(\d+)\.\s+(.+)', line)
        if m:
            items.append({
                "id": f"fact_{m.group(1)}",
                "type": "fact",
                "number": int(m.group(1)),
                "text": m.group(2).strip(),
            })
            continue

        m = re.match(r'^\*\s+\[(.+?)\]\((.+?)\)', line)
        if m:
            items.append({
                "id": f"video_{m.group(1).replace(' ', '_')}",
                "type": "video",
                "title": m.group(1),
                "url": m.group(2),
            })

    return items
