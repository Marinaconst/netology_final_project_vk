from os import environ as env
from dotenv import load_dotenv

load_dotenv()

access_token = env.get('VK_ACCESS_TOKEN')
ya_disk_token = env.get('YA_DISK_TOKEN')
