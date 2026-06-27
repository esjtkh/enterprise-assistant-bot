from bale import MenuKeyboardMarkup,MenuKeyboardButton

class R_and_D_form:

    def __init__(self,db_manager):

        self.db_manager = db_manager
        #ستون اول صورت سوال
        #ستون دوم نام ستون دیتابیس
        #ستون سوم گزینه های سوال تستی
        self.questions = [
            ("عنوان پروژه / قطعه:", "project_title",""),
            ("هدف پروژه:", "purpose",["بهبود کیفیت چاپ", "بهبود دقت ابعادی", "کاهش مصرف ماده", "افزایش استحکام مکانیکی", "کاهش زمان چاپ", "توسعه پارامتر چاپ قطعه جدید", "سایر"]),
            ("کاربرد قطعه: ", "application",["صنعتی", "پزشکی", "نمونه سازی", "تحقیقاتی"]),
            ("نام مشتری/واحد داخلی: ", "customer_name",""),
            ("تاریخ شروع پروژه: ", "start_date",""),
            ("شماره پروژه R&D: ", "project_number",""),
            ("نام مسئول پروژه: ", "project_manager",""),
            ("نوع پرینتر: ", "printer_type",""),
            ("نوع ماده مصرفی: ", "material_type",""),
            ("قطر نازل mm: ", "nozzle_diameter",""),
            ("شرایط محیطی (تقریبی):", "environmental_conditions",""),   # 0-10
            ############################################################################################
            ########################### پارامترهای متغیر ##################################################
            ("پارامترهای متغیر\n\nدمای نازل °C", "nozzle_temperature",""), # 11-27
            ("دمای بستر °C", "bed_temperature",""),
            ("سرعت چاپ mm/s", "print_speed",""),
            ("ارتفاع لایه mm", "layer_height",""),
            ("درصد پرشدگی %", "infill_percentage",""),
            ("نوع الگوی پرشدگی: ", "infill_pattern",["خطی", "مثلثی", "مشبک", "مارپیچ", "سایر"]),
            ("سرعت فن %", "fan_speed",""),
            ("جهت‌گیری قطعه در هنگام چاپ: ", "part_orientation",""),
            ("زمان چاپ:","time",""),
            ("میزان مصرف ماده (گرم)","material_consumption_rate",""),
            ("وضعیت چاپ","print_status",["موفق","ناموفق"]),
            ("ارزیابی نتایج هر آزمون\n\n کیفیت ظاهری:","appearance_quality",["عالی","قابل قبول","ضعیف"]),
            ("دقت ابعادی","dimensional_accuracy",["عالی","قابل قبول","ضعیف"]),
            ("استحکام مکانیکی","mechanical_strength",["عالی","قابل قبول","ضعیف"]),
            ("چسبندگی لایه‌ها","layer_adhesiveness",["مناسب","متوسط","ضعیف"]),
            ("وجود عیوب:","defection_existance",["تاب برداشتگی","لایه لایه شدن","ترک","شکست","سایر"]),
            ("توضیحات فنی:","technical_description",""),
            ############################################################################################
            ("تحلیل نتایج و مقایسه آزمون‌ها\n\nپارامترهای موثر شناسایی شده:","effective_parameters",""), #28-33
            ("بهترین ترکیب پارامترها(پیشنهادی):","best_parameter_combination",""),
            ("دلایل انتخاب ترکیب بهینه:","choice_reasons",""),
            ("نتیجه نهایی پروژه R&D\n\nوضعیت پروژه:","project_status",["موفق","ناموفق","نیازمند بررسی بیشتر"]),
            ("پارامترهای نهایی تایید شده برای تولید/خدمات چاپ","final_parameters",""),
            ("این پارامترها به چه عنوانی مورد استفاده قرار میگیرند؟","parameters_usecase",["مرجع خدمات چاپ","ورودی طراحی محصول","دستورالعمل چاپ"])
        ]
    


    
    async def restart(self,bot,id):

        keyboard = MenuKeyboardMarkup()

        keyboard.add(MenuKeyboardButton("آئین نامه‌ها"))
        keyboard.add(MenuKeyboardButton("فرم‌ها"))
        keyboard.add(MenuKeyboardButton("گزارش ‌گیری"))
        print("Restarting main menu...")

        await bot.send_message(id, "یکی از گزینه‌ها را انتخاب کنید: ",components=keyboard)  


    async def show_form(self,bot, callback,form_handler):

        await form_handler.Start_New_Form("R_and_D_form",self.questions[0:28],callback) 

    
    async def  add_new_test_R_and_D_project(self,project_title,callback,form_handler):
        
        await form_handler.Start_New_Form(project_title,self.questions[11:28],callback) 


    
    async def  add_final_R_and_D_project_data(self,project_title,callback,form_handler):

        await form_handler.Start_New_Form(project_title,self.questions[28:34],callback) 



    
