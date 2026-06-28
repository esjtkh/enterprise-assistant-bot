import pandas as pd
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from database_manager import DatabaseManager
import os, json
import jdatetime
import asyncio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image


# برای اضافه کردن واترمارک به هر صفحه
class PDF(FPDF):
    def __init__(self, watermark_path: str,template_path:str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.watermark_path = watermark_path
        self.template_path = template_path
        self.set_margins(15, 45, 15)
          # جلوگیری از ورود متن به فوتر
        self.set_auto_page_break(auto=True, margin=40)


        self.header_width = self.w
        self.header_height = self.h
        
        self.prepare_images()


    def prepare_images(self):
        """
        فقط یکبار ابعاد تصاویر را محاسبه می‌کند.
        """

        # ---------------- Watermark ----------------

        if os.path.exists(self.watermark_path):

            img = Image.open(self.watermark_path)

            w_px, h_px = img.size
            img.close()

            self.watermark_width = 80
            self.watermark_height = self.watermark_width * h_px / w_px

            self.watermark_x = (self.w - self.watermark_width) / 2
            self.watermark_y = (self.h - self.watermark_height) / 2

        else:

            self.watermark_width = None

        

    def header(self):

        # ---------- Header ----------

        if self.header_width:

            self.image(
                self.template_path,
                x=0,
                y=0,
                w=self.header_width,
                h=self.header_height
            )

        # ---------- Watermark ----------

        if self.watermark_width:

            self.image(
                self.watermark_path,
                x=self.watermark_x,
                y=self.watermark_y,
                w=self.watermark_width,
                h=self.watermark_height
            )

        self.set_y(40)

    # def header(self):
    #     """این متد برای هر صفحهٔ جدید اجرا می‌شود."""
    #     if not os.path.exists(self.watermark_path):
    #         return
        

    #     # ----------- تنظیمات اندازه و مکان واترمارک -----------

    #     ######################### کد جدید ##################################################
    #     self.draw_template()
    #     self.draw_watermark()
        ########################## کد جدید پایان##################################################

        # desired_width_mm = 80                     # می‌توانید این مقدار را تغییر دهید
        # img = Image.open(self.watermark_path)
        # w_px, h_px = img.size
        # aspect_ratio = h_px / w_px

        # height_mm = desired_width_mm * aspect_ratio
        # x = (self.w - desired_width_mm) / 2       # مرکز افقی
        # y = (self.h - height_mm) / 2              # مرکز عمودی
        # # -----------------------------------------------------

        # # رسم تصویر
        # self.image(self.watermark_path, x=x, y=y,
        #            w=desired_width_mm, h=height_mm)
    
    
    ######################### کد جدید ##################################################
    def draw_template(self):
        #رسم سربرگ
        if not os.path.exists(self.template_path):
            return

        self.image(
            self.template_path,
            x=0,
            y=0,
            w=self.w,
            h=self.h
        )
    
    def draw_watermark(self):
        """
        رسم واترمارک در مرکز صفحه.
        """

        if not os.path.exists(self.watermark_path):
            return

        desired_width_mm = 80

        img = Image.open(self.watermark_path)
        img_w, img_h = img.size

        aspect_ratio = img_h / img_w

        width_mm = desired_width_mm
        height_mm = width_mm * aspect_ratio

        x = (self.w - width_mm) / 2
        y = (self.h - height_mm) / 2

        self.image(
            self.watermark_path,
            x=x,
            y=y,
            w=width_mm,
            h=height_mm
        )
    ######################### کد جدید پایان ##################################################

    

class ReportManager:

    def __init__(self, db_name="mrprinter3d_database.db"):
        self.db_name = db_name
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        column_map_path = os.path.join(self.BASE_DIR, "docs", "column-map", "column-map.json")
        self.column_map = json.load(open(column_map_path, 'r', encoding='utf-8'))
        self.watermark_path = os.path.join(
            self.BASE_DIR,
            "docs",
            "images",
            "logo_watermark.png"  
        )

        self.company_template_path = os.path.join(
        self.BASE_DIR,
        "docs",
        "images",
        "header.jpg"
        )

        self.reports_path = os.path.join(
        self.BASE_DIR,
        "docs",
        "reports"
        )

        os.makedirs(
        self.reports_path,
        exist_ok=True
        )
        self.font_path = os.path.join(
        self.BASE_DIR,
        "docs",
        "fonts",
        "YekanBakh-Regular.ttf"
        )

    def get_column_map(self, table_name):
        return self.column_map.get(table_name, {})


    async def get_data_from_db(self, table_name , project_title):
        database_manager = DatabaseManager() 

        if project_title:
          
            row,columns,variable_parameters_rows,variable_parameters_columns,final_project_data_rows,final_project_data_columns = await database_manager.R_and_D_subform_report_data(project_title)
            main_form_df = pd.DataFrame([row], columns=columns)
            variable_parameters_df = pd.DataFrame(variable_parameters_rows,columns=variable_parameters_columns)
            final_project_data_df = pd.DataFrame(final_project_data_rows,columns=final_project_data_columns)
        
        else :
           
            row,columns = await database_manager.report_data(table_name)
            main_form_df = pd.DataFrame(row, columns=columns)
            variable_parameters_df = None
            final_project_data_df = None
        
       # تبدیل تاریخ میلادی به شمسی
        if 'created_at' in main_form_df.columns:
            main_form_df['created_at'] = pd.to_datetime(main_form_df['created_at'], errors='coerce')
            main_form_df['created_at'] = main_form_df['created_at'].apply(
            lambda x: jdatetime.datetime.fromtimestamp(x.timestamp()).strftime('%Y/%m/%d %H:%M')
            if pd.notnull(x) else "—"
            )
        
        if variable_parameters_df is not None:
            variable_parameters_df['created_at'] = pd.to_datetime(variable_parameters_df['created_at'], errors='coerce')
            variable_parameters_df['created_at'] = variable_parameters_df['created_at'].apply(
            lambda x: jdatetime.datetime.fromtimestamp(x.timestamp()).strftime('%Y/%m/%d %H:%M')
            if pd.notnull(x) else "—"
            )
        
        if final_project_data_df is not None:
            final_project_data_df['created_at'] = pd.to_datetime(final_project_data_df['created_at'], errors='coerce')
            final_project_data_df['created_at'] = final_project_data_df['created_at'].apply(
            lambda x: jdatetime.datetime.fromtimestamp(x.timestamp()).strftime('%Y/%m/%d %H:%M')
            if pd.notnull(x) else "—"
            )

        return main_form_df,variable_parameters_df,final_project_data_df


    def render_dataframe(self, pdf, df, section_title):
        
        if df is None or df.empty:
            return


        pdf.set_font('YekanBakh', size=14)
        title = get_display(reshape(section_title))
        pdf.cell(pdf.epw, 10, txt=title, ln=1, align='C')
        pdf.ln(5)

        pdf.set_font('YekanBakh', size=14)
        
        for index, row in df.iterrows():
            # چک کردن برای صفحه جدید: اگر صفحه عوض شد، 
            
            # if pdf.get_y() > 180: # نزدیک به انتهای صفحه
            #     pdf.add_page()
                #self._add_watermark(pdf)

            for col_name, value in row.items():
                val_str = str(value) if value is not None else "-"
                if (col_name == "عکس یا مستندات مرتبط با عدم انطباق" and val_str != "-" and os.path.exists(val_str)):
                    pdf.multi_cell(180, 11, txt=get_display(reshape(f"{col_name}:")), align='R')
                    ext = os.path.splitext(val_str)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png']:
                        try:
                            pdf.image(val_str, x=pdf.w - 110, w=100)
                            pdf.ln(5)
                        except:
                            pass
                else:
                    line = f"{col_name}: {val_str}"
                    line = line.replace('\u200c', ' ')
                    reshaped_line = get_display(reshape(line))
                    pdf.set_x(pdf.l_margin)
                    pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin, 11, txt=reshaped_line, align='R')
            pdf.ln(5)
        pdf.ln(10)


    # def _add_watermark(self, pdf):
        
    #     if os.path.exists(self.watermark_path):
    #     # ۱. اندازه دلخواه خودت رو اینجا به میلی‌متر وارد کن
    #     # مثلاً اگر می‌خوای عرض لوگو ۸۰ میلی‌متر باشه:
    #         desired_width = 80 
            
    #         # ۲. باز کردن تصویر برای به دست آوردن نسبت ابعاد (Aspect Ratio)
    #         img = Image.open(self.watermark_path)
    #         img_w, img_h = img.size
    #         aspect_ratio = img_h / img_w
            
    #         # ۳. محاسبه ارتفاع متناسب با عرض دلخواه (تا عکس دفرمه نشه)
    #         width_mm = desired_width
    #         height_mm = width_mm * aspect_ratio

    #         # ۴. فرمول طلایی برای وسط‌چین کردن:
    #         # (عرض صفحه منهای عرض عکس) تقسیم بر ۲
    #         x = (pdf.w - width_mm) / 2
    #         y = (pdf.h - height_mm) / 2

    #     # ۵. چاپ تصویر در مرکز
    #     pdf.image(self.watermark_path, x=x, y=y, w=width_mm, h=height_mm)

   
    # async def create_pdf(self, table_name, project_title=None):

    #     main_form_df, variable_parameters_df, final_project_data_df = await self.get_data_from_db(table_name, project_title)
    #     main_form_df.rename(columns=self.get_column_map(table_name), inplace=True)
        
    #     reports_file_path = os.path.join(self.BASE_DIR, "docs", "reports")
    #     if not os.path.exists(reports_file_path): os.makedirs(reports_file_path)
        
    #     font_path = os.path.join(self.BASE_DIR, "docs", "fonts", "YekanBakh-Regular.ttf")

    #     # استفاده از کلاس پی دی اف که واترمارک را در هدر می‌گذارد
       
    #    #کد جدید ###############################3
    #     pdf = PDF(watermark_path=self.watermark_path,template_path=self.company_template_path)
    #     # pdf.set_auto_page_break(auto=True, margin=15)
    #     # کد جدید ##############################

    #     #pdf = FPDF()
    #     #pdf.set_auto_page_break(auto=True, margin=15)
    #     pdf.add_font('YekanBakh', '', font_path)
    #     pdf.set_font('YekanBakh', size=13)

    #     # صفحه اول
    #     pdf.add_page()
       
    #     #self._add_watermark(pdf) # واترمارک اول از همه
    #     # تیتر
    #     title_text = get_display(reshape(f"گزارش جدول: {table_name}"))
    #     pdf.cell(pdf.epw, 10, txt=title_text, ln=1, align='C')
    #     pdf.ln(10)

    #     # رندر جدول
    #     self.render_dataframe(pdf, main_form_df, "اطلاعات اصلی پروژه")

    #     # رندر دیتافریم پارامترهای متغیر پروژه تحقیق و توسعه
    #     if variable_parameters_df is not None:
            
    #         variable_parameters_df.rename(columns=self.get_column_map("project_variable_parameters"), inplace=True)
    #         self.render_dataframe(pdf, variable_parameters_df, "پارامترهای متغیر")
        
    #     if final_project_data_df is not None:

    #         final_project_data_df.rename(columns=self.get_column_map("final_project_data"), inplace=True)
    #         self.render_dataframe(pdf, final_project_data_df, "نتایج نهایی")
        
    #     file_path = os.path.join(reports_file_path, f"{table_name}_report.pdf")
    #     pdf.output(file_path)
    #     return file_path

    async def create_pdf(self, table_name, project_title=None):

        (main_form_df,variable_parameters_df,final_project_data_df) = await self.get_data_from_db(
            table_name,project_title)

        main_form_df.rename(
            columns=self.get_column_map(table_name),
            inplace=True
        )

        file_path = await asyncio.to_thread(
            self._build_pdf,
            table_name,
            main_form_df,
            variable_parameters_df,
            final_project_data_df
        )

        return file_path
    
    def _build_pdf(self,table_name,main_form_df,variable_parameters_df,final_project_data_df):

        #reports_file_path = os.path.join(self.BASE_DIR, "docs", "reports")
        if not os.path.exists(self.reports_path):
            os.makedirs(self.reports_path)

        

        pdf = PDF(
            watermark_path=self.watermark_path,
            template_path=self.company_template_path

        )

        pdf.set_auto_page_break(auto=True, margin=40)

        pdf.add_font('YekanBakh', '', self.font_path)
        pdf.set_font('YekanBakh', size=13)

        pdf.add_page()

        title_text = get_display(
            reshape(f"گزارش جدول: {table_name}")
        )

        pdf.cell(
            pdf.epw,
            10,
            txt=title_text,
            new_x="LMARGIN",
            new_y="NEXT",
            align="C"
        )

        pdf.ln(10)

        self.render_dataframe(
            pdf,
            main_form_df,
            "اطلاعات اصلی پروژه"
        )

        if variable_parameters_df is not None:
            variable_parameters_df.rename(
                columns=self.get_column_map("project_variable_parameters"),
                inplace=True
            )

            self.render_dataframe(
                pdf,
                variable_parameters_df,
                "پارامترهای متغیر"
            )

        if final_project_data_df is not None:
            final_project_data_df.rename(
                columns=self.get_column_map("final_project_data"),
                inplace=True
            )

            self.render_dataframe(
                pdf,
                final_project_data_df,
                "نتایج نهایی"
            )

        file_path = os.path.join(
            self.reports_path,
            f"{table_name}_report.pdf"
        )

        self.add_chart_to_pdf(pdf)
        pdf.output(file_path)
        return file_path
    
    def create_demo_chart(self):
        """
        ساخت نمودار نمونه (فعلاً با داده‌های ثابت)
        """

        chart_path = os.path.join(
            self.reports_path,
            "temp_chart.png"
        )

        months = [
            "Far",
            "Ord",
            "Kho",
            "Tir",
            "Mor",
            "Sha"
        ]

        values = [
            5,
            8,
            2,
            11,
            7,
            4
        ]

        plt.figure(figsize=(8,4))

        plt.plot(
            months,
            values,
            marker="o",
            linewidth=2
        )

        plt.title("Monthly Non-Conformities")
        plt.xlabel("Month")
        plt.ylabel("Count")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(chart_path, dpi=200)

        plt.close()

        return chart_path
    
    
    def add_chart_to_pdf(self, pdf):

        chart_path = self.create_demo_chart()

        pdf.add_page()

        title = get_display(
            reshape("نمودار آماری")
        )

        pdf.set_font("YekanBakh", size=16)

        pdf.cell(
            pdf.epw,
            10,
            txt=title,
            new_x="LMARGIN",
            new_y="NEXT",
            align="C"
        )

        pdf.ln(10)

        pdf.image(
            chart_path,
            x=20,
            w=170
        )