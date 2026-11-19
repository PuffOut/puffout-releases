import argparse
import html
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from post_format import with_feedback
from publish import query, CHANNEL, BOT_NAME


def safe_link(url, label):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.netloc:
        raise ValueError('An HTTPS publication link is required')
    return '<a href="' + html.escape(url, quote=True) + '">' + label + '</a>'


def build_message(post):
    if 'text' in post:
        message = post['text'].strip()
    else:
        if post.get('platform') != 'pwa' or not post.get('version') or not post.get('sections'):
            raise ValueError('A PWA release needs version and changelog sections')
        label = ' · ' + html.escape(post['label']) if post.get('label') else ''
        parts = ['🛠 <b>PuffOut ' + html.escape(post['version']) + ' · PWA' + label + '</b>']
        for section in post['sections']:
            if not section.get('items'):
                raise ValueError('Empty changelog section')
            parts.append('<b>' + html.escape(section['title']) + '</b>\n' + '\n'.join('• ' + html.escape(item) for item in section['items']))
        parts.append('🌐 ' + safe_link(post['app_url'], 'Открыть PuffOut для iPhone и ПК') + '\n📖 ' + safe_link(post['guide_url'], 'Инструкция для iPhone'))
        parts.append('🔄 <b>Как обновить</b>\nОткройте PuffOut при подключённом интернете и нажмите «Обновить», когда появится плашка новой версии. Удалять приложение не нужно — прогресс сохраняется.')
        message = '\n\n'.join(parts)
    message = with_feedback(message, html=True)
    if len(message.encode('utf-16-le')) // 2 > 4096:
        raise ValueError('The Telegram post exceeds 4096 characters')
    return message


def main():
    parser = argparse.ArgumentParser(description='Publish PuffOut PWA changelogs to the Telegram channel')
    parser.add_argument('--release', type=Path, default=Path('posts/pwa-release.json'))
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--edit-message-id', type=int)
    args = parser.parse_args()
    message = build_message(json.loads(args.release.read_text(encoding='utf-8')))
    token = os.environ['TELEGRAM_BOT_TOKEN']
    bot = query(token, 'getMe')
    if bot.get('username', '').lower() != BOT_NAME:
        raise RuntimeError('Unexpected bot')
    member = query(token, 'getChatMember', chat_id=CHANNEL, user_id=bot['id'])
    if member.get('status') != 'administrator' or not member.get('can_post_messages'):
        raise RuntimeError('Publishing permission missing')
    if args.check:
        print('Bot access and PWA release format verified; no post sent.')
        return
    fields = dict(chat_id=CHANNEL, text=message, parse_mode='HTML', disable_web_page_preview='true')
    if args.edit_message_id is not None:
        if args.edit_message_id < 1:
            raise ValueError('Invalid message ID')
        fields['message_id'] = args.edit_message_id
        result = query(token, 'editMessageText', **fields)
        print('Updated https://t.me/PuffOutapp/' + str(result['message_id']))
    else:
        result = query(token, 'sendMessage', **fields)
        print('Published https://t.me/PuffOutapp/' + str(result['message_id']))


if __name__ == '__main__':
    main()
