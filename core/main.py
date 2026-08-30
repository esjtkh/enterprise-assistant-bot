import os
from dotenv import load_dotenv
from bale import Bot, Message, MenuKeyboardMarkup, MenuKeyboardButton,InputFile,InlineKeyboardMarkup,InlineKeyboardButton
import json ,asyncio
import forms.R_and_D_form as R_and_D
from database_manager import DatabaseManager
from report_manager import ReportManager
import forms.Defect_and_repair_registration_form as defect_form
import forms.Product_non_conformity_form as product_non_conformity_form
import FormHandler



async def file_sender(bot :Bot,chat_id, file_path):

    if not os.path.exists(file_path):
        await bot.send_message(chat_id, "خطا در ایجاد فایل گزارش.")
        return

    if os.path.getsize(file_path) == 0:
        await bot.send_message(chat_id, "خطا: فایل گزارش خالی است.")
        return

    try:
        with open(file_path, "rb") as f:
            await bot.send_document(
                chat_id=chat_id,
                document=InputFile(f, file_name=os.path.basename(file_path))
            )
    except Exception as e:
        await bot.send_message(chat_id, f"خطا در ارسال فایل: {e}")


async def handle_instructions(bot:Bot, chat_id, data,inst_files):

    await bot.send_document(
        chat_id,
        InputFile(inst_files[data][0])
    )


######### show form #############

async def handle_show_new_form(bot:Bot , message:Message , form_files: dict ):

    keyboard = InlineKeyboardMarkup()

    for i, k in enumerate(form_files.keys(), 1):
        keyboard.add(InlineKeyboardButton(k, callback_data=k), row=i)

    await message.reply("لطفا یکی از فرم‌ها را انتخاب کنید", components=keyboard)


async def handle_show_selected_form(bot:Bot , callback, data , db_manager:DatabaseManager , form_handler:FormHandler.Form_Handler):

    message = callback.message

    if data == "فرم ثبت عیب و تعمیر دستگاه":

        keyboard = MenuKeyboardMarkup()
        keyboard.add(MenuKeyboardButton("دستورالعمل ثبت عیب و تعمیر دستگاه"))
        keyboard.add(MenuKeyboardButton("برگشت به سوال قبل"))
        keyboard.add(MenuKeyboardButton("لغو فرم"))

        await message.reply("در صورت تمایل میتوانید به سوال قبل برگردید، فرم را لغو یا دستورالعمل فرم را مشاهده کنید.",components=keyboard)

        form = defect_form.Defect_And_Repair_Registration_Form(db_manager)
        await form.show_form( bot,callback,form_handler)

    elif data == "فرم ثبت عدم انطباق محصول":

        keyboard = MenuKeyboardMarkup()
        keyboard.add(MenuKeyboardButton("دستورالعمل عدم انطباق محصول"))
        keyboard.add(MenuKeyboardButton("برگشت به سوال قبل"))
        keyboard.add(MenuKeyboardButton("لغو فرم"))

        await message.reply(
            "در صورت تمایل میتوانید به سوال قبل برگردید، فرم را لغو یا دستورالعمل فرم را مشاهده کنید.",
            components=keyboard
        )

        form = product_non_conformity_form.Product_non_conformity_form(db_manager)
        await form.show_form(bot, callback,form_handler)


    elif data == "فرم تحقیق و توسعه":

        keyboard = MenuKeyboardMarkup()

        keyboard.add(MenuKeyboardButton("برگشت به سوال قبل"))
        keyboard.add(MenuKeyboardButton("لغو فرم"))
        await message.reply(
            "در صورت تمایل میتوانید به سوال قبل برگردید یا فرم را لغو کنید.",
            components=keyboard
        )
        form = R_and_D.R_and_D_form(db_manager)
        await form.show_form(bot,callback,form_handler)        


######### edit form #############

async def handle_edit_form(message:Message , form_files:dict):

    keyboard = InlineKeyboardMarkup()

    for i, k in enumerate(form_files.keys(), 1):
        keyboard.add(
            InlineKeyboardButton(k, callback_data=f"edit_form_{k}"),
            row=i
        )

    await message.reply("کدام فرم را می‌خواهید ویرایش کنید؟", components=keyboard)


async def handle_edit_selected_form(message:Message, data , db_manager:DatabaseManager): ######## ناقص

    keyboard = InlineKeyboardMarkup()
    form_name = data.replace("edit_form_", "")


    if form_name == "فرم تحقیق و توسعه":

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("افزودن اطلاعات آزمایش جدید",callback_data="add_new_test_R_and_D_project_data"))
        keyboard.add(InlineKeyboardButton("افزودن اطلاعات نهایی پروژه",callback_data="add_final_R_and_D_project_data"))
        await message.reply("چه ویرایشی می‌خواهید انجام دهید؟",components=keyboard)


       
    elif form_name == "فرم ثبت عیب و تعمیر دستگاه":
        pass
    
    
    elif form_name == "فرم ثبت عدم انطباق محصول":
        pass


async def handle_choose_edit_action_r_and_d_project(message:Message , data , db_manager:DatabaseManager):
     
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("افزودن آزمون جدید",callback_data="add_new_test_R_and_D_project_data"))
        keyboard.add(InlineKeyboardButton("افزودن اطلاعات نهایی پروژه",callback_data="add_final_R_and_D_project_data"))
        await message.reply("چه ویرایشی می‌خواهید انجام دهید؟",components=keyboard)




async def handle_add_new_test_or_final_R_and_D_project_data(message:Message, data, form_handler, db_manager):
    
    form_names = await db_manager.fetch_projects_names("R_and_D_form")

    keyboard = InlineKeyboardMarkup()
    

    if data =="add_new_test_R_and_D_project_data":

        for name in form_names:
            keyboard.add(
                    InlineKeyboardButton(
                        name,
                        callback_data=f"add_new_test_R_and_D_project_data_{name}"
                    )
                )
            
    elif data == "add_final_R_and_D_project_data":
          
          for name in form_names:
            keyboard.add(
                    InlineKeyboardButton(
                        name,
                        callback_data=f"add_final_R_and_D_project_data_{name}"
                    )
                )
    
    await message.reply("کدام پروژه را می‌خواهید ویرایش کنید؟", components=keyboard)



######### report ################

async def handle_selected_form_report(message, data, db_manager:DatabaseManager,  report_manager:ReportManager):

    if data == "R_and_D_reports":

        keyboard = InlineKeyboardMarkup()

        form_names = await db_manager.fetch_projects_names("R_and_D_form")

        for name in form_names:
            keyboard.add(
                InlineKeyboardButton(
                    name,
                    callback_data=f"R_and_D_report_{name}"
                )
            )

        await message.reply(
            "گزارش کدام پروژه را می‌خواهید؟",
            components=keyboard
        ) 

    else:
        data = data.replace("reports","form")
        file_path = await report_manager.create_pdf(f"{data}")
        await file_sender(
            bot,
            message.chat.id,
            file_path
        )


async def handle_R_and_D_report(callback, data,report_manager:ReportManager):

    chat_id = callback.message.chat.id
    project_title = data.replace("R_and_D_report_", "")

    file_path = await report_manager.create_pdf("R_and_D_form", project_title)
    await file_sender(bot,chat_id, file_path)
   

########################################################################################################################


  
db_manager = DatabaseManager()
 
report_manager =  ReportManager(db_manager)



load_dotenv()

BASE_DIR =os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
inst_files_addr = os.path.join(BASE_DIR, "docs", "inst_names.json")
form_files_addr = os.path.join(BASE_DIR, "docs", "forms_names.json")
form_inst_files_addr = os.path.join(BASE_DIR, "docs", "forms_inst_names.json")

                
forms_reports_names_addr = os.path.join(BASE_DIR, "docs", "forms_reports_names.json")

API_TOKEN = os.getenv("API_TOKEN")


with open(inst_files_addr ,'r',encoding='utf-8') as f:
        inst_files = json.load(f)

with open(form_files_addr ,'r',encoding='utf-8') as f:
        form_files = json.load(f)

with open(forms_reports_names_addr ,'r',encoding='utf-8') as f:
        forms_reports_names = json.load(f)

with open(form_inst_files_addr, 'r', encoding='utf-8') as f:
                    form_inst_files = json.load(f)

if not API_TOKEN:
        print("no api_token found")
        exit(0)
bot = Bot(token=API_TOKEN)

form_handler = FormHandler.Form_Handler(bot, db_manager,inst_files,form_files,form_inst_files)



@bot.event
async def on_ready():
        print("robot is running successfully...")
        asyncio.create_task(form_handler.cleanup_inactive_forms()) # شبیه به garbage_collector کار میکنه برای فرم های ناقص رها شده


@bot.event
async def on_message(message: Message):
        
        
        handled = await form_handler.handle_message(message) #بررسی کن که مربوط به پاسخ فرم هاست یا ربطی نداره
        if handled:
            return


        if not message.content  is None:
            text = message.content.strip()
        else:
            text = ""

        if text == "/start" or text == "لغو فرم":

            keyboard = MenuKeyboardMarkup()

            keyboard.add(MenuKeyboardButton("آئین نامه‌ها"))
            keyboard.add(MenuKeyboardButton("فرم‌ها"))
            keyboard.add(MenuKeyboardButton("گزارش ‌گیری"))
            

            await message.reply(
            "🤖 به دستیار هوشمند سازمان خوش آمدید\n\n"
            "این سامانه با هدف دیجیتالی‌سازی فرآیندهای سازمانی، کاهش زمان انجام امور و افزایش دقت در ثبت و مدیریت اطلاعات طراحی شده است.\n\n"
            "📋 امکانات سامانه:\n"
            "• ثبت، ویرایش و پیگیری فرم‌های سازمانی\n"
            "• تولید گزارش‌های حرفه‌ای در قالب PDF\n"
            "• دسترسی سریع به آیین‌نامه‌ها و مستندات\n"
            "• مدیریت یکپارچه اطلاعات و سوابق\n\n"
            "✨ این ربات متناسب با ساختار هر سازمان قابل سفارشی‌سازی است و امکان افزودن فرم‌ها، گزارش‌ها، گردش کار، داشبوردهای مدیریتی و قابلیت‌های هوشمند بر اساس نیاز مجموعه وجود دارد.\n\n"
            "👇 لطفاً یکی از گزینه‌های زیر را انتخاب کنید.",
            components=keyboard
            )     

        elif text == "آئین نامه‌ها":
            
            keyboard = InlineKeyboardMarkup()
            i = 1
            for i,(k,v) in enumerate(inst_files.items(),1):
                
                keyboard.add(InlineKeyboardButton(k,callback_data=v[1]),row = i)
                i += 1
            
            await message.reply("لطفا یکی از آئین نامه‌ها را انتخاب کنید", components=keyboard)  

        elif text == "فرم‌ها" :

            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("فرم جدید",callback_data="فرم جدید"),row=1)
            keyboard.add(InlineKeyboardButton("ویرایش فرم موجود",callback_data="ویرایش فرم موجود"),row=2)
            await message.reply("یک گزینه را انتخاب کنید.",components=keyboard)
    

        elif text == "گزارش ‌گیری" :
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("گزارش‌ فرم ثبت عیب و تعمیر دستگاه",callback_data="defect_and_repair_registration_reports"),row=1)
            keyboard.add(InlineKeyboardButton("گزارش‌ فرم عدم انطباق محصول",callback_data="product_non_conformity_reports"),row=2)
            keyboard.add(InlineKeyboardButton("گزارش‌ فرم تحقیق و توسعه",callback_data="R_and_D_reports"),row=3)


            await message.reply("یکی از گزینه‌ها را انتخاب کنید: ",components=keyboard)



@bot.event
async def on_callback(callback):   
        
        handled = await form_handler.handle_callback(callback)

        if handled: # اگر پاسخ سوالات فرم باشد در تابع بالا بهش رسیدگی شده و دیگه نیاز به کاری نیست
            return


        data = callback.data
        message = callback.message
        chat_id = message.chat.id
        user_id = callback.from_user.id

        # ===== ROUTER =====

        if data == "فرم جدید":
            
            await handle_show_new_form(bot,message,form_files)

        elif data == "ویرایش فرم موجود":

            await handle_edit_form(message,form_files)

        elif data.startswith("edit_form_"):
            await handle_edit_selected_form(message, data,db_manager) 
        
        elif data.startswith("add_final_R_and_D_project_data_"):
            
            r_and_d = R_and_D.R_and_D_form(db_manager)
            project_title = data.replace("add_final_R_and_D_project_data_","")
            await r_and_d.add_final_R_and_D_project_data(project_title,callback,form_handler)

        elif data.startswith("add_new_test_R_and_D_project_data_"):
           
            r_and_d = R_and_D.R_and_D_form(db_manager)
            project_title = data.replace("add_new_test_R_and_D_project_","")
            await r_and_d.add_new_test_R_and_D_project(project_title,callback,form_handler)

        elif data in inst_files:
            await handle_instructions(bot, chat_id, data, inst_files)

        elif data in form_files:
            await handle_show_selected_form(bot, callback, data, db_manager, form_handler)

        elif data in forms_reports_names:
            await handle_selected_form_report(message, data , db_manager, report_manager)

        elif data.startswith("R_and_D_report_"):
            await handle_R_and_D_report(callback, data , report_manager)
        


bot.run()

