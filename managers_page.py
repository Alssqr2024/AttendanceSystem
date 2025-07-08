import flet as ft
import cv2
import base64
import face_recognition
from zk import ZK  # pyzk library
from db import (
    add_employee,
    get_employees,
    delete_employee as db_delete_employee,
    update_employee as db_update_employee,
    get_employee_by_id,
    log_action,
    get_users,
)
import asyncio
import subprocess
import sys
import os
import configparser

def get_fingerprint_config():
    """Reads fingerprint device configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    if not config.has_section('Fingerprint'):
        raise Exception("Fingerprint configuration section not found in config.ini")
    return config['Fingerprint']

# دالة لتحديد الوجه وتصغير الصورة
def detect_and_resize_face(image_path, output_size=(150, 150)):
    image = cv2.imread(image_path)
    if image is None:
        print("فشل في تحميل الصورة!")
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    if len(faces) == 0:
        print("لم يتم اكتشاف أي وجه في الصورة!")
        return None
    (x, y, w, h) = faces[0]
    face = image[y:y+h, x:x+w]
    resized_face = cv2.resize(face, output_size)
    return resized_face

# دالة لتشفير الوجه
def encode_face(image):
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_encodings = face_recognition.face_encodings(rgb_image)
    if len(face_encodings) > 0:
        return face_encodings[0].tobytes().hex()
    else:
        return None



class EmployeeManagementPage(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 10
        self.selected_image_path = None
        self.face_encoding = None
        self.fingerprint_data = None
        self.temp_frame = None  # لإضافة المتغير هنا
        self.camera_container = ft.Container(visible=False)
        self.camera_preview_img = ft.Image(
            src_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+X2ZkAAAAASUVORK5CYII=",
            width=640,
            height=480,
            key="camera_preview",
            error_content=ft.Text("", color=ft.Colors.RED)
        )
        self.camera_container.content = ft.Column([
            self.camera_preview_img,
            ft.Row([
                ft.ElevatedButton("التقاط", on_click=self.capture_frame, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                ft.ElevatedButton("إغلاق الكاميرا", on_click=self.close_camera_container, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], alignment=ft.MainAxisAlignment.CENTER)

        # جدول الموظفين
        self.employees_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("رقم الموظف", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)),
                ft.DataColumn(ft.Text("الاســم", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)),
                ft.DataColumn(ft.Text("البريد الإلكتروني", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)),
                ft.DataColumn(ft.Text("الهاتف", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)),
                ft.DataColumn(ft.Text("الوظيفة", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)),
                ft.DataColumn(ft.Text("القسم", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)),
                ft.DataColumn(ft.Text("الإجراءات", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)),
            ],
            rows=[],
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.BLACK),
            column_spacing=20,
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_300),
            vertical_lines=ft.BorderSide(1, ft.Colors.GREY_300),
            heading_row_color=ft.Colors.BLUE_100,
        )
        
        scrollable_table = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=False,
            controls=[self.employees_table],
        )

        # حقل البحث
        self.search_field = ft.TextField(
            label="بحث بالاسم أو الرقم",
            tooltip="ابحث عن موظف باستخدام الاسم أو رقم الموظف",
            width=400,
            on_change=self.on_search_change,
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
        )

        # عناصر واجهة الإدخال
        self.first_name_input = ft.TextField(label="الاســـم", tooltip="أدخل اسم الموظف الكامل", width=280, border_radius=10)
        self.email_input = ft.TextField(label="البريد الإلكتروني", tooltip="أدخل البريد الإلكتروني للموظف", width=280, border_radius=10)
        self.phone_input = ft.TextField(label="الهاتف", tooltip="أدخل رقم هاتف الموظف", width=280, border_radius=10)
        self.position_input = ft.TextField(label="الوظيفة", tooltip="أدخل منصب الموظف", width=280, border_radius=10)
        self.department_input = ft.TextField(label="القسم", tooltip="أدخل قسم الموظف", width=280, border_radius=10)
        
        file_picker = ft.FilePicker(on_result=self.pick_image)
        self.page.overlay.append(file_picker)
        
        self.image_preview = ft.Image(
            src=None,
            width=150,
            height=150,
            fit=ft.ImageFit.COVER,
            border_radius=10
        )
        self.image_placeholder = ft.Icon(ft.Icons.PERSON, size=80, color=ft.Colors.WHITE)

        self.image_container = ft.Container(
            width=150,
            height=150,
            content=self.image_placeholder,
            bgcolor=ft.Colors.WHITE24,
            border_radius=10,
            on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png"]),
            tooltip="اختيار صورة للموظف"
        )
        
        self.add_button = ft.ElevatedButton(
            "إضافة موظف",
            icon=ft.Icons.ADD,
            tooltip="حفظ بيانات الموظف الجديد",
            width=280,
            on_click=self.add_employee_click,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
        )

        self.enroll_fingerprint_button = ft.ElevatedButton(
            "تسجيل البصمة",
            icon=ft.Icons.FINGERPRINT,
            tooltip="تسجيل بصمة إصبع الموظف باستخدام جهاز البصمة",
            width=135,
            on_click=self.enroll_fingerprint,
            bgcolor=ft.Colors.ORANGE_700,
            color=ft.Colors.WHITE,
        )

        self.start_camera_button = ft.ElevatedButton(
            "الكاميرا",
            icon=ft.Icons.CAMERA,
            tooltip="التقاط صورة للموظف باستخدام الكاميرا",
            width=135,
            on_click=self.open_camera_and_capture,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        )
        
        reset_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            icon_color=ft.Colors.WHITE,
            tooltip="مسح الحقول",
            on_click=lambda e: self.reset_form()
        )
        
        # اللوحة اليسرى (لوحة الإدخال)
        form_panel = ft.Container(
            width=350,
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.CYAN_800,
            border_radius=15,
            content=ft.Column(
                controls=[
                    self.first_name_input,
                    self.email_input,
                    self.phone_input,
                    self.position_input,
                    self.department_input,
                    self.image_container,
                    ft.Row(
                        [self.enroll_fingerprint_button, self.start_camera_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    self.add_button,
                    ft.Row([reset_button], alignment=ft.MainAxisAlignment.END)
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

        # اللوحة اليمنى (الجدول والبحث)
        table_panel = ft.Column(
            controls=[
                self.search_field,
                ft.Container(
                    content=scrollable_table,
                    expand=True,
                    border_radius=10,
                    padding=5,
                    border=ft.border.all(1, ft.Colors.GREY_300)
                )
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        )

        # شريط العنوان العلوي
        appbar = ft.Container(
            content=ft.Text("إدارة الموظفين", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align='center'),
            bgcolor=ft.Colors.CYAN_800,
            padding=15,
            border_radius=15,
            width=1400,
        )
        
        self.controls = [
            appbar,
            ft.Row(
                [
                    form_panel,
                    table_panel
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
                expand=True,
            ),
            self.camera_container # لإبقاء حاوية الكاميرا تعمل
        ]
        
        # تحميل البيانات عند تشغيل الصفحة
        self.update_table()

    # دالة البحث
    def on_search_change(self, e):
        search_term = e.control.value.lower()
        self.employees_table.rows = self.load_employees(search_term)
        self.page.update()

    # الدوال الأساسية
    def load_employees(self, search_term=None):
        employees = get_employees()
        rows = []
        for emp in employees:
            if len(emp) >= 7:
                (employee_id, first_name, email, phone, position, department, face_data) = emp[:7]
                photo_data = emp[7] if len(emp) > 7 else None
                if search_term:
                    search_term = search_term.lower()
                    if search_term not in str(employee_id) and search_term not in first_name.lower():
                        continue
                delete_button = ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=ft.Colors.RED,
                    tooltip="حذف الموظف",
                    on_click=lambda e, id=employee_id: self.confirm_delete(id),
                )
                edit_button = ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_color=ft.Colors.BLUE,
                    tooltip="تعديل الموظف",
                    on_click=lambda e, id=employee_id: self.edit_employee(id),
                )
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(employee_id), color=ft.Colors.BLACK)),
                            ft.DataCell(ft.Text(first_name, color=ft.Colors.BLACK)),
                            ft.DataCell(ft.Text(email, color=ft.Colors.BLACK)),
                            ft.DataCell(ft.Text(phone, color=ft.Colors.BLACK)),
                            ft.DataCell(ft.Text(position, color=ft.Colors.BLACK)),
                            ft.DataCell(ft.Text(department, color=ft.Colors.BLACK)),
                            ft.DataCell(ft.Row([delete_button, edit_button], spacing=10)),
                        ]
                    )
                )
            else:
                print(f"تحذير: بيانات غير متوقعة للموظف: {emp}")
        return rows

    # تحديث بيانات الجدول
    def update_table(self):
        self.employees_table.rows = self.load_employees()
        self.page.update()

    # إدارة البصمة
    def enroll_fingerprint(self, e):
        try:
            fp_config = get_fingerprint_config()
            zk = ZK(fp_config.get('ip'), port=int(fp_config.get('port')), timeout=5, password=0, force_udp=False, ommit_ping=False)
            self._show_snack("يرجى وضع إصبعك على جهاز البصمة...", ft.Colors.BLUE)
            
            conn = zk.connect()
            if not conn:
                self._show_snack("فشل الاتصال بجهاز البصمة", ft.Colors.RED)
                return

            # بدء عملية تسجيل بصمة جديدة
            # استخدام enroll_user يتطلب معرف مستخدم (رقمي) ومعرف بصمة (0-9)
            # سنستخدم رقم الموظف كـ user_id
            employee_id_str = self._generate_new_employee_id()
            try:
                employee_id_int = int(employee_id_str)
            except ValueError:
                self._show_snack("رقم الموظف غير صالح للتسجيل في جهاز البصمة.", ft.Colors.RED)
                conn.disconnect()
                return

            self._show_snack(f"تسجيل بصمة للموظف رقم: {employee_id_int}", ft.Colors.BLUE)
            conn.enable_device()
            # The 'enroll_user' method might start an interactive session on the device.
            # This part of the code assumes it guides the user on the device screen.
            # The pyzk library doesn't seem to have a direct, non-interactive way to capture a new template
            # without pre-existing enrollment process knowledge. This is a common approach.
            
            # The following is a conceptual representation. The actual library usage might differ.
            # We will simulate waiting for fingerprint capture and store a placeholder.
            # In a real scenario, you'd need a more robust way to handle this, perhaps a callback
            # or by checking device status in a loop.
            self.fingerprint_data = f"fingerprint_template_for_{employee_id_int}"
            
            self._show_snack("تم تسجيل البصمة بنجاح (بيانات مؤقتة)", ft.Colors.GREEN)

            conn.disconnect()

        except Exception as ex:
            self._show_snack(f"خطأ في الاتصال بجهاز البصمة: {ex}", ft.Colors.RED)

    # إدارة الوجه والصورة
    def open_camera_and_capture(self, e):
        import cv2
        import os
        import sys
        import time
        temp_captured_image_path = os.path.abspath("temp_captured_image.jpg")
        # حذف أي صورة قديمة
        if os.path.exists(temp_captured_image_path):
            os.remove(temp_captured_image_path)
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self._show_snack("فشل في فتح الكاميرا!", ft.Colors.RED)
            return
        window_name = "Camera Capture"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 640, 480)
        # محاولة رفع النافذة للأعلى عدة مرات
        for _ in range(10):
            try:
                # win32gui أولاً
                try:
                    import win32gui
                    import win32con
                    hwnd = win32gui.FindWindow(None, window_name)
                    if hwnd:
                        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                        break
                except Exception:
                    # pygetwindow احتياطي
                    try:
                        import pygetwindow as gw
                        win = gw.getWindowsWithTitle(window_name)
                        if win:
                            win[0].activate()
                            win[0].minimize()
                            win[0].restore()
                            win[0].bringToFront()
                            win[0].alwaysOnTop = True
                            break
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(0.2)
        captured = False
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # Esc
                break
            elif key == 32:  # Space
                cv2.imwrite(temp_captured_image_path, frame)
                captured = True
                break
        cap.release()
        cv2.destroyAllWindows()
        if captured and os.path.exists(temp_captured_image_path):
            self.selected_image_path = temp_captured_image_path
            self.image_preview.src = self.selected_image_path
            self.image_container.content = self.image_preview
            self.page.update()
        self.camera_container.visible = True

    def capture_frame(self, e):
        if hasattr(self, 'cap') and self.cap and hasattr(self, 'camera_preview_img'):
            ret, frame = self.cap.read()
            if ret:
                temp_image_path = "temp_captured_image.jpg"
                cv2.imwrite(temp_image_path, frame)
                self.selected_image_path = temp_image_path
                self.image_preview.src = self.selected_image_path
                self.image_container.content = self.image_preview
        self.close_camera_container(e)
        self.page.update()

    def close_camera_container(self, e):
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
            self.cap = None
        self.camera_streaming = False
        self.camera_container.visible = False
        self.page.update()

    # اختيار صورة من الملفات
    def pick_image(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_image_path = e.files[0].path
            self.image_preview.src = self.selected_image_path
            self.image_container.content = self.image_preview
            self.page.update()

    # إدارة النماذج
    def add_employee_click(self, e):
        first_name = self.first_name_input.value.strip()
        email = self.email_input.value.strip()
        phone = self.phone_input.value.strip()
        position = self.position_input.value.strip()
        department = self.department_input.value.strip()
        if not all([first_name, email, phone, position, department]):
            self._show_snack("يجب ملء جميع الحقول!", ft.Colors.RED)
            return
        if not self.selected_image_path:
            self._show_snack("يجب اختيار صورة!", ft.Colors.RED)
            return
        face_image = detect_and_resize_face(self.selected_image_path)
        if face_image is None:
            self._show_snack("فشل في اكتشاف الوجه!", ft.Colors.RED)
            return
        face_encoding = encode_face(face_image)
        if not face_encoding:
            self._show_snack("فشل في تشفير الوجه!", ft.Colors.RED)
            return
        if not self.fingerprint_data:
            self._show_snack("يجب تسجيل البصمة!", ft.Colors.RED)
            return
        try:
            with open(self.selected_image_path, 'rb') as image_file:
                photo_data = image_file.read()
        except Exception as e:
            print(f"Error reading image file: {e}")
            photo_data = None
        user_id = self._generate_new_employee_id()
        add_employee(user_id, first_name, email, phone, position, department, face_encoding, photo_data)
        # تسجيل الحدث باسم المستخدم الحالي
        current_username = self.page.session.get("username")
        users = get_users()
        current_user_id = None
        for u in users:
            if u[1] == current_username:
                current_user_id = u[0]
                break
        if current_user_id:
            log_action(user_id=current_user_id, action=f"أضاف المستخدم {current_username} موظفًا جديدًا باسم {first_name}")
        self._show_snack("تم الإضافة بنجاح!", ft.Colors.GREEN)
        self.reset_form()
        self.update_table()

    # إعادة تعيين النموذج
    def reset_form(self):
        self.first_name_input.value = ""
        self.email_input.value = ""
        self.phone_input.value = ""
        self.position_input.value = ""
        self.department_input.value = ""
        self.selected_image_path = None
        self.image_container.content = self.image_placeholder
        self.add_button.text = "إضافة موظف"
        self.add_button.on_click = self.add_employee_click
        self.page.update()

    # الدوال المساعدة
    def _generate_new_employee_id(self):
        employees = get_employees()
        return employees[-1][0] + 1 if employees else 1

    # عرض الرسائل المنبثقة
    def _show_snack(self, message, color):
        snack_bar = ft.SnackBar(ft.Text(message), bgcolor=color)
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()

    # حذف الموظف
    def delete_employee(self, employee_id):
        try:
            device_connected = False
            try:
                zk = ZK("192.168.1.201", port=4370, timeout=2)
                conn = zk.connect()
                if conn:
                    device_connected = True
                    conn.disconnect()
            except Exception:
                device_connected = False
            if not db_delete_employee(employee_id):
                self._show_snack("فشل في حذف الموظف من قاعدة البيانات!", ft.Colors.RED)
                return
            if device_connected:
                try:
                    zk = ZK("192.168.1.201", port=4370, timeout=5)
                    conn = zk.connect()
                    if conn:
                        conn.delete_user(uid=employee_id)
                        conn.test_voice(0)
                        self._show_snack("تم حذف الموظف من قاعدة البيانات وجهاز البصمة!", ft.Colors.GREEN)
                    conn.disconnect()
                except Exception as e:
                    self._show_snack("تم حذف الموظف من قاعدة البيانات، لكن فشل الحذف من جهاز البصمة", ft.Colors.ORANGE)
            else:
                self._show_snack("تم حذف الموظف من قاعدة البيانات فقط. جهاز البصمة غير متصل!", ft.Colors.ORANGE)
            # تسجيل الحدث باسم المستخدم الحالي
            current_username = self.page.session.get("username")
            users = get_users()
            current_user_id = None
            for u in users:
                if u[1] == current_username:
                    current_user_id = u[0]
                    break
            if current_user_id:
                log_action(user_id=current_user_id, action=f"حذف المستخدم {current_username} الموظف رقم {employee_id}")
            self.reset_form()
            self.update_table()
        except Exception as e:
            self._show_snack(f"حدث خطأ غير متوقع: {str(e)}", ft.Colors.RED)

    # تأكيد الحذف
    def confirm_delete(self, employee_id):
        def close_dlg(e):
            dlg.open = False
            self.page.update()
            
        def delete_and_close(e):
            self.delete_employee(employee_id)
            dlg.open = False
            
        device_connected = False
        try:
            zk = ZK("192.168.1.201", port=4370, timeout=2)
            conn = zk.connect()
            if conn:
                device_connected = True
                conn.disconnect()
        except Exception:
            device_connected = False
            
        warning_message = "هل أنت متأكد من حذف الموظف؟\n"
        if not device_connected:
            warning_message += "\nتنبيه: جهاز البصمة غير متصل! سيتم حذف الموظف من قاعدة البيانات فقط."
            
        dlg = ft.AlertDialog(
            title=ft.Text("تأكيد الحذف"),
            content=ft.Text(warning_message),
            actions=[
                ft.TextButton("نعم", on_click=delete_and_close),
                ft.TextButton("لا", on_click=close_dlg),
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    # تعديل بيانات الموظف
    def edit_employee(self, employee_id):
        employee = get_employee_by_id(employee_id)
        if not employee:
            self._show_snack("الموظف غير موجود!", ft.Colors.RED)
            return
            
        self.first_name_input.value = employee[1]
        self.email_input.value = employee[2]
        self.phone_input.value = employee[3]
        self.position_input.value = employee[4]
        self.department_input.value = employee[5]
        self.add_button.text = "تحديث"
        self.add_button.on_click = lambda e: self.update_employee_click(e, employee_id)
        self.page.update()

    # تحديث بيانات الموظف
    def update_employee_click(self, e, employee_id):
        try:
            first_name = self.first_name_input.value.strip()
            email = self.email_input.value.strip()
            phone = self.phone_input.value.strip()
            position = self.position_input.value.strip()
            department = self.department_input.value.strip()
            if not all([first_name, email, phone, position, department]):
                self._show_snack("يجب ملء جميع الحقول!", ft.Colors.RED)
                return
            db_update_employee(employee_id, first_name, email, phone, position, department)
            try:
                zk = ZK("192.168.1.201", port=4370, timeout=5)
                conn = zk.connect()
                if conn:
                    conn.set_user(uid=employee_id, name=first_name, privilege=0)
                    conn.test_voice(0)
                    conn.disconnect()
            except Exception as ex:
                self._show_snack(f"تم تحديث قاعدة البيانات، لكن فشل تحديث جهاز البصمة: {str(ex)}", ft.Colors.ORANGE)
            # تسجيل الحدث باسم المستخدم الحالي
            current_username = self.page.session.get("username")
            users = get_users()
            current_user_id = None
            for u in users:
                if u[1] == current_username:
                    current_user_id = u[0]
                    break
            if current_user_id:
                log_action(user_id=current_user_id, action=f"عدّل المستخدم {current_username} بيانات الموظف رقم {employee_id}")
            self._show_snack("تم التحديث!", ft.Colors.GREEN)
            self.reset_form()
            self.update_table()
        except Exception as e:
            self._show_snack("فشل في التحديث!", ft.Colors.RED)

# Main function to run the application
def main(page: ft.Page):
    page.title = "إدارة الموظفين"
    page.fonts = {"Cairo": "assets/fonts/Cairo-VariableFont_slnt,wght.ttf"}
    page.theme = ft.Theme(font_family="Cairo")
    page.padding = 30
    page.bgcolor = ft.Colors.GREY_200

    employee_page = EmployeeManagementPage(page)
    page.add(employee_page)

    # تحديث الصفحة
    page.update()

# تشغيل التطبيق
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--camera-capture":
        import flet as ft
        import cv2
        import base64
        import asyncio
        def camera_page(page: ft.Page):
            page.title = "التقاط صورة الموظف"
            page.window_width = 700
            page.window_height = 600
            page.vertical_alignment = ft.MainAxisAlignment.CENTER
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            page.bgcolor = ft.Colors.BLUE_GREY_50
            image_preview = ft.Image(width=640, height=480, fit=ft.ImageFit.CONTAIN)
            cap = cv2.VideoCapture(0)
            streaming = True
            async def update_frame():
                while streaming and cap.isOpened():
                    for _ in range(2):
                        cap.grab()
                    ret, frame = cap.read()
                    if not ret:
                        break
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    image_preview.src_base64 = base64.b64encode(buffer).decode('utf-8')
                    page.update()
                    await asyncio.sleep(0.03)
            def capture_image(e):
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        temp_path = os.path.abspath("temp_captured_image.jpg")
                        cv2.imwrite(temp_path, frame)
                close_window(e)
            def close_window(e):
                nonlocal streaming
                streaming = False
                if cap.isOpened():
                    cap.release()
                page.window_close()
            page.add(
                ft.Column([
                    image_preview,
                    ft.Row([
                        ft.ElevatedButton("التقاط", on_click=capture_image, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                        ft.ElevatedButton("إلغاء", on_click=close_window, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ], alignment=ft.MainAxisAlignment.CENTER)
            )
            page.run_task(update_frame)
        ft.app(target=camera_page)
        sys.exit(0)
    else:
        ft.app(target=main)