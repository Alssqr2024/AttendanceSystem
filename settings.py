import flet as ft
import os
import subprocess
import logging
import configparser
import psycopg2
from datetime import datetime
from zk import ZK

class SettingsPage(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.alignment = ft.MainAxisAlignment.START
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 20
        self.expand = True
        
        self.config = configparser.ConfigParser()
        self.load_config()
        self.setup_logging()
        
        self.initialize_components()
        self.build_ui()

    def setup_logging(self):
        logging.basicConfig(
            filename='system.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_config(self):
        self.config.read('config.ini')
        if not self.config.has_section('Database'):
            self.config.add_section('Database')
            self.config.set('Database', 'host', 'localhost')
            self.config.set('Database', 'port', '5432')
            self.config.set('Database', 'user', 'postgres')
            self.config.set('Database', 'dbname', 'Attendance_System')
            self.config.set('Database', 'password', '')
        
        if not self.config.has_section('Fingerprint'):
            self.config.add_section('Fingerprint')
            self.config.set('Fingerprint', 'ip', '192.168.1.201')
            self.config.set('Fingerprint', 'port', '4370')

        if not self.config.has_section('Paths'):
            self.config.add_section('Paths')
            self.config.set('Paths', 'postgres_bin', r'C:\Program Files\PostgreSQL\17\bin')

        if not self.config.has_section('Appearance'):
            self.config.add_section('Appearance')
            self.config.set('Appearance', 'theme', 'light')
            self.config.set('Appearance', 'report_font', 'assets/fonts/Amiri-Italic.ttf')

        if not self.config.has_section('Settings'):
            self.config.add_section('Settings')
            self.config.set('Settings', 'log_retention', "30")
            self.config.set('Settings', 'backup_format', "c")
        
        self.save_config()

    def save_config(self):
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def save_and_log(self, section, key, value, control_to_update=None):
        self.config.set(section, key, str(value))
        self.save_config()
        
        if control_to_update:
            control_to_update.value = str(value)

        current_username = self.page.session.get("username")
        try:
            from db import get_users, log_action
            users = get_users()
            user_id = next((u[0] for u in users if u[1] == current_username), None)
            if user_id:
                log_action(user_id=user_id, action=f"غيّر الإعداد: {section}.{key} إلى {value}")
        except Exception as e:
            logging.warning(f"Failed to log settings change: {e}")
        
        self.page.update()

    def create_setting_textfield(self, section, key, label, is_password=False, tooltip=None):
        return ft.TextField(
            label=label,
            value=self.config.get(section, key, fallback=""),
            password=is_password,
            can_reveal_password=is_password,
            on_change=lambda e: self.save_and_log(section, key, e.control.value),
            tooltip=tooltip,
            border_radius=8,
        )

    def initialize_components(self):
        # Database Components
        self.db_host = self.create_setting_textfield('Database', 'host', "اسم المضيف (Host)", tooltip="عنوان IP أو اسم المضيف لخادم قاعدة البيانات")
        self.db_port = self.create_setting_textfield('Database', 'port', "المنفذ (Port)", tooltip="منفذ الاتصال بقاعدة البيانات (الافتراضي 5432)")
        self.db_user = self.create_setting_textfield('Database', 'user', "اسم المستخدم", tooltip="اسم المستخدم للوصول إلى قاعدة البيانات")
        self.db_name = self.create_setting_textfield('Database', 'dbname', "اسم قاعدة البيانات", tooltip="اسم قاعدة البيانات المحددة للنظام")
        self.db_password = self.create_setting_textfield('Database', 'password', "كلمة المرور", True, "كلمة مرور مستخدم قاعدة البيانات")
        self.db_status = ft.Text("لم يتم الاختبار", color="grey")

        # Fingerprint Components
        self.zk_ip = self.create_setting_textfield('Fingerprint', 'ip', "عنوان IP لجهاز البصمة", tooltip="عنوان IP الخاص بجهاز البصمة في الشبكة")
        self.zk_port = self.create_setting_textfield('Fingerprint', 'port', "منفذ جهاز البصمة", tooltip="منفذ الاتصال بجهاز البصمة (الافتراضي 4370)")
        self.zk_status = ft.Text("لم يتم الاختبار", color="grey")

        # Paths Components
        self.postgres_path_field = ft.TextField(
            label="مسار مجلد bin في PostgreSQL",
            value=self.config.get('Paths', 'postgres_bin'),
            read_only=True,
            tooltip="المجلد الذي يحتوي على أدوات pg_dump و psql",
        )
        self.path_picker = ft.FilePicker(on_result=self.on_path_selected)
        self.page.overlay.append(self.path_picker)

        # Appearance Components
        self.theme_dropdown = ft.Dropdown(
            label="الثيم",
            value=self.config.get('Appearance', 'theme'),
            options=[
                ft.dropdown.Option("light", "فاتح"),
                ft.dropdown.Option("dark", "داكن")
            ],
            on_change=lambda e: self.change_theme(e.control.value),
        )
        
        available_fonts = ["assets/fonts/Amiri-Italic.ttf", "assets/fonts/Cairo-VariableFont_slnt,wght.ttf"]
        self.report_font_dropdown = ft.Dropdown(
            label="خط تقارير PDF",
            value=self.config.get('Appearance', 'report_font'),
            options=[ft.dropdown.Option(font, text=os.path.basename(font)) for font in available_fonts],
            on_change=lambda e: self.save_and_log('Appearance', 'report_font', e.control.value),
        )

        # General Settings Components
        self.log_retention = self.create_setting_textfield('Settings', 'log_retention', "أيام الاحتفاظ بالسجلات")
        self.backup_format = ft.Dropdown(
            label="تنسيق النسخ الاحتياطي",
            value=self.config.get('Settings', 'backup_format'),
            options=[
                ft.dropdown.Option("c", "مخصص (مضغوط)"),
                ft.dropdown.Option("p", "نص عادي")
            ],
            on_change=lambda e: self.save_and_log('Settings', 'backup_format', e.control.value),
        )

        # Backup & Restore Components
        self.backup_picker = ft.FilePicker(on_result=self.on_backup_dir_selected)
        self.restore_picker = ft.FilePicker(on_result=self.on_restore_file_selected)
        self.page.overlay.extend([self.backup_picker, self.restore_picker])
        self.progress_bar = ft.ProgressBar(width=400, visible=False, color="#2ECC71", bgcolor="#EAECEE")

    def create_expandable_card(self, title, icon, controls, initially_expanded=False):
        """إنشاء بطاقة قابلة للطي والفتح"""
        # محتوى البطاقة
        content = ft.Column(controls, spacing=15, visible=initially_expanded)
        
        # زر التبديل مع أيقونة
        toggle_button = ft.ListTile(
            leading=ft.Icon(icon, color="#006064"),
            title=ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color="#006064"),
            trailing=ft.Icon(
                ft.Icons.EXPAND_MORE if initially_expanded else ft.Icons.EXPAND_LESS,
                color="#006064"
            ),
            on_click=lambda e: self.toggle_card_expansion(content, toggle_button.trailing)
        )
        
        return ft.Card(
            elevation=4,
            content=ft.Container(
                padding=20,
                border_radius=10,
                content=ft.Column([
                    toggle_button,
                    ft.Divider(visible=initially_expanded),
                    content
                ], spacing=15)
            )
        )

    def toggle_card_expansion(self, content, icon):
        """تبديل حالة فتح/إغلاق البطاقة"""
        is_visible = content.visible
        content.visible = not is_visible
        
        # تغيير الأيقونة
        icon.name = ft.Icons.EXPAND_MORE if not is_visible else ft.Icons.EXPAND_LESS
        
        self.page.update()

    def build_ui(self):
        # إنشاء البطاقات القابلة للطي
        db_card = self.create_expandable_card("إعدادات قاعدة البيانات", ft.Icons.STORAGE, [
            self.db_host, self.db_port, self.db_user, self.db_name, self.db_password,
            ft.Row([
                ft.ElevatedButton("اختبار الاتصال", icon=ft.Icons.CABLE, on_click=self.test_db_connection),
                self.db_status
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], initially_expanded=True)  # مفتوحة افتراضياً

        zk_card = self.create_expandable_card("إعدادات جهاز البصمة", ft.Icons.FINGERPRINT, [
            self.zk_ip, self.zk_port,
            ft.Row([
                ft.ElevatedButton("اختبار الاتصال", icon=ft.Icons.CABLE, on_click=self.test_zk_connection),
                self.zk_status
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ])
        
        paths_card = self.create_expandable_card("الإعدادات المتقدمة والنسخ الاحتياطي", ft.Icons.BUILD, [
            ft.Row([
                self.postgres_path_field,
                ft.IconButton(icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: self.path_picker.get_directory_path(), tooltip="اختيار مجلد"),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            self.log_retention,
            self.backup_format,
            ft.Row([
                ft.ElevatedButton("إنشاء نسخة احتياطية", icon=ft.Icons.BACKUP, on_click=self.init_backup),
                ft.ElevatedButton("استعادة نسخة", icon=ft.Icons.RESTORE, on_click=self.init_restore),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            self.progress_bar,
        ])

        appearance_card = self.create_expandable_card("المظهر والتخصيص", ft.Icons.BRUSH, [
            self.theme_dropdown,
            self.report_font_dropdown,
        ])

        # إضافة أزرار لفتح/إغلاق جميع البطاقات
        expand_all_btn = ft.ElevatedButton(
            "فتح جميع الإعدادات",
            icon=ft.Icons.EXPAND_MORE,
            on_click=lambda e: self.expand_all_cards(),
            bgcolor="#388E3C",
            color="#FFFFFF"
        )
        
        collapse_all_btn = ft.ElevatedButton(
            "طي جميع الإعدادات",
            icon=ft.Icons.EXPAND_LESS,
            on_click=lambda e: self.collapse_all_cards(),
            bgcolor="#F57C00",
            color="#FFFFFF"
        )

        self.controls = [
            ft.Text("إعدادات النظام", size=28, weight="bold"),
            ft.Row([
                expand_all_btn,
                collapse_all_btn
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            ft.Column([
                db_card, 
                zk_card, 
                paths_card, 
                appearance_card
            ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
        ]
        
        # حفظ مراجع البطاقات للتحكم فيها
        self.cards = [db_card, zk_card, paths_card, appearance_card]

    def expand_all_cards(self):
        """فتح جميع البطاقات"""
        for card in self.cards:
            content = card.content.content.controls[2]  # محتوى البطاقة
            icon = card.content.content.controls[0].trailing  # أيقونة الزر
            if not content.visible:
                self.toggle_card_expansion(content, icon)

    def collapse_all_cards(self):
        """طي جميع البطاقات"""
        for card in self.cards:
            content = card.content.content.controls[2]  # محتوى البطاقة
            icon = card.content.content.controls[0].trailing  # أيقونة الزر
            if content.visible:
                self.toggle_card_expansion(content, icon)

    def on_path_selected(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.save_and_log('Paths', 'postgres_bin', e.path, self.postgres_path_field)

    def change_theme(self, theme_name):
        self.config.set('Appearance', 'theme', theme_name)
        self.save_config()
        self.show_snackbar(f"تم تغيير الثيم إلى {theme_name}")
        self.apply_theme_to_all_pages(theme_name == 'dark')
        self.page.update()

    def apply_theme_to_all_pages(self, is_dark):
        """تطبيق المظهر على جميع الصفحات المفتوحة"""
        try:
            # البحث عن جميع النوافذ المفتوحة وتطبيق المظهر عليها
            for window in self.page.window_manager.windows if hasattr(self.page, 'window_manager') else []:
                if hasattr(window, 'page'):
                    window.page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
                    window.page.update()
        except Exception as e:
            logging.warning(f"Could not apply theme to all pages: {e}")

    def show_snackbar(self, message, color="green"):
        snack_bar = ft.SnackBar(ft.Text(message), bgcolor=color)
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()
        # Remove the snackbar after a delay
        self.page.overlay.remove(snack_bar)

    def test_db_connection(self, e=None):
        try:
            conn = psycopg2.connect(
                host=self.config.get('Database', 'host'),
                port=self.config.get('Database', 'port'),
                user=self.config.get('Database', 'user'),
                dbname=self.config.get('Database', 'dbname'),
                password=self.config.get('Database', 'password'),
                connect_timeout=3,
            )
            conn.close()
            self.db_status.value = "اتصال ناجح"
            self.db_status.color = "green"
        except Exception as ex:
            self.db_status.value = "اتصال فاشل"
            self.db_status.color = "red"
            logging.error(f"DB connection test failed: {ex}")
        self.page.update()
        return self.db_status.color == "green"

    def test_zk_connection(self, e=None):
        try:
            zk = ZK(self.config.get('Fingerprint', 'ip'), port=int(self.config.get('Fingerprint', 'port')), timeout=5)
            conn = zk.connect()
            if conn:
                self.zk_status.value = f"متصل: {conn.get_serialnumber()}"
                self.zk_status.color = "green"
                conn.disconnect()
            else:
                raise Exception("فشل في الاتصال بالجهاز")
        except Exception as ex:
            self.zk_status.value = "اتصال فاشل"
            self.zk_status.color = "red"
            logging.error(f"ZK connection test failed: {ex}")
        self.page.update()

    def toggle_progress(self, visible):
        self.progress_bar.visible = visible
        self.page.update()

    def init_backup(self):
        if not self.test_db_connection():
            self.show_snackbar("فشل التحقق من اتصال قاعدة البيانات!", "red")
            return
        self.backup_picker.get_directory_path(
            dialog_title="اختر مجلد لحفظ النسخة الاحتياطية"
        )

    def init_restore(self):
        if not self.test_db_connection():
            self.show_snackbar("فشل التحقق من اتصال قاعدة البيانات!", "red")
            return
        self.restore_picker.pick_files(
            allowed_extensions=["backup", "sql"],
            allow_multiple=False,
            dialog_title="اختر ملف النسخة الاحتياطية"
        )

    def on_backup_dir_selected(self, e):
        if not e.path:
            self.show_snackbar("لم يتم اختيار مجلد!", "red")
            return

        self.toggle_progress(True)
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_format = self.config.get('Settings', 'backup_format')
            ext = "backup" if backup_format == 'c' else 'sql'
            backup_file = os.path.join(e.path, f"attendance_backup_{timestamp}.{ext}")
            
            pg_dump_path = os.path.join(self.config.get('Paths', 'postgres_bin'), "pg_dump.exe")
            if not os.path.exists(pg_dump_path):
                raise FileNotFoundError(f"أداة pg_dump غير موجودة في المسار: {pg_dump_path}")
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.config.get('Database', 'password')

            cmd = [
                pg_dump_path,
                "-U", self.config.get('Database', 'user'),
                "-h", self.config.get('Database', 'host'),
                "-p", self.config.get('Database', 'port'),
                "-d", self.config.get('Database', 'dbname'),
                "-f", backup_file,
                "-F", backup_format
            ]

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )

            if os.path.exists(backup_file):
                self.show_snackbar("تم الإنشاء بنجاح: {backup_file}", "green")
                logging.info(f"Backup created: {backup_file}")
                # تسجيل الحدث
                current_username = self.page.session.get("username")
                from db import get_users, log_action
                users = get_users()
                user_id = next((u[0] for u in users if u[1] == current_username), None)
                if user_id:
                    log_action(user_id=user_id, action=f"أنشأ المستخدم {current_username} نسخة احتياطية")
            else:
                raise Exception("فشل في إنشاء الملف")

        except subprocess.CalledProcessError as e:
            error_msg = f"خطأ في النسخ الاحتياطي: {e.stderr}"
            self.show_snackbar(error_msg, "red")
            logging.error(error_msg)
        except Exception as e:
            self.show_snackbar(str(e), "red")
            logging.error(str(e))
        finally:
            self.toggle_progress(False)

    def on_restore_file_selected(self, e):
        if not e.files:
            self.show_snackbar("لم يتم اختيار ملف!", "red")
            return

        restore_file = e.files[0].path
        if not os.path.exists(restore_file):
            self.show_snackbar("الملف المحدد غير موجود!", "red")
            return

        self.toggle_progress(True)
        try:
            psql_path = os.path.join(self.config.get('Paths', 'postgres_bin'), "psql.exe")
            if not os.path.exists(psql_path):
                raise FileNotFoundError(f"أداة psql غير موجودة في المسار: {psql_path}")
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.config.get('Database', 'password')

            cmd = [
                psql_path,
                "-U", self.config.get('Database', 'user'),
                "-h", self.config.get('Database', 'host'),
                "-p", self.config.get('Database', 'port'),
                "-d", self.config.get('Database', 'dbname'),
                "-f", restore_file
            ]

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )

            self.show_snackbar("تم الاستعادة بنجاح", "green")
            logging.info(f"Database restored from: {restore_file}")
            # تسجيل الحدث
            current_username = self.page.session.get("username")
            from db import get_users, log_action
            users = get_users()
            user_id = next((u[0] for u in users if u[1] == current_username), None)
            if user_id:
                log_action(user_id=user_id, action=f"استعاد المستخدم {current_username} نسخة احتياطية")

        except subprocess.CalledProcessError as e:
            error_msg = f"خطأ في الاستعادة: {e.stderr}"
            self.show_snackbar(error_msg, "red")
            logging.error(error_msg)
        except Exception as e:
            self.show_snackbar(str(e), "red")
            logging.error(str(e))
        finally:
            self.toggle_progress(False)

def main(page: ft.Page):
    page.title = "إعدادات النظام"
    page.fonts = {"Cairo": "assets/fonts/Cairo-VariableFont_slnt,wght.ttf"}
    page.theme = ft.Theme(font_family="Cairo")
    page.padding = 30
    
    settings_page = SettingsPage(page)
    page.add(settings_page)

if __name__ == "__main__":
    ft.app(target=main)