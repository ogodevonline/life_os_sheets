# Настройка OAuth для Google Sheets API (для локального запуска без верификации)

## Введение
OAuth позволяет аутентифицироваться с вашим личным аккаунтом Google. Для локального запуска без блокировки добавьте себя как тестера — верификация не нужна.

## Шаг 1: Создание проекта в Google Cloud Console
1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/).
2. Создайте новый проект или выберите существующий.
3. Включите Google Sheets API и Google Drive API:
   - Перейдите в "APIs & Services" > "Library".
   - Найдите и включите "Google Sheets API".
   - Найдите и включите "Google Drive API".

## Шаг 2: Настройка OAuth Consent Screen
1. Перейдите в "APIs & Services" > "OAuth consent screen".
2. Выберите "External" (для личного использования).
3. Заполните:
   - **App name**: Например, "Life OS Sheets".
   - **User support email**: Ваш email.
   - **Developer contact information**: Ваш email.
4. Нажмите "Save and Continue".
5. В разделе "Scopes" добавьте:
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/drive`
6. Нажмите "Save and Continue".
7. В разделе "Test users" (появится после сохранения) нажмите "Add users" и введите ваш email (svaaugust@gmail.com).
8. Нажмите "Save and Continue".
9. Перейдите в раздел "Audience" и нажмите "Publish app" > "Publish" для режима тестирования.

## Шаг 3: Создание OAuth Credentials
1. Перейдите в "APIs & Services" > "Credentials".
2. Нажмите "Create Credentials" > "OAuth 2.0 Client IDs".
3. Выберите "Desktop application".
4. Скачайте файл `credentials.json` и разместите в `src/life_os/config/credentials.json`.

## Шаг 4: Запуск
1. Удалите файл `token.json` в корне проекта (если есть), чтобы переавторизоваться.
2. Запустите `python main.py` — откроется браузер для авторизации. Таблицы будут в вашем личном Drive.

## Примечания
- Нет лимита 15 ГБ — используйте ваше хранилище.
- Если браузер блокирует, проверьте статус в Console (может быть "Pending review").
- Для продакшена пройдите верификацию.