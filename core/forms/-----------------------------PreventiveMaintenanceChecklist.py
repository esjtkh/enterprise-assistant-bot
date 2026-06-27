import os
from dotenv import load_dotenv
from bale import Bot, Message, MenuKeyboardMarkup, MenuKeyboardButton,InputFile,InlineKeyboardMarkup,InlineKeyboardButton
import json

load_dotenv()

BASE_DIR =os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
inst_files_addr = os.path.join(BASE_DIR, "docs", "inst_names.json")

API_TOKEN = os.getenv("API_TOKEN")

with open(inst_files_addr ,'r',encoding='utf-8') as f:
    inst_files = json.load(f)

if not API_TOKEN:
    print("no api_token found")
    exit(0)

bot = Bot(token=API_TOKEN)




