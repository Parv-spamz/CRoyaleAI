"""Send a new report through the existing webhook, recording each delivery once."""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def units(text):
    return len(text.encode('utf-16-le')) // 2


def split_message(text):
    if not text.strip():
        raise ValueError('Report is empty')
    if re.search(r'@(everyone|here)|<@|discord(?:app)?\.com/api/webhooks/', text, re.I):
        raise ValueError('Report contains a mention or webhook URL')
    chunks = []
    rest = text.strip()
    while rest:
        end = 0
        size = 0
        for char in rest:
            size += units(char)
            if size > 1850:
                break
            end += 1
        if end < len(rest):
            boundary = rest.rfind('\n\n', 0, end + 1)
            if boundary > end // 2:
                end = boundary
        chunks.append(rest[:end].rstrip())
        rest = rest[end:].lstrip()
    if len(chunks) > 1:
        chunks = [f'**Part {i + 1} of {len(chunks)}**\n\n{c}' for i, c in enumerate(chunks)]
    if any(units(c) > 2000 for c in chunks):
        raise ValueError('Message part exceeds Discord limit')
    return chunks


def write_state(path, state):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8', newline='\n') as f:
        json.dump(state, f, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


def deliver(report_id, text, root, webhook_path, opener=urllib.request.urlopen):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,100}', report_id):
        raise ValueError('Invalid report ID')
    chunks = split_message(text)
    directory = root / report_id
    root.mkdir(parents=True, exist_ok=True)
    try:
        directory.mkdir()  # Atomic claim; prevents concurrent or duplicate sends.
    except FileExistsError:
        receipt = directory / 'delivery.json'
        if receipt.exists():
            previous = json.loads(receipt.read_text(encoding='utf-8'))
            if previous.get('status') == 'delivered':
                print('ALREADY_DELIVERED', report_id)
                return previous
        raise RuntimeError('Existing incomplete attempt: reconcile delivery before any retry')
    (directory / 'message.md').write_text(text, encoding='utf-8')
    state = dict(report_id=report_id, created_at=stamp(), text_sha256=digest(text),
                 status='prepared', chunks=[])
    receipt = directory / 'delivery.json'
    write_state(receipt, state)
    try:
        url = webhook_path.read_text(encoding='utf-8').strip()
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname not in ('discord.com', 'discordapp.com'):
            raise ValueError('Invalid configured webhook host')
        query = dict(urllib.parse.parse_qsl(parsed.query))
        query['wait'] = 'true'
        url = urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query)))
        for index, chunk in enumerate(chunks):
            part = dict(index=index + 1, sha256=digest(chunk), status='pending', started_at=stamp())
            state['chunks'].append(part)
            state['status'] = 'sending'
            write_state(receipt, state)  # Pending is durable before network I/O.
            data = json.dumps({'content': chunk, 'allowed_mentions': {'parse': []}}).encode('utf-8')
            request = urllib.request.Request(url, data=data, method='POST', headers={
                'Content-Type': 'application/json', 'User-Agent': 'ClashBot-updates/2.0'})
            with opener(request, timeout=30) as response:
                result = json.loads(response.read())
                if response.status != 200 or not str(result.get('id', '')).isdigit():
                    raise RuntimeError('Delivery response lacks confirmed message ID')
                part.update(status='delivered', http_status=response.status,
                            message_id=result['id'], completed_at=stamp())
            write_state(receipt, state)
        state.update(status='delivered', completed_at=stamp())
        write_state(receipt, state)
        print('DELIVERED', report_id, len(chunks), 'parts')
        return state
    except Exception as exc:
        state.update(status='needs_reconciliation', error_type=type(exc).__name__)
        write_state(receipt, state)
        # Exception text can include the credential-bearing URL; never print it.
        raise RuntimeError('Delivery incomplete; inspect the saved receipt before retrying') from None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--file', required=True, type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    text = args.file.read_text(encoding='utf-8')
    if args.dry_run:
        chunks = split_message(text)
        print(json.dumps({'id': args.id, 'parts': len(chunks), 'part_units': [units(c) for c in chunks],
                          'text_sha256': digest(text), 'sent': False}))
        return
    deliver(args.id, text, REPO / 'reports/discord/deliveries',
            REPO / 'icebow/data/discord_webhook.txt')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(type(exc).__name__ + ': report not completed; inspect local records', file=sys.stderr)
        sys.exit(1)
