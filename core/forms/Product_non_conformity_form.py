from bale import CallbackQuery, MenuKeyboardButton, MenuKeyboardMarkup, Message,InlineKeyboardMarkup,InlineKeyboardButton,InputFile
import os 


print(os.getcwd())

print(os.path.dirname(os.path.abspath(__file__)) )


class Product_non_conformity_form:
    
    def __init__(self,db_manager):
        self.db_manager=db_manager
        self.BASE_DIR =os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        self.questions=[
            
            ("شماره عدم انطباق", "non_conformity_number", ""),
            # ("تاریخ ثبت", "registration_date", ""),
            ("نام ثبت کننده/واحد ثبت کننده", "registrant_name", ""),
            ("محل وقوع عدم انطباق", "non_conformity_location", ["خط تولید دستگاه","خط تولید قطعات","تکمیل و پس پردازش","خدمات پس از فروش","مشتری"]),
            ("نوع محصول/کد محصول","product_type_code", ""),
            ("شماره سری ساخت/سفارش", "order_serial", ""),
            ("مقدار یا تعداد کل محصول","total_quantity", ""),
            ("مقدار یا تعداد غیرمنطبق","total_non_conform_quantity",""),
            ("نوع عدم انطباق","non_conformity_type",["ابعادی","ظاهری","عملکردی","بسته‌بندی","برچسب‌گذاری","مواد اولیه","سایر"]),
            ("شرح دقیق مشکل","problem_description", ""),
            ("عکس یا مستندات مرتبط با عدم انطباق (در صورت وجود)","non_conformity_docs", ""),
            ("کشف شده توسط : ","explored_by",["تولید","QA","QC","مشتری","سایر"]),
            ("مرحله کشف :","explore_phase",["حین تولید","قبل از تحویل","پس از تحویل","خدمات پس از فروش"]),
            ("بررسی اولیه توسط :","initial_review_by",""),
            ("تصمیم اولیه در مورد محصول غیرمنطبق :","initial_decision",["اصلاح ابعاد قطعه","تغییر تنظیمات اسلایسر","ترمیم مشکلات ظاهری و پرداخت","اسقاط","مرجوعی به تامین کننده","استفاده مجدد پس از تایید","سایر"]),
            ("مسئول اجرای تصمیم :","decision_responsible", ""),
            ("تاریخ اقدام اولیه :","initial_action_date", ""),
            ("تحلیل علت ریشه‌ای (درصورت نیاز) : ","root_cause_analysis", ""),
            ("ابزار تحلیل علت","analysis_tool", ["Ishikawa","5Why","بررسی فرآیند","سایر"]),
            ("علت اصلی بروز عدم انطباق :","root_cause", ""),
            ("پیشنهاد اقدام اصلاحی :","corrective_action", ""),
            ("ارجاع به فرم اقدام اصلاحی :","corrective_action_form", ""),
            ("اقدام اصلاحی انجام شده : ","corrective_action_done", ""),
            ("واحد اجراکننده","corrective_action_responsible", ""),
            ("تاریخ اجرای اقدام اصلاحی :","corrective_action_date", ""),
            ("تایید اثربخشی اقدام اصلاحی :","corrective_action_effectiveness", ["موثر","نیاز به اقدام مجدد دارد"]),
            ("تاریخ بستن عدم انطباق :","closure_date", ""),
            ("وضعیت نهایی","final_status", ["در حال پیگیری","بسته شده"])                  
            
            ]


    # async def restart(self,bot,id):
    #     keyboard = MenuKeyboardMarkup()

    #     keyboard.add(MenuKeyboardButton("آئین نامه‌ها"))
    #     keyboard.add(MenuKeyboardButton("فرم‌ها"))
    #     keyboard.add(MenuKeyboardButton("گزارش ‌گیری"))
    #     print("Restarting main menu...")

    #     await bot.send_message(id, "یکی از گزینه‌ها را انتخاب کنید: ",components=keyboard)  


    async def show_form(self, bot,callback,form_handler):

        await form_handler.Start_New_Form("product_non_conformity_form",self.questions,callback) 



        # user_id = callback.from_user.id
        # chat_id = callback.message.chat.id
        # form_data = {}
        # form_data['user_id'] = user_id  # ذخیره user_id برای استفاده در ذخیره‌سازی نهایی

        # def check(m: Message):
        #      return (
        #          m.author.id == user_id and
        #          m.chat.id == chat_id and
        #         (m.content or m.photos or m.document or m.video) # پذیرش متن یا انواع فایل

        #             )
        # def check_callback(cb: CallbackQuery):
        #     return cb.from_user.id == user_id and cb.message.chat.id == chat_id

        # index = 0

        # while index < len(self.questions): #حلقه روی سوالات
            
        #     question = self.questions[index]

        #     if (question[2]): #ارسال سوال تستی در صورت وجود
                
        #         keyboard = InlineKeyboardMarkup()
         
        #         for i, item in enumerate(question[2]):

        #             keyboard.add(InlineKeyboardButton(item, callback_data=item),row=i)  # ایجاد دکمه برای تست ها     

        #         keyboard.add(InlineKeyboardButton("لغو فرم", callback_data="cancel"),row=len(question[2])) # دکمه لغو در انتهای سوالات تستی
                
        #         await bot.send_message(chat_id, question[0] ,components=keyboard)   

        #     else: # ارسال سوال تشریحی در صورت وجود

        #         await bot.send_message(chat_id, question[0])
            
        #     try:
        #      ################################## انتظار برای دریافت فایل #############################################################
        #         if question[2]: 
        #         # اگر سوال تستی بود، منتظر پاسخ دکمه ای باش

        #             response = await bot.wait_for("callback", check=check_callback , timeout=600.0)

        #             if response.data == "cancel":
        #                 await bot.send_message(chat_id, "فرم ثبت عیب و تعمیر دستگاه لغو شد.")
        #                 await self.restart(bot,chat_id)
        #                 return
        #             else:
        #                 form_data[question[1]] = response.data.strip() # ذخیره پاسخ دکمه ای
        #                 index += 1 # رفتن به سوال بعدی
        #         else:
        #             response = await bot.wait_for("message", check=check, timeout=600.0)
                    
                    
        #             file_id = None
        #             file_extension = ""

        #             if response.document:
                        
        #                 file_id = response.document.file_id
        #                 file_extension = os.path.splitext(response.document.file_name)[1]
                    
        #             elif response.photos:
        #                 # طبق مستندات، photo لیستی از سایزهاست، آخرین مورد بزرگترین است

        #                 ext = os.path.splitext(response.photos[-1].file_name)[1].lower()
                       
        #                 allowed_extensions = [".jpg", ".jpeg", ".png"]

        #                 if ext not in allowed_extensions:
        #                        await bot.send_message(chat_id, "فرمت فایل مجاز نیست.")
        #                        continue
                        
        #                 file_id = response.photos[-1].file_id
        #                 file_extension = ext

        #             elif response.video:
        #                 file_id = response.video.file_id
        #                 file_extension = ".mp4"   

        #             if file_id:
                        
        #                 # ۱. دریافت اطلاعات فایل از سرور بله (طبق صفحه ۱۰ و ۱۱ فایل Bot)
        #                 # متد get_file محتوای فایل را به صورت bytes برمی‌گرداند

        #                 file_content = await bot.get_file(file_id)
        #                 upload_dir = os.path.join(self.BASE_DIR, "docs", "attachments")

        #                 if not os.path.exists(upload_dir):
        #                     os.makedirs(upload_dir)

        #                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        #                 file_name = f"{question[1]}_{user_id}_{timestamp}{file_extension}"
        #                 file_path = os.path.join(upload_dir, file_name)
                        
        #                 with open(file_path, "wb") as f:
        #                     f.write(file_content)
                        
        #                 # ذخیره "مسیر فایل" در دیتابیس به جای متن
        #                 form_data[question[1]] = file_path
        #                 await bot.send_message(chat_id, "✅ فایل با موفقیت دریافت و ذخیره شد.")
        #                 index += 1

        #             elif response.content and response.content.strip()  == "لغو فرم":
        #                 await bot.send_message(chat_id, "فرم ثبت عیب و تعمیر دستگاه لغو شد.")
        #                 await self.restart(bot,chat_id)
        #                 return
                    
        #             elif response.content and response.content.strip() == "دستورالعمل عدم انطباق محصول":
                    
        #                 form_inst_files_addr = os.path.join(self.BASE_DIR, "docs", "forms_inst_names.json")

        #                 with open(form_inst_files_addr ,'r',encoding='utf-8') as f:
        #                     form_inst_files = json.load(f)
                        
        #                 await bot.send_document(chat_id=chat_id,document = InputFile(form_inst_files [response.content.strip()]))
        #                 continue # ارسال مجدد سوال بعد از ارسال دستورالعمل برای پاسخ دهی کاربر
        #             else:
        #                 form_data[question[1]] = response.content.strip() # ذخیره پاسخ متنی
        #                 index += 1 # رفتن به سوال بعدی
        #     except asyncio.TimeoutError:
        #         await bot.send_message(chat_id, "زمان پاسخگویی به سوالات به پایان رسید. لطفا دوباره تلاش کنید.")
        #         await self.restart(bot,chat_id)
        #         return
        # try:
        #     self.db_manager.insert_data("product_non_conformity_form", form_data)  # ذخیره داده‌های فرم در پایگاه داده   
        #     await bot.send_message(chat_id, "✅ فرم با موفقیت در دیتابیس مسترپرینتر ثبت شد.")
        #     await self.restart(bot,chat_id)
        #     return
        
        # except Exception as e:
        #        print(f"Database Error: {e}")
        #        await bot.send_message(chat_id, "خطا در ذخیره سازی پاسخ شما. لطفا به پشتیبانی اطلاع دهید.")
        #        await self.restart(bot,chat_id)
        #        return

