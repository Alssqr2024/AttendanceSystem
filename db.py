# db.py

# import psycopg2
# from psycopg2 import sql
from datetime import datetime
from psycopg2.pool import SimpleConnectionPool
import hashlib
import configparser

# Global variable for the connection pool
connection_pool = None

def get_config():
    """Reads the configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    if not config.has_section('Database'):
        raise Exception("Database configuration section not found in config.ini")
    return config

def initialize_connection_pool():
    """Initializes the connection pool using settings from config.ini."""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
    
    config = get_config()
    db_config = config['Database']
    
    try:
        connection_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dbname=db_config.get('dbname'),
            user=db_config.get('user'),
            password=db_config.get('password'),
            host=db_config.get('host'),
            port=db_config.get('port')
        )
    except Exception as e:
        print(f"Failed to initialize connection pool: {e}")
        connection_pool = None

def get_db_connection():
    """Gets a connection from the pool. Initializes the pool if it doesn't exist."""
    global connection_pool
    if connection_pool is None:
        initialize_connection_pool()
    
    if connection_pool is None:
        raise Exception("Connection pool is not available.")
        
    return connection_pool.getconn()

def release_connection(conn):
    """Releases a connection back to the pool."""
    if connection_pool:
        connection_pool.putconn(conn)

# Initialize the pool when the module is loaded
initialize_connection_pool()

# ========== إدارة المستخدمين (users) ==========

def hash_password(password):
    """تشفير كلمة المرور باستخدام SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_users():
    """جلب جميع المستخدمين مع رقم المستخدم واسم المستخدم وكلمة المرور المشفرة والوظائف من جدول users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT userid, username, password, functions
            FROM users
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []
    finally:
        release_connection(conn)

def add_user(username, password, functions=None):
    """إضافة مستخدم جديد إلى جدول user مع تشفير كلمة المرور وتخزين الوظائف"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, password, functions)
            VALUES (%s, %s, %s)
        """, (username, hashed_pw, functions))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding user: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

def update_user(username, new_password, new_functions=None):
    """تعديل كلمة المرور (مع تشفيرها) أو الوظائف للمستخدم بناءً على اسم المستخدم"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if new_password:
            hashed_pw = hash_password(new_password)
            cursor.execute("""
                UPDATE users SET password = %s, functions = %s WHERE username = %s
            """, (hashed_pw, new_functions, username))
        else:
            cursor.execute("""
                UPDATE users SET functions = %s WHERE username = %s
            """, (new_functions, username))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating user: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

def delete_user(username):
    """حذف مستخدم من جدول users بناءً على اسم المستخدم"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting user: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

def check_user_password(username, password):
    """التحقق من اسم المستخدم وكلمة المرور (مشفرة)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            return False
        hashed_input = hash_password(password)
        return hashed_input == row[0]
    except Exception as e:
        print(f"Error checking user password: {e}")
        return False
    finally:
        release_connection(conn)

def delete_user_logs(user_id):
    """حذف جميع سجلات المستخدم من جدول logs بناءً على user_id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM logs WHERE UserID = %s", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting user logs: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

# ========== الحضور والانصراف =========================

def record_check_in(employee_id, today):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # التحقق من وجود تسجيل حضور اليوم
        query_check = """
            SELECT CheckInTime 
            FROM Attendance 
            WHERE EmployeeID = %s AND Date = %s
        """
        cursor.execute(query_check, (employee_id, today))
        result = cursor.fetchone()
        if result:
            return False  # تم تسجيل الحضور مسبقًا
        # تسجيل الحضور
        query_insert = """
            INSERT INTO Attendance (EmployeeID, CheckInTime, Date)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query_insert, (employee_id, datetime.now(), today))
        conn.commit()
        log_action(employee_id=employee_id, action="تسجيل الحضور")
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)

def record_check_out(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # التحقق من وجود سجل حضور بدون انصراف
        query_check_in = """
            SELECT CheckInTime
            FROM Attendance
            WHERE EmployeeID = %s AND Date = %s AND CheckOutTime IS NULL
        """
        today = datetime.now().date()
        cursor.execute(query_check_in, (employee_id, today))
        result = cursor.fetchone()
        if not result:
            return None  # لم يُسجل حضور لهذا الموظف اليوم
        # تحديث وقت الانصراف
        check_out_time = datetime.now()
        query_update = """
            UPDATE Attendance
            SET CheckOutTime = %s
            WHERE EmployeeID = %s AND Date = %s AND CheckOutTime IS NULL
            RETURNING CheckInTime
        """
        cursor.execute(query_update, (check_out_time, employee_id, today))
        check_in_time = cursor.fetchone()[0]
        # حساب المدة
        duration = check_out_time - check_in_time
        # تحديث المدة في قاعدة البيانات (اختياري)
        duration_update_query = """
            UPDATE Attendance
            SET Duration = %s
            WHERE EmployeeID = %s AND Date = %s AND CheckOutTime IS NOT NULL
        """
        cursor.execute(duration_update_query, (duration, employee_id, today))
        conn.commit()
        log_action(employee_id=employee_id, action="تسجيل الانصراف")
        return duration  # إرجاع المدة الزمنية (timedelta)
    except Exception as e:
        conn.rollback()
        raise Exception(f"خطأ في تسجيل الانصراف: {str(e)}")
    finally:
        release_connection(conn)

# ========== السجلات (logs) ==========

def log_action(employee_id=None, action=None, user_id=None):
    """
    تسجيل حدث في جدول Logs
    - إذا كان الحدث يخص مستخدم النظام (مثل العمليات الإدارية)، يجب تمرير user_id.
    - إذا كان الحدث يخص موظف فقط (وليس مستخدم)، مرر employee_id فقط.
    لا تعتمد على users[0][0] كخيار افتراضي.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id is not None:
        query = """
            INSERT INTO Logs (UserID, Action, Timestamp)
            VALUES (%s, %s, NOW())
        """
        cursor.execute(query, (user_id, action))
    else:
        query = """
            INSERT INTO Logs (EmployeeID, Action, Timestamp)
            VALUES (%s, %s, NOW())
        """
        cursor.execute(query, (employee_id, action))
    conn.commit()
    release_connection(conn)

def get_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            l.LogID, 
            COALESCE(e.FirstName, u.username) AS Name,  -- اسم الموظف أو اسم المستخدم
            l.Action, 
            l.Timestamp
        FROM Logs l
        LEFT JOIN Employees e ON l.EmployeeID = e.EmployeeID
        LEFT JOIN users u ON l.UserID = u.userid
        ORDER BY l.Timestamp DESC
    """
    cursor.execute(query)
    logs = cursor.fetchall()
    release_connection(conn)
    return logs

# ========== إحصائيات ==========

def get_daily_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    # عدد الحضور اليومي
    cursor.execute("""
        SELECT COUNT(*) 
        FROM Attendance 
        WHERE Date = %s AND CheckInTime IS NOT NULL
    """, (datetime.now().date(),))
    present_count = cursor.fetchone()[0]
    # عدد الغياب اليومي
    cursor.execute("""
        SELECT COUNT(*) 
        FROM Employees 
        WHERE EmployeeID NOT IN (
            SELECT EmployeeID 
            FROM Attendance 
            WHERE Date = %s
        )
    """, (datetime.now().date(),))
    absent_count = cursor.fetchone()[0]
    # إجمالي عدد الموظفين
    cursor.execute("SELECT COUNT(*) FROM Employees")
    total_employees = cursor.fetchone()[0]
    conn.close()
    return present_count, absent_count, total_employees

# ========== إدارة الموظفين (employees) ==========

def get_employees():
    """جلب جميع الموظفين مع جميع الحقول المطلوبة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT EmployeeID, FirstName, Email, Phone, Position, Department, FaceData, Photo
            FROM Employees
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching employees: {e}")
        return []
    finally:
        release_connection(conn)

# ========== حالة الحضور لموظف في يوم معين ========== 
def get_attendance_status(employee_id, day):
    """جلب حالة الحضور والانصراف لموظف في يوم معين (check_in_time, check_out_time)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT CheckInTime, CheckOutTime
            FROM Attendance
            WHERE EmployeeID = %s AND Date = %s
        """, (employee_id, day))
        row = cursor.fetchone()
        if row:
            return {
                'check_in_time': row[0],
                'check_out_time': row[1]
            }
        else:
            return None
    except Exception as e:
        print(f"Error fetching attendance status: {e}")
        return None
    finally:
        release_connection(conn)

# ========== جلب أسماء جميع الموظفين فقط ========== 
def get_employee_names():
    """جلب قائمة أسماء جميع الموظفين (FirstName فقط)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT FirstName FROM Employees")
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"Error fetching employee names: {e}")
        return []
    finally:
        release_connection(conn)

# ========== حذف جميع السجلات من جدول logs ========== 
def delete_all_logs():
    """حذف جميع السجلات من جدول logs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM logs")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting all logs: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

# ========== جلب جميع سجلات الحضور والانصراف ========== 
def get_attendance_records():
    """جلب جميع سجلات الحضور والانصراف مع الحقول المطلوبة للتقارير"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT a.EmployeeID, e.FirstName, e.Department, e.Position, a.CheckInTime, a.CheckOutTime, a.Date, a.Duration
            FROM Attendance a
            JOIN Employees e ON a.EmployeeID = e.EmployeeID
            ORDER BY a.Date DESC, a.CheckInTime DESC
        ''')
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching attendance records: {e}")
        return []
    finally:
        release_connection(conn)

# ========== جلب جميع الأقسام ========== 
def get_departments():
    """جلب قائمة الأقسام الفريدة من جدول الموظفين"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT Department FROM Employees")
        rows = cursor.fetchall()
        return [row[0] for row in rows if row[0]]
    except Exception as e:
        print(f"Error fetching departments: {e}")
        return []
    finally:
        release_connection(conn)

# ========== إضافة موظف جديد ========== 
def add_employee(employee_id, first_name, email, phone, position, department, face_data, photo_data=None):
    """إضافة موظف جديد إلى جدول Employees"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO Employees (EmployeeID, FirstName, Email, Phone, Position, Department, FaceData, Photo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (employee_id, first_name, email, phone, position, department, face_data, photo_data))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding employee: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

# ========== حذف موظف ========== 
def delete_employee(employee_id):
    """حذف موظف من جدول Employees بناءً على EmployeeID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Employees WHERE EmployeeID = %s", (employee_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting employee: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

# ========== تعديل بيانات موظف ========== 
def update_employee(employee_id, first_name, email, phone, position, department, photo_data=None):
    """تعديل بيانات موظف في جدول Employees"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE Employees
            SET FirstName = %s, Email = %s, Phone = %s, Position = %s, Department = %s, Photo = %s
            WHERE EmployeeID = %s
        ''', (first_name, email, phone, position, department, photo_data, employee_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating employee: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

# ========== جلب بيانات موظف برقم الموظف ========== 
def get_employee_by_id(employee_id):
    """جلب بيانات موظف واحد حسب EmployeeID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT EmployeeID, FirstName, Email, Phone, Position, Department, FaceData, Photo
            FROM Employees
            WHERE EmployeeID = %s
        ''', (employee_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching employee by id: {e}")
        return None
    finally:
        release_connection(conn)

def check_database_status():
    """فحص حالة قاعدة البيانات وعدد الموظفين"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # فحص عدد الموظفين
        cursor.execute("SELECT COUNT(*) FROM Employees")
        employee_count = cursor.fetchone()[0]
        
        # فحص عدد المستخدمين
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # فحص عدد سجلات الحضور
        cursor.execute("SELECT COUNT(*) FROM Attendance")
        attendance_count = cursor.fetchone()[0]
        
        print(f"📊 حالة قاعدة البيانات:")
        print(f"   - عدد الموظفين: {employee_count}")
        print(f"   - عدد المستخدمين: {user_count}")
        print(f"   - عدد سجلات الحضور: {attendance_count}")
        
        return {
            'employees': employee_count,
            'users': user_count,
            'attendance': attendance_count
        }
    except Exception as e:
        print(f"❌ خطأ في فحص قاعدة البيانات: {e}")
        return None
    finally:
        if conn:
            try:
                release_connection(conn)
            except:
                pass

def delete_all_attendance_records():
    """حذف جميع سجلات الحضور والانصراف من جدول Attendance"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Attendance")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting all attendance records: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)