import requests
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=1)

bot_token = '7400359196:AAEgna8tDMaMUI92-xkeDU-jMQap_TutUAw'  # Replace with your bot's API token
chat_id = '965690681'      # Replace with your chat ID

def send_notification(message):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': message}
    executor.submit(requests.post, url, data=payload)