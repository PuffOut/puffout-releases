DIRECT_URL = "https://t.me/PuffOutapp?direct"
FOOTER_HTML = "🐞 <b>Сообщить об ошибке</b>\nЕсли вы обнаружили ошибку в работе приложения, сообщите об этом в <a href=\"https://t.me/PuffOutapp?direct\">личные сообщения канала</a>. По возможности укажите модель устройства, версию приложения и приложите скриншот."
FOOTER_TEXT = "🐞 Сообщить об ошибке\nЕсли вы обнаружили ошибку в работе приложения, сообщите об этом в личные сообщения канала: " + DIRECT_URL + ". По возможности укажите модель устройства, версию приложения и приложите скриншот."

def with_feedback(text, html=True):
    if DIRECT_URL in text:
        return text
    return text.rstrip() + "\n\n" + (FOOTER_HTML if html else FOOTER_TEXT)
