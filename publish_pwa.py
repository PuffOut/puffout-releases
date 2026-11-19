import json,os
from pathlib import Path
from post_format import with_feedback
from publish import query,CHANNEL,BOT_NAME

token=os.environ['TELEGRAM_BOT_TOKEN']
bot=query(token,'getMe')
if bot.get('username','').lower()!=BOT_NAME: raise RuntimeError('Unexpected bot')
member=query(token,'getChatMember',chat_id=CHANNEL,user_id=bot['id'])
if member.get('status')!='administrator' or not member.get('can_post_messages'): raise RuntimeError('Publishing permission missing')
post=json.loads(Path('posts/pwa-launch.json').read_text(encoding='utf-8'))
result=query(token,'sendMessage',chat_id=CHANNEL,text=with_feedback(post['text'], html=True),parse_mode='HTML',disable_web_page_preview='true')
print('Published https://t.me/PuffOutapp/'+str(result['message_id']))
