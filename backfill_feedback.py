import json,os,urllib.request,urllib.parse,urllib.error
from pathlib import Path
from publish import query,CHANNEL,BOT_NAME
from post_format import DIRECT_URL

token=os.environ['TELEGRAM_BOT_TOKEN']
bot=query(token,'getMe')
assert bot.get('username','').lower()==BOT_NAME
member=query(token,'getChatMember',chat_id=CHANNEL,user_id=bot['id'])
assert member.get('status')=='administrator' and member.get('can_post_messages')
for post in json.loads(Path('posts/backfill-feedback.json').read_text(encoding='utf-8')):
    method='editMessageCaption' if post['kind']=='caption' else 'editMessageText'
    field='caption' if post['kind']=='caption' else 'text'
    fields={'chat_id':CHANNEL,'message_id':post['message_id'],field:post['text'],'parse_mode':'HTML'}
    if field=='text':fields['disable_web_page_preview']='true'
    request=urllib.request.Request('https://api.telegram.org/bot'+token+'/'+method,data=urllib.parse.urlencode(fields).encode())
    try:
        with urllib.request.urlopen(request,timeout=40) as response: result=json.load(response)
    except urllib.error.HTTPError as error:
        result=json.load(error)
    if not result.get('ok'):
        if 'message is not modified' in result.get('description','').lower():
            print('Already updated https://t.me/PuffOutapp/'+str(post['message_id']))
            continue
        raise RuntimeError('Editing post '+str(post['message_id'])+' failed: '+result.get('description','unknown error'))
    message=result['result']
    entities=message.get('caption_entities',[]) if field=='caption' else message.get('entities',[])
    assert any(e.get('url')==DIRECT_URL for e in entities), 'Feedback link missing'
    print('Updated https://t.me/PuffOutapp/'+str(message['message_id'])+'; direct-message link verified')
