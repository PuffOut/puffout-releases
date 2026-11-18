# PuffOut

Выпуски приложения для Android 8.0 и новее и публикации в Telegram-канале @PuffOutapp.

## Публикация

GitHub Actions отправляет APK и текст из changelog.txt одним постом от @puffoutbot.
Отправка запускается при изменении release.json в ветке main.
Новый APK, ченжлог и release.json нужно добавлять одним коммитом.

В разделе Actions также доступен ручной запуск Publish PuffOut to Telegram.
По умолчанию ручной запуск проверяет подключение и права бота.
Для отправки отключи check_only. Повторная отправка создаёт новый пост.

## Настройка

Добавь секрет репозитория TELEGRAM_BOT_TOKEN с токеном @puffoutbot.
В канале @PuffOutapp бот должен быть администратором с правом публикации сообщений.

Для работы используется стандартный Linux runner GitHub Actions.

## Файлы выпуска

- releases/ содержит APK.
- changelog.txt содержит подпись к APK длиной до 1024 символов.
- release.json указывает версию и путь к APK.

Для локальной проверки подключения выполни python3 publish.py --check.
