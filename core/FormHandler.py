import asyncio
from bale import CallbackQuery, MenuKeyboardButton, MenuKeyboardMarkup, Message,InlineKeyboardMarkup,InlineKeyboardButton,InputFile
import os 
from datetime import datetime

class Form_Handler:

    def __init__(self,bot,db_manager,inst_files,form_files,form_inst_files):
        
        self.bot = bot
        self.db_manager = db_manager
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.user_states={}

        self.inst_files = inst_files
        self.form_files = form_files
        self.form_inst_files = form_inst_files

    async def cleanup_inactive_forms(self): # شبیه به garbage collector کار میکنه

        while True:
            now = datetime.now()

            to_delete = []

            for user_id, state in self.user_states.items():
                if (now - state["last_activity"]).total_seconds() > 86400:  # 24 ساعت
                    to_delete.append(user_id)

            for user_id in to_delete:
                chat_id = self.user_states[user_id]["chat_id"]
                await self.bot.send_message(chat_id, "⏳ فرم به دلیل عدم فعالیت لغو شد.")
                del self.user_states[user_id]

            await asyncio.sleep(86400)  # هر 24 ساعت بررسی کن'



    async def restart(self,bot,id):
        
        keyboard = MenuKeyboardMarkup()

        keyboard.add(MenuKeyboardButton("آئین نامه‌ها"))
        keyboard.add(MenuKeyboardButton("فرم‌ها"))
        keyboard.add(MenuKeyboardButton("گزارش ‌گیری"))
        print("Restarting main menu...")

        await bot.send_message(id, "یکی از گزینه‌ها را انتخاب کنید: ",components=keyboard)  



    async def Start_New_Form(self,form_db,questions,callback): # شروع فرم جدید
            

            message = callback.message
            user_id = callback.from_user.id
            chat_id = message.chat.id

            if user_id in self.user_states: #اگر کاربر جدید نیست و فرم فعال داشته
                del self.user_states[user_id]
                await self.bot.send_message(chat_id,"فرم قبلی لغو شد.")
                

            self.user_states[user_id] = {
                    "chat_id": chat_id,
                    "form_db": form_db,
                    "questions": questions,
                    "index": 0,
                    "answer": {},
                    "last_activity":datetime.now()
                }
                        
            await self.ask_next_question(user_id)



    async def ask_next_question(self, user_id):

        state = self.user_states[user_id]
        index = state["index"]
        questions = state["questions"]

        if index >= len(questions):
            await self.finish_form(user_id)
            print("form is finished...")
            return 

        question = questions[index]
        
        if question[2]:  # تولید دکمه برای سوال تستی و ارسال آن
            keyboard = InlineKeyboardMarkup()
            for i,item in enumerate(question[2]):
                keyboard.add(InlineKeyboardButton(item, callback_data=item),row=i)

            await self.bot.send_message(state["chat_id"], question[0], components=keyboard)

        else:# ارسال سوال تشریحی
            await self.bot.send_message(state["chat_id"], question[0])




    async def handle_message(self, message: Message):

        user_id = message.from_user.id
        chat_id = message.chat.id
       

        if user_id not in self.user_states: # بررسی میکنیم که پیام دریافت شده مربوط به فرم کاربر قبلی بوده یا ربطی نداره
             return False

        state = self.user_states[user_id]
        question = state["questions"][state["index"]]

        if message.content and message.content.strip() == "لغو فرم":
            await self.bot.send_message(state["chat_id"], "فرم لغو شد.")
            del self.user_states[user_id]
            await self.restart(self.bot, state["chat_id"])
            return True
        
        elif message.content and message.content.strip() == "برگشت به سوال قبل":

            if  state["index"] > 0 :

                state["index"] -= 1
                await self.ask_next_question(user_id)
                
            else:
                await self.bot.send_message(state["chat_id"],"شما در سوال اول هستید.")
                await self.ask_next_question(user_id)

            
            return True



        if question[2]:  #  اگر سوال تستی بود و پیام متنی داد
            await self.bot.send_message(state["chat_id"], "فقط یکی از گزینه‌ها را انتخاب کنید.")
            return True
        
        
        file_id = None
        file_extension = ""

        #  document
        if message.document:
            file_id = message.document.file_id
            file_extension = os.path.splitext(message.document.file_name)[1]

        #  photo
        elif message.photos:
            ext = os.path.splitext(message.photos[-1].file_name)[1].lower()
            allowed_extensions = [".jpg", ".jpeg", ".png"]
            
            if ext not in allowed_extensions:
                await self.bot.send_message(state["chat_id"], "فرمت فایل مجاز نیست.")
                return True

            file_id = message.photos[-1].file_id
            file_extension = ext
        
        #  video
        elif message.video:
            file_id = message.video.file_id
            file_extension = ".mp4"

    # اگر فایل بود
        if file_id:
           
            file_content = await self.bot.get_file(file_id)

            upload_dir = os.path.join(self.BASE_DIR, "docs", "attachments")
            os.makedirs(upload_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{question[1]}_{user_id}_{timestamp}{file_extension}"
            file_path = os.path.join(upload_dir, file_name)
            
            with open(file_path, "wb") as f:
                f.write(file_content)

            
            state["answer"][question[1]] = file_path
            await self.bot.send_message(state["chat_id"], "✅ فایل ذخیره شد.")
            state["index"] += 1
            await self.ask_next_question(user_id)
            return True



        elif message.content.strip() in self.form_inst_files:

        
            # form_inst_files_addr = os.path.join(self.BASE_DIR, "docs", "forms_inst_names.json")

            # with open(form_inst_files_addr, 'r', encoding='utf-8') as f:
            #     form_inst_files = json.load(f)

            await self.bot.send_document(
                chat_id=chat_id,
                document=InputFile(self.form_inst_files[message.content.strip()])
            )

            await self.ask_next_question(user_id)
            return True


        # اگر متن معمولی بود
        elif message.content:

            if state["form_db"] == "R_and_D_form" and state["index"] == 0: # بررسی یکتا بودن عنوان پروژه تحقیق و توسعه وارد شده
                
               isUnique = await self.db_manager.check_isUnique("project_title",message.content,"R_and_D_form")
               
               if not isUnique:
                    
                    await self.bot.send_message(state["chat_id"], "عنوان پروژه نباید تکراری باشد.")
                    await self.ask_next_question(user_id)
                    return True 
               else:
               
                state["answer"][question[1]] = message.content.strip()
                state["index"] += 1

                await self.ask_next_question(user_id)
                
                return True


            else:
                state["answer"][question[1]] = message.content.strip()
                state["index"] += 1

                await self.ask_next_question(user_id)
                
                return True

        else:
            await self.bot.send_message(state["chat_id"], "پاسخ نامعتبر است.")
            return True 

       

    async def handle_callback(self, callback: CallbackQuery):

        user_id = callback.from_user.id

        if user_id not in self.user_states: # بررسی میکنیم که اگه پیام دریافتی مربوط به کاربری که در حال پرکردن فرم بوده نیست ، ردش کنیم
            return False


        state = self.user_states[user_id]
        question = state["questions"][state["index"]]

        if not question[2]: #اگر سوال تستی نیست ولی کاربر یه دکمه ای رو زده
            return True

        if callback.data not in question[2]:  #اگه سوال تستیه ولی دکمه ی نامربوط به سوال زده شده
            await self.bot.send_message(state["chat_id"], "گزینه نامعتبر است.")
            return True

        state["answer"][question[1]] = callback.data
        state["index"] += 1

        await self.ask_next_question(user_id)

        return True




    async def finish_form(self, user_id):

        state = self.user_states[user_id]

        try:

            
            if state["form_db"] != "R_and_D_form":
                result = await self.db_manager.insert_data(state["form_db"], state["answer"])
                if result:
                    await self.bot.send_message(state["chat_id"], "✅ فرم با موفقیت ثبت شد.")
                    del self.user_states[user_id]
                    await self.restart(self.bot, state["chat_id"])
                else:
                    await self.bot.send_message(state["chat_id"], "مشکل در ذخیره سازی فرم...")
                    del self.user_states[user_id]
                    await self.restart(self.bot, state["chat_id"])
            


            elif state["form_db"] == "R_and_D_form":
                
                result = await self.db_manager.insert_data_into_r_and_d_form(state["answer"])
                
                if result:
                    await self.bot.send_message(state["chat_id"], "✅ فرم با موفقیت ثبت شد.")
                    del self.user_states[user_id]
                    await self.restart(self.bot, state["chat_id"])
                else:
                    await self.bot.send_message(state["chat_id"], "مشکل در ذخیره سازی فرم...")
                    del self.user_states[user_id]
                    await self.restart(self.bot, state["chat_id"])
            

        except Exception as e:
            print(f"Database Error: {e}")
            await self.bot.send_message(state["chat_id"], "خطا در ذخیره سازی.")




