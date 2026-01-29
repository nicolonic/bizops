#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from datetime import datetime


def participant_info(msg):
    sender = msg.get("sender") or msg.get("actor") or {}
    pt = sender.get("participantType") or {}
    org = pt.get("organization")
    if org:
        name = (org.get("name") or {}).get("text")
        url = org.get("pageUrl")
        if name:
            return name, url
    member = pt.get("member")
    if member:
        fn = (member.get("firstName") or {}).get("text", "")
        ln = (member.get("lastName") or {}).get("text", "")
        full = (fn + " " + ln).strip()
        url = member.get("profileUrl")
        if full:
            return full, url
        headline = (member.get("headline") or {}).get("text")
        if headline:
            return headline, url
    urn = sender.get("entityUrn") or sender.get("backendUrn")
    return urn or "Unknown", None


def sender_name(msg):
    name, _ = participant_info(msg)
    return name


def message_text(msg):
    body = msg.get("body") or {}
    text = body.get("text") or ""
    return " ".join(text.strip().split())


def delivered_at(msg):
    ts = msg.get("deliveredAt")
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""

def extract_conversation_urn(data):
    elements = (
        data.get("data", {})
        .get("messengerMessagesBySyncToken", {})
        .get("elements", [])
    )
    if not elements:
        return None
    conv = elements[0].get("conversation") or {}
    return conv.get("entityUrn")

def extract_unread_urns(path):
    data = json.loads(path.read_text())
    urns = set()

    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, str) and obj.startswith("urn:li:msg_conversation:"):
            urns.add(obj)

    walk(data)
    return urns

def latest_inbox_list():
    root = Path("linkedin/data/raw")
    candidates = sorted(root.glob("linkedin_unread_inbox_*.json"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads-dir", default="linkedin/data/raw/threads")
    ap.add_argument("--out", default="")
    ap.add_argument("--inbox-list", default="")
    ap.add_argument("--all-threads", action="store_true")
    args = ap.parse_args()

    threads_dir = Path(args.threads_dir)
    files = sorted(threads_dir.glob("*.json"))
    if not files:
        print(f"No thread files found in {threads_dir}")
        return 1

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_path = Path(args.out) if args.out else Path(f"linkedin/data/processed/unread_threads_{ts}.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    inbox_list = None
    if not args.all_threads:
        if args.inbox_list:
            inbox_list = Path(args.inbox_list)
        else:
            inbox_list = latest_inbox_list()
        if inbox_list and not inbox_list.exists():
            inbox_list = None

    allowed_urns = None
    use_filter = False
    if inbox_list:
        allowed_urns = extract_unread_urns(inbox_list)
        use_filter = True

    threads = []
    for f in files:
        data = json.loads(f.read_text())
        elements = (
            data.get("data", {})
            .get("messengerMessagesBySyncToken", {})
            .get("elements", [])
        )
        elements = sorted(elements, key=lambda m: m.get("deliveredAt") or 0)
        conv_urn = extract_conversation_urn(data)
        if use_filter and (not conv_urn or conv_urn not in allowed_urns):
            continue
        threads.append((f, data, elements, conv_urn))

    lines = []
    lines.append("---")
    lines.append(f'generated_at: "{datetime.now().strftime("%Y-%m-%d %H:%M")}"')
    lines.append(f'source_dir: "{threads_dir}"')
    if inbox_list:
        lines.append(f'inbox_list: "{inbox_list}"')
        lines.append('filter_mode: "inbox_list"')
    lines.append(f"thread_count: {len(threads)}")
    lines.append("---")
    lines.append("")
    lines.append("# LinkedIn Unread Threads")
    lines.append("")

    for idx, (f, data, elements, conv_urn) in enumerate(threads, start=1):
        participants = []
        profile_urls = {}
        seen = set()
        for m in elements:
            name, url = participant_info(m)
            if name and name not in seen:
                participants.append(name)
                seen.add(name)
            if name and url and name not in profile_urls:
                profile_urls[name] = url
        last_ts = delivered_at(elements[-1]) if elements else ""
        lines.append(f"## Thread {idx}")
        lines.append(f"- source_file: {f}")
        if conv_urn:
            lines.append(f"- conversation_urn: {conv_urn}")
        if participants:
            lines.append(f"- participants: {', '.join(participants)}")
        if elements:
            lines.append(f"- message_count: {len(elements)}")
        if last_ts:
            lines.append(f"- last_message_at: {last_ts}")
        lines.append("")
        if participants:
            lines.append("### Participants")
            for name in participants:
                url = profile_urls.get(name)
                if url:
                    lines.append(f"- {name}: {url}")
                else:
                    lines.append(f"- {name}")
            lines.append("")
        lines.append("### Transcript")
        for m in elements:
            t = delivered_at(m)
            name = sender_name(m)
            text = message_text(m)
            if not text:
                continue
            prefix = f"- [{t}] {name}: " if t else f"- {name}: "
            lines.append(prefix + text)
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.write_text("\n".join(lines) + "\n")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
