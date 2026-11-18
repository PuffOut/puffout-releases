import argparse
import getpass
import json
import os
from pathlib import Path
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


CHANNEL = "@PuffOutapp"
BOT_NAME = "puffoutbot"
ROOT = Path(__file__).resolve().parent


class PublishError(Exception):
    pass


def api(token, method, data, content_type):
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=data,
        headers={"Content-Type": content_type},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise PublishError(f"Telegram returned HTTP {error.code}. Check the token and bot permissions.") from None
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
        if method == "sendDocument":
            raise PublishError(
                "The upload response was lost. Check the channel before trying again to avoid a duplicate."
            ) from None
        raise PublishError("Cannot reach Telegram. Check the network connection.") from None
    except (ValueError, UnicodeError):
        raise PublishError("Telegram returned an unreadable response.") from None
    if not result.get("ok"):
        raise PublishError("Telegram rejected the request. Check the token and channel permissions.")
    return result["result"]


def query(token, method, **fields):
    return api(
        token, method, urllib.parse.urlencode(fields).encode(),
        "application/x-www-form-urlencoded",
    )


def document_body(apk, caption):
    boundary = "PuffOut" + uuid.uuid4().hex
    parts = []
    for name, value in (("chat_id", CHANNEL), ("caption", caption)):
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode("utf-8")
        )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{apk.name}"\r\n'
        'Content-Type: application/vnd.android.package-archive\r\n\r\n'.encode("utf-8")
    )
    parts.append(apk.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def main():
    parser = argparse.ArgumentParser(description="Publish a PuffOut APK and changelog to @PuffOutapp.")
    parser.add_argument("--apk", type=Path)
    parser.add_argument("--changelog", type=Path, default=ROOT / "changelog.txt")
    parser.add_argument("--check", action="store_true", help="Check bot and channel permissions without publishing.")
    parser.add_argument("--yes", action="store_true", help="Publish without an interactive confirmation.")
    args = parser.parse_args()
    if args.apk is None:
        release = json.loads((ROOT / "release.json").read_text(encoding="utf-8"))
        args.apk = (ROOT / release["apk"]).resolve()
        if not args.apk.is_relative_to(ROOT):
            raise PublishError("The APK must be inside this repository.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.apk", args.apk.name):
        raise PublishError("Use a simple APK filename such as PuffOut-1.2.12.apk.")
    if not args.apk.is_file() or not args.changelog.is_file():
        raise PublishError("The APK or changelog file is missing.")
    if args.apk.stat().st_size > 49_000_000:
        raise PublishError("The APK is too large for this publisher.")
    caption = args.changelog.read_text(encoding="utf-8-sig").strip()
    if not caption or len(caption.encode("utf-16-le")) // 2 > 1024:
        raise PublishError("The changelog must contain between 1 and 1024 characters.")
    print(f"Channel {CHANNEL}\nFile {args.apk.name}\n\n{caption}\n")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        if not sys.stdin.isatty():
            raise PublishError("Set the repository secret TELEGRAM_BOT_TOKEN before running this workflow.")
        token = getpass.getpass("Bot token (hidden input) > ")
    token = token.strip()
    if not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+", token):
        raise PublishError("Invalid token format.")
    bot = query(token, "getMe")
    if bot.get("username", "").lower() != BOT_NAME:
        raise PublishError("This token belongs to a different bot. Expected @puffoutbot.")
    member = query(token, "getChatMember", chat_id=CHANNEL, user_id=bot["id"])
    if member.get("status") != "administrator" or not member.get("can_post_messages"):
        raise PublishError("Add @puffoutbot as a channel administrator with permission to post messages.")
    print("Bot and channel permissions verified.")
    if args.check:
        return
    if not args.yes and input("Type SEND to publish this APK and changelog > ").strip() != "SEND":
        print("Cancelled.")
        return
    data, content_type = document_body(args.apk, caption)
    message = api(token, "sendDocument", data, content_type)
    print(f"Published https://t.me/PuffOutapp/{message['message_id']}")


if __name__ == "__main__":
    try:
        main()
    except (PublishError, OSError, UnicodeError, EOFError, ValueError, KeyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
