import aiosqlite
import sqlite3
from contextlib import asynccontextmanager
from typing import List, Tuple, Any, Dict, Optional

class DatabaseManager:

    def __init__(self, db_name="mrprinter3d_database.db"):
        self.db_name = db_name
        self.init_db()

    @asynccontextmanager
    async def establish_connection(self):
        async with aiosqlite.connect(self.db_name, timeout=20) as conn:
            await conn.execute("PRAGMA foreign_keys = ON")
            await conn.execute("PRAGMA journal_mode=WAL;")
            try:
                yield conn
            finally:
                pass
        

    def init_db(self):
        """ایجاد جداول برای تمام فرم‌ها"""

        conn = sqlite3.connect(self.db_name, timeout=20)
        
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode=WAL;")


        ###### جدول فرم تحقیق و توسعه (R&D) ###################################################################################

            ''' ساختار جداول برای فرم تحقیق و توسعه (R&D):
            ┌───────────────────────┐
            │     R_and_D_form      │
            │-----------------------│
            │ id (PK)               │
            │ project_title         │
            │ ...                   │
            └───────────┬───────────┘
                        │
                        ▼
            ┌─────────────────────────────┐
            │ project_variable_parameters │
            │-----------------------------│
            │ id (PK)                     │
            │ project_id (FK)             │
            │ level_number                │
            │ nozzle_temperature          │
            │ ...                         │
            └─────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   final_project_data  │
            │-----------------------│
            │ id (PK)               │
            │ project_title  fk     │
            │ ...                   │
            └───────────┬───────────┘
                        '''

            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS R_and_D_form (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_title TEXT UNIQUE,
                    purpose TEXT,
                    application TEXT,
                    customer_name TEXT,
                    start_date TEXT,
                    project_number TEXT,
                    project_manager TEXT,
                    printer_type TEXT,
                    material_type TEXT,
                    nozzle_diameter TEXT,
                    environmental_conditions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS project_variable_parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    level_number TEXT NOT NULL,
                    nozzle_temperature TEXT,
                    bed_temperature TEXT,
                    print_speed TEXT,
                    layer_height TEXT,
                    infill_percentage TEXT,
                    infill_pattern TEXT,
                    fan_speed TEXT,
                    part_orientation TEXT,
                    time TEXT,
                    material_consumption_rate TEXT,
                    print_status TEXT,
                    appearance_quality TEXT,
                    dimensional_accuracy TEXT,
                    mechanical_strength TEXT,
                    layer_adhesiveness TEXT,
                    defection_existance TEXT,
                    technical_description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES R_and_D_form(id) ON DELETE CASCADE,
                    UNIQUE(project_id, level_number)
                );

                CREATE TABLE IF NOT EXISTS final_project_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    effective_parameters TEXT,
                    best_parameter_combination TEXT,
                    choice_reasons TEXT,
                    project_status TEXT,
                    final_parameters TEXT,
                    parameters_usecase TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES R_and_D_form(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS defect_and_repair_registration_form (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_name TEXT,
                    machine_code TEXT,
                    location TEXT,
                    operator TEXT,
                    fault_date TEXT,
                    fault_time TEXT,
                    order_code TEXT,
                    part_type TEXT,
                    material TEXT,
                    progress_percent TEXT,
                    uptime_before_fault TEXT,
                    fault_summary TEXT,
                    fault_category TEXT,
                    operator_detailed_desc TEXT,
                    initial_action TEXT,
                    apparent_cause TEXT,
                    root_cause_needed TEXT,
                    analysis_method TEXT,
                    root_cause_desc TEXT,
                    action_type TEXT,
                    action_desc TEXT,
                    repair_start_date TEXT,
                    repair_end_date TEXT,
                    final_machine_status TEXT,
                    test_result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS product_non_conformity_form (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    non_conformity_number TEXT,
                    registration_date TEXT,
                    registrant_name TEXT,
                    non_conformity_location TEXT,
                    product_type_code TEXT,
                    order_serial TEXT,
                    total_quantity TEXT,
                    total_non_conform_quantity TEXT,
                    non_conformity_type TEXT,
                    problem_description TEXT,
                    non_conformity_docs TEXT,
                    explored_by TEXT,
                    explore_phase TEXT,
                    initial_review_by TEXT,
                    initial_decision TEXT,
                    decision_responsible TEXT,
                    initial_action_date TEXT,
                    root_cause_analysis TEXT,
                    analysis_tool TEXT,
                    root_cause TEXT,
                    corrective_action TEXT,
                    corrective_action_form TEXT,
                    corrective_action_done TEXT,
                    corrective_action_responsible TEXT,
                    corrective_action_date TEXT,
                    corrective_action_effectiveness TEXT,
                    closure_date TEXT,
                    final_status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            conn.commit()

        finally:
            conn.close()
       
     

   

    async def check_isUnique(self,column,value,form_db:str) -> bool:
        
       async with self.establish_connection() as conn:

            async with conn.execute(f"SELECT 1 FROM {form_db} WHERE {column} = ? LIMIT 1", (value,)) as cur:

                row = await cur.fetchone()
                return row is None
    


    async def insert_data(self, table_name:str , form_data: Dict , conn=None) -> bool:

        """متد کلی برای ذخیره دیتای هر فرم در جدول مربوطه"""
        
        if conn is None:
            # conn = await self.establish_connection()
            async with self.establish_connection() as new_conn:
                return await self.insert_data(table_name, form_data, conn=new_conn)
        
        # cursor = conn.cursor()
        
        # استخراج نام ستون‌ها و مقادیر از دیکشنری
        columns = ', '.join(form_data.keys())
        placeholders = ', '.join(['?'] * len(form_data))
        values = list(form_data.values())
        
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        try:
            await conn.execute(sql, values)            
            await conn.commit()
            print(f"Data inserted successfully into {table_name}")
            return True
        except Exception as e:
            await conn.rollback()
            print(f"Error inserting into {table_name}: {e}")
            return False
       



    async def insert_data_into_r_and_d_form(self,form_data:Dict) ->bool:
        
          
        keys1 = list(form_data.keys())[0:11] 
        keys2 = list(form_data.keys())[11:28]
        # keys3 = list(form_data.keys())[28:34]
           
        form_data1 = {k : form_data[k] for k in keys1}#اضافه کردن سوالات تحلیل نتایج و مقایسه آزمون‌ها به دیتای فرم تحقیق و توسعه
        form_data2 = {k : form_data[k] for k in keys2}#دیتای مربوط به پارامترهای متغیر
        #form_data3 = {k : form_data[k] for k in keys3}# دیتای مربوط به نتایج نهایی پروژه

        async with self.establish_connection() as conn:
        
        # استخراج نام ستون‌ها و مقادیر از دیکشنری
            columns = ', '.join(form_data1.keys())
            placeholders = ', '.join(['?'] * len(form_data1))
            values = list(form_data1.values())
            
            sql = f"INSERT INTO R_and_D_form ({columns}) VALUES ({placeholders})"
        
            try:
                cursor = await conn.execute(sql, values)
                project_id = cursor.lastrowid #دریافت آی دی پروژه جدید            
            
            except Exception as e:
                await conn.rollback()
                print("error inserting into r_and_d_form: ",e)
                return False
        

            async with conn.execute("SELECT COUNT(*) FROM project_variable_parameters WHERE project_id = ?",(project_id,)) as cursor :   
                count_result = await cursor.fetchone()
                level_number = str(count_result[0] + 1)  # محاسبه شماره آزمایش جدید
           
           
            form_data2['project_id'] = str(project_id)
            form_data2['level_number'] = level_number

            result = await self.insert_data("project_variable_parameters", form_data2 , conn)
            
        return result
            
    
 

############# گزارش‌گیری #########################################################     

    async def report_data(self, table_name:str):
        """خواندن کل داده‌های یک جدول برای گزارش‌گیری"""
        
        async with  self.establish_connection() as conn:
             
            async with conn.execute(f"SELECT * FROM {table_name}") as cursor:
                rows = await cursor.fetchall()
            
                columns = [description[0] for description in cursor.description]

            return rows , columns
    

    async def fetch_projects_names(self, table_name):
        """خواندن نام پروژه‌ها برای گزارش‌گیری"""
        
        async with  self.establish_connection() as conn:
            async with  conn.execute(f"SELECT project_title FROM {table_name}") as cursor:
                rows = await cursor.fetchall()
                                     
            return [row[0] for row in rows]
        

    async def R_and_D_subform_report_data(self, project_title):

        "گزارش گیری از اطلاعات فرم یک پروژه خاص تحقیق و توسعه"
        
        async with  self.establish_connection() as conn:
      

####################### گزارش گیری از پارامترهای متغیر یک پروژه خاص ########################################################################################

            async with conn.execute(f"SELECT id FROM R_and_D_form WHERE project_title = ?", (project_title,)) as cursor:
                row = await cursor.fetchone()
                project_id = row[0] if row else None

            async with conn.execute(f"SELECT * FROM project_variable_parameters WHERE project_id = ?", (project_id,)) as cursor:
                variable_parameters_rows = await cursor.fetchall()
                variable_parameters_columns = [description[0] for description in cursor.description]
            
            async with conn.execute(f"SELECT * FROM final_project_data WHERE project_id = ?", (project_id,)) as cursor:
                final_project_data_rows = await cursor.fetchall()
                final_project_data_columns = [description[0] for description in cursor.description]


################################  گزارش گیری از اطلاعات ثابت یک پروژه خاص در جدول اصلی ##########################################################################################################
       
            async with conn.execute(f"SELECT * FROM R_and_D_form WHERE id = ?", (project_id,)) as cursor:
                row = await cursor.fetchone()
                columns = [description[0] for description in cursor.description]


            
            return row , columns,variable_parameters_rows,variable_parameters_columns,final_project_data_rows,final_project_data_columns


    def get_database_schema(self) -> str:
        """اسکیمای جداول را برمی‌گرداند؛ توسط ماژول ai برای NL→SQL استفاده می‌شود"""

        conn = sqlite3.connect(self.db_name)

        cur = conn.cursor()

        cur.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
        """)

        tables = cur.fetchall()

        schema = ""

        for (table,) in tables:

            schema += f"\nTable: {table}\n"

            cur.execute(f"PRAGMA table_info({table})")

            cols = cur.fetchall()

            for col in cols:

                schema += f"{col[1]} ({col[2]})\n"

        conn.close()

        return schema