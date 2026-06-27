import asyncio
from bale import CallbackQuery, MenuKeyboardButton, MenuKeyboardMarkup, Message,InlineKeyboardMarkup,InlineKeyboardButton,InputFile
import os , json
import FormHandler

class Defect_And_Repair_Registration_Form:

    def __init__(self,db_manager):
        self.db_manager = db_manager
        self.questions = [

        ('نام خود را وارد کنید:', 'user_name',''),
        # قسمت اول هر تاپل : متن سوال
        # قسمت دوم هر تاپل : نام ستون سوال در جدول دیتابیس
        # قسمت سوم هر تاپل : گزینه های سوال تستی در صورت وجود

        # بخش اطلاعات پایه
        ("کد دستگاه را وارد کنید:", "machine_code",""),
        ("محل استقرار دستگاه:", "location",""),
        ("نام اپراتور دستگاه:", "operator",""),
        # ("تاریخ گزارش عیب (مثلا 1402/01/01):", "fault_date",""),
        ("ساعت بروز عیب (مثلا 14:30):", "fault_time",""),

        # بخش اطلاعات تولید
        ("کد سفارش مربوطه:", "order_code",""),
        ("نوع قطعه در حال چاپ:", "part_type",""),
        ("متریال مصرفی:", "material",""),
        ("درصد پیشرفت چاپ را انتخاب کنید: ", "progress_percent",["<25%","25-50%","50-75%",">75%"]),
        ("زمان کارکرد دستگاه قبل از بروز عیب (ساعت):", "uptime_before_fault",""),

        # شرح و دسته‌بندی عیب
        ("شرح عیب مشاهده شده را بنویسید:", "fault_summary",""),
        ("نوع عیب را انتخاب کنید: ", "fault_category",["فن/خنک‌کاری","قطعی برق","توقف کامل","افت کیفیت","محور z","اکسترودر","نرم افزاری" , "سایر"]),
        ("شرح دقیق عیب توسط اپراتور:", "operator_detailed_desc",""),
        ("شرح اقدام اولیه انجام شده توسط اپراتور:", "initial_action",""),

        # تحلیل فنی
        ("علت ظاهری خرابی: ", "apparent_cause",["نرم‌افزاری","مکانیکی","الکتریکی","انسانی"]),
        ("نیاز به تحلیل ریشه‌ای دارد؟ (بله / خیر)", "root_cause_needed",["بله","خیر"]),
        ("روش تحلیل را انتخاب کنید:", "analysis_method",["Ishikawa","5Why"]),
        ("شرح علت اصلی و ریشه‌ای خرابی:", "root_cause_desc",""),

        # اقدامات اصلاحی و زمانی
        ("نوع اقدام انجام شده را انتخاب کنید:\n(تعمیر - تعویض قطعه - کالیبراسیون - بروزرسانی اسلایسر - تعمیر طراحی)", "action_type",["تعمیر","تعویض قطعه","کالیبراسیون","بروزرسانی اسلایسر","تعمیر طراحی"]),
        ("شرح دقیق اقدام انجام شده:", "action_desc",""),
        ("تاریخ شروع تعمیر:", "repair_start_date",""),
        ("تاریخ پایان تعمیر:", "repair_end_date",""),

        # وضعیت نهایی
        ("وضعیت نهایی دستگاه: ", "final_machine_status",["آماده بهره برداری","نیاز به پایش","خارج از سرویس"]),
        ("نتیجه تست پس از تعمیر: ", "test_result",["موفق","ناموفق"])
        ]

        
    async def show_form(self,bot, callback,form_handler):


        await form_handler.Start_New_Form("defect_and_repair_registration_form",self.questions,callback) 