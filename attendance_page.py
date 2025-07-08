# attendance_page.py
#----------------------------------استيراد المكتبات----------------------------------
import flet as ft # Flet library for UI
import cv2 # OpenCV for video capture and image processing
import face_recognition # Face recognition library for detecting and recognizing faces
import numpy as np # NumPy for numerical operations
import base64 # Base64 for encoding images
import asyncio # Asyncio for asynchronous programming
from datetime import datetime # For handling dates and times
from db import get_employees, record_check_in, record_check_out, get_attendance_status, get_users, log_action # Database functions for attendance records
from zk import ZK # ZK library for fingerprint attendance system
import time # Time library for delays
#------------------------------إنشاء نظام الحضور والانصراف------------------
def create_attendance_system(page: ft.Page, on_back=None):
    page.title = "نظام الحضور والانصراف"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20
    page.bgcolor = ft.Colors.BLUE_GREY_50

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        page.add(ft.Text("خطأ: الكاميرا غير متاحة!", size=20, color=ft.Colors.RED))
        return

    image_preview = ft.Image(width=640, height=480, fit=ft.ImageFit.CONTAIN, border_radius=10)

    check_in_button = ft.ElevatedButton(
        "التحضير", icon=ft.Icons.LOGIN,
        bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )
    check_out_button = ft.ElevatedButton(
        "الانصراف", icon=ft.Icons.LOGOUT,
        bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )
    check_in_button.on_click = lambda e: page.run_task(check_in, e)
    check_out_button.on_click = lambda e: page.run_task(check_out, e)

    face_recognition_attempts = 0 # متغير لتتبع عدد محاولات التعرف على الوجه
    max_face_attempts = 3 # الحد الأقصى لعدد المحاولات
    frame_task = None  # لتخزين مهمة update_frame الحالية
    fingerprint_lock = False  # متغير حماية لمنع تكرار التحقق بالبصمة
    is_verifying_fingerprint = False  # متغير لإيقاف تحديث الكاميرا مؤقتًا أثناء التحقق بالبصمة

    # --- إضافة دروب داون لاختيار الكاميرا ---
    camera_options = [
        ("كاميرا الكمبيوتر (الافتراضية)", 0),
        ("كاميرا خارجية 1", 1),
        ("كاميرا خارجية 2", 2),
        ("كاميرا خارجية 3", 3),
    ]
    selected_camera_index = 0
    camera_dropdown = ft.Dropdown(
        label="اختر الكاميرا المستخدمة",
        width=300,
        value=str(selected_camera_index),
        options=[ft.dropdown.Option(str(idx), name) for name, idx in camera_options],
    )

    def set_camera(index):
        nonlocal cap, selected_camera_index
        # جرّب فتح الكاميرا الجديدة أولاً
        new_cap = cv2.VideoCapture(index)
        if not new_cap.isOpened():
            snack_bar = ft.SnackBar(ft.Text(f"❌ لا يمكن الوصول إلى الكاميرا رقم {index}! تأكد من توصيلها أو اختر كاميرا أخرى."), bgcolor=ft.Colors.RED)
            page.overlay.append(snack_bar)
            snack_bar.open = True
            page.update()
            return  # لا تغيّر الكاميرا الحالية
        # إذا نجح فتح الكاميرا الجديدة، أغلق القديمة وبدّل
        if cap and cap.isOpened():
            cap.release()
        cap = new_cap
        selected_camera_index = index
        page.update()

    def on_camera_change(e):
        idx = int(e.control.value)
        set_camera(idx)

    camera_dropdown.on_change = on_camera_change

    # --- تهيئة الكاميرا الافتراضية عند بدء الصفحة ---
    set_camera(selected_camera_index)

#------------------------------إغلاق الصفحة------------------
    def close_page(e):
        cap.release()
        page.window_close()
#------------------------------إعادة تشغيل الكاميرا------------------
    def restart_camera():
        nonlocal cap
        
        try:
            if cap.isOpened():
                cap.release()
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                snack_bar = ft.SnackBar(ft.Text("تم إعادة تشغيل الكاميرا بنجاح!"), bgcolor=ft.Colors.GREEN)
            else:
                raise Exception("الكاميرا غير متاحة")
        except Exception as e:
            snack_bar = ft.SnackBar(ft.Text(f"فشل في إعادة تشغيل الكاميرا: {e}"), bgcolor=ft.Colors.RED)
        
        page.overlay.append(snack_bar)
        snack_bar.open = True
        page.update()
        
        # إعادة تشغيل مؤشر الإطارات باستخدام page.run_task
        page.run_task(update_frame)
#------------------------------تحديث الإطار------------------
    async def update_frame():
        nonlocal frame_task
        while cap.isOpened():
            if is_verifying_fingerprint:
                await asyncio.sleep(0.1)
                continue
            # تخطي كل إطار ثاني لتخفيف الحمل
            for _ in range(2):
                cap.grab()
            
            ret, frame = cap.read()
            if not ret:
                print("خطأ في قراءة الإطار.")
                break
            
            # تقليل دقة الإطار
            small_frame = cv2.resize(frame, (320, 240))
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # الكشف عن الوجوه
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # رسم المستطيلات على الإطار الأصلي
            for (top, right, bottom, left) in face_locations:
                # ضرب الإحداثيات بمعامل التصغير
                top, right, bottom, left = [x*2 for x in (top, right, bottom, left)]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # تشفير الإطار بجودة أقل
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            image_preview.src_base64 = base64.b64encode(buffer).decode("utf-8")
            
            page.update()
            await asyncio.sleep(0.03)  # تقليل وقت الانتظار
#------------------------------التعرف على الوجه------------------
    # تعديل دالة recognize_face
    def recognize_face(face_encoding):
        employees = get_employees()
        best_match = None
        best_distance = float('inf')
        
        for emp in employees:
            if len(emp) >= 7:
                emp_id, first_name = emp[0], emp[1]
                face_data = emp[6] if len(emp) > 6 else None
                
                if face_data:
                    try:
                        known_face_encoding = np.frombuffer(bytes.fromhex(face_data), dtype=np.float64)
                        distance = face_recognition.face_distance([known_face_encoding], face_encoding)[0]
                        
                        # زيادة المسافة المسموح بها للحصول على نتائج أكثر تساهلاً
                        if distance < 0.6 and distance < best_distance:
                            best_distance = distance
                            best_match = (emp_id, first_name)
                    except Exception as e:
                        print(f"خطأ في تحليل بصمة الوجه: {e}")
        
        return best_match if best_match else (None, None)
#------------------------------عرض نافذة التأكيد------------------   
    async def show_confirmation_dialog(employee_id, first_name, show_bypass=False):
        nonlocal face_recognition_attempts
        confirm = False
        bypass_option = False

        def nonlocal_assignment(value):
            nonlocal bypass_option
            bypass_option = value

        def on_confirm(e):
            nonlocal confirm
            confirm = True
            dialog.open = False
            page.update()

        def on_cancel(e):
            nonlocal confirm, bypass_option
            dialog.open = False
            page.update()

        # محتوى نافذة التأكيد المحسنة
        dialog_content = [
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PERSON_SEARCH, size=60, color=ft.Colors.BLUE_600),
                    ft.Text(
                        "تأكيد الهوية",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_900,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=15,
            ),
            
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"هل أنت:",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_800,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        f"السيد/ة {first_name}",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        f"رقم الموظف: {employee_id}",
                        size=16,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
            ),
            
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.WARNING_AMBER, size=40, color=ft.Colors.ORANGE_600),
                    ft.Text(
                        "⚠️ يرجى التأكيد على أنك الشخص المحدد قبل المتابعة",
                        size=16,
                        color=ft.Colors.ORANGE_800,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.W_500,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15,
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=10,
            )
        ]

        if show_bypass:
            dialog_content.insert(1, ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INFO, size=30, color=ft.Colors.AMBER_600),
                    ft.Text(
                        "⚠️ تجاوزت الحد الأقصى للمحاولات. يمكنك الآن تخطي التعرف على الوجه.",
                        size=14,
                        color=ft.Colors.AMBER_800,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Checkbox(
                        label="تخطي التعرف على الوجه في المحاولة التالية",
                        on_change=lambda e: nonlocal_assignment(e.control.value),
                        fill_color=ft.Colors.AMBER_600,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15,
                bgcolor=ft.Colors.AMBER_50,
                border_radius=10,
            ))

        dialog = ft.AlertDialog(
            modal=True,
            title=None,  # إزالة العنوان الافتراضي
            content=ft.Container(
                content=ft.Column(dialog_content, 
                                alignment=ft.MainAxisAlignment.CENTER,
                                expand=True,
                                spacing=15,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
            ),
            actions=[
                ft.Container(
                    content=ft.Row([
                        ft.ElevatedButton(
                            "❌ إلغاء",
                            on_click=on_cancel,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.RED_600,
                                color=ft.Colors.WHITE,
                                padding=ft.padding.all(15),
                            ),
                        ),
                        ft.ElevatedButton(
                            "✅ نعم، هذا أنا",
                            on_click=on_confirm,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.GREEN_600,
                                color=ft.Colors.WHITE,
                                padding=ft.padding.all(15),
                            ),
                        ),
                    ], spacing=20, alignment=ft.MainAxisAlignment.CENTER),
                    padding=20,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

        while dialog.open:
            await asyncio.sleep(0.1)

        return confirm, bypass_option
#------------------------------ التحقق من البصمة------------------
    async def show_fingerprint_snackbar(page, msg, color=ft.Colors.BLUE, duration=5000):
        print(f"[DEBUG] محاولة فتح SnackBar: {msg}")
        snack = ft.SnackBar(
            ft.Row([
                ft.Icon(ft.Icons.FINGERPRINT, color=ft.Colors.WHITE),
                ft.Text(msg, color=ft.Colors.WHITE, size=18)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=color,
            duration=duration
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
        await asyncio.sleep(duration / 1000)
        snack.open = False
        page.update()
        print("[DEBUG] SnackBar أغلق.")

    async def verify_fingerprint(user_id):
        nonlocal fingerprint_lock
        nonlocal is_verifying_fingerprint
        if fingerprint_lock:
            print("محاولة تحقق بالبصمة قيد التنفيذ بالفعل.")
            return False
        fingerprint_lock = True
        is_verifying_fingerprint = True

        await show_fingerprint_snackbar(page, "جاري التحقق من البصمة... يرجى وضع إصبعك على الجهاز", ft.Colors.BLUE, 5000)

        ip = await load_fingerprint_ip()
        port = 4370
        max_retries = 3  # عدد محاولات التحقق
        retry_count = 0
        success = False
        conn = None
        print(f"بدء عملية التحقق بالبصمة... IP: {ip}")
        
        def reset_connection():
            nonlocal conn
            if conn:
                try:
                    conn.disconnect()
                    print("تم قطع الاتصال بجهاز البصمة (تهيئة جديدة)")
                except Exception as ex:
                    print(f"فشل في disconnect: {ex}")
            conn = None

        try:
            while retry_count < max_retries and not success:
                reset_connection()
                try:
                    zk = ZK(ip, port=port, timeout=5)
                    conn = zk.connect()
                    print(f"تم الاتصال بجهاز البصمة (محاولة {retry_count+1})")
                    start_time = asyncio.get_event_loop().time()
                    timeout = 10
                    while (asyncio.get_event_loop().time() - start_time) < timeout and not success:
                        remaining = max(0, int(timeout - (asyncio.get_event_loop().time() - start_time)))
                        await show_fingerprint_snackbar(page, f"جاري التحقق من البصمة... يرجى وضع إصبعك على الجهاز خلال {remaining} ثانية", ft.Colors.YELLOW, 1000)
                        for attendance in conn.live_capture():
                            print(f"التقاط: {attendance}, user_id: {getattr(attendance, 'user_id', None)}")
                            show_fingerprint_snackbar(page, f"جاري التحقق من البصمة... يرجى وضع إصبعك على الجهاز خلال {remaining} ثانية", ft.Colors.YELLOW, 1000)
                            if attendance:
                                scanned_id = str(getattr(attendance, 'user_id', '')).strip()
                                if scanned_id == str(user_id).strip():
                                    success = True
                                    await show_fingerprint_snackbar(page, "✅ تم التحقق من البصمة بنجاح!", ft.Colors.GREEN, 2000)
                                    print("تمت مطابقة البصمة بنجاح!")
                                    await asyncio.sleep(1)
                                    break
                                else:
                                    # بصمة شخص آخر
                                    await show_fingerprint_snackbar(page, "❌ البصمة لا تخص الموظف المحدد! يرجى وضع إصبع الموظف الصحيح.", ft.Colors.RED, 2000)
                                    print("بصمة غير مطابقة للموظف المحدد. العودة لبداية العملية.")
                                    fingerprint_lock = False
                                    is_verifying_fingerprint = False
                                    page.run_task(update_frame)
                                    return False
                        if success:
                            break
                        await asyncio.sleep(0.5)
                    if not success:
                        await show_fingerprint_snackbar(page, "❌ لم يتم التعرف على البصمة. إعادة المحاولة...", ft.Colors.RED, 2000)
                        retry_count += 1
                        await asyncio.sleep(1)
                    else:
                        break
                except Exception as e:
                    print(f"خطأ في التحقق من البصمة: {e}")
                    print(f"خطأ في جهاز البصمة: {e}")
                    await show_fingerprint_snackbar(page, f"⚠️ خطأ في الاتصال بالجهاز: {str(e)}", ft.Colors.RED, 2000)
                    retry_count += 1
                    await asyncio.sleep(1)
                finally:
                    reset_connection()
        finally:
            is_verifying_fingerprint = False
            page.run_task(update_frame)

        if not success:
            await show_fingerprint_snackbar(page, "❌ فشل التحقق من البصمة! يرجى المحاولة مرة أخرى.", ft.Colors.RED, 3000)
            fingerprint_lock = False
            return False
        fingerprint_lock = False
        return True
#------------------------------الاختيار اليدوي للموظف------------------
    async def show_employee_selector():
        print("تم استدعاء show_employee_selector")  # للتأكد من التنفيذ
        employees = get_employees()
        if not employees:
            page.snack_bar = ft.SnackBar(ft.Text("❌ لا يوجد موظفين في النظام!"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
            return None
        employee_options = {str(emp[0]): emp[1] for emp in employees}  # emp_id: name
        selected_emp = ft.Ref[ft.Dropdown]()
        dialog = ft.AlertDialog(
            title=ft.Text("اختر اسمك من القائمة"),
            content=ft.Dropdown(
                ref=selected_emp,
                options=[ft.dropdown.Option(k, v) for k, v in employee_options.items()],
                width=300
            ),
            actions=[
                ft.TextButton("تأكيد", on_click=lambda e: setattr(dialog, "open", False)),
                ft.TextButton("إلغاء", on_click=lambda e: setattr(dialog, "open", False)),
            ]
        )
        page.dialog = None  # أفرغ أي Dialog سابق
        page.overlay.append(dialog)  # استخدم overlay بدلاً من page.dialog
        dialog.open = True
        page.update()
        while dialog.open:
            await asyncio.sleep(0.1)
        if selected_emp.current.value:
            selected_id = selected_emp.current.value
            selected_name = employee_options[selected_id]
            return (selected_id, selected_name)
        return None
#-------------------------------تسجيل الدخول-----------------------
    async def check_in(e):
        nonlocal face_recognition_attempts
        snack_bar = None  # ضمان التعريف
        try:
            # 1. التقاط صورة من الكاميرا
            ret, frame = cap.read()
            if not ret:
                raise Exception("خطأ في الكاميرا!")
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            if not face_encodings:
                face_recognition_attempts += 1
                raise Exception("لم يتم اكتشاف أي وجه! يرجى الوقوف أمام الكاميرا.")

            # 2. التعرف على الوجه
            employee_id, first_name = recognize_face(face_encodings[0])

            if not employee_id or not first_name:
                face_recognition_attempts += 1
                if face_recognition_attempts >= max_face_attempts:
                    print("سيتم عرض كومبوبوكس اختيار الموظف الآن")  # للتأكد من التنفيذ
                    selected = await show_employee_selector()
                    if selected:
                        employee_id, first_name = selected
                        face_recognition_attempts = 0
                        # أكمل العملية من هنا
                    else:
                        snack_bar = ft.SnackBar(ft.Text("تم إلغاء العملية من قبل المستخدم."), bgcolor=ft.Colors.RED)
                        page.overlay.append(snack_bar)
                        snack_bar.open = True
                        page.update()
                        return
                else:
                    snack_bar = ft.SnackBar(ft.Text("⚠️ لم يتم التعرف على الوجه! يرجى المحاولة مرة أخرى."), bgcolor=ft.Colors.RED)
                    page.overlay.append(snack_bar)
                    snack_bar.open = True
                    page.update()
                    return

            # 3. عرض نافذة تأكيد الهوية
            confirmed, bypass = await show_confirmation_dialog(
                employee_id, first_name,
                show_bypass=(face_recognition_attempts >= max_face_attempts)
            )
            if not confirmed:
                if bypass:
                    try:
                        manual_employee = await show_employee_selector()
                    except asyncio.CancelledError:
                        manual_employee = None
                    if manual_employee:
                        employee_id, first_name = manual_employee
                        face_recognition_attempts = 0
                        confirmed = True
                    else:
                        snack_bar = ft.SnackBar(ft.Text("تم إلغاء العملية من قبل المستخدم."), bgcolor=ft.Colors.RED)
                        page.overlay.append(snack_bar)
                        snack_bar.open = True
                        page.update()
                        return
                else:
                    face_recognition_attempts += 1
                    snack_bar = ft.SnackBar(ft.Text("تم إلغاء العملية من قبل المستخدم."), bgcolor=ft.Colors.RED)
                    page.overlay.append(snack_bar)
                    snack_bar.open = True
                    page.update()
                    return

            # إعادة تعيين العداد بعد النجاح
            face_recognition_attempts = 0

            # 4. التحقق من الحضور السابق
            today = datetime.now().date()
            attendance_status = get_attendance_status(employee_id, today)
            if attendance_status and attendance_status.get('check_in_time'):
                check_in_time = attendance_status['check_in_time']
                msg = f"⚠️ السيد/ة {first_name} قد حضر/ت اليوم في الساعة {check_in_time.strftime('%H:%M')}"
                snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.ORANGE)
                page.overlay.append(snack_bar)
                snack_bar.open = True
                page.update()
                return

            # 5. التحقق من البصمة
            if not await verify_fingerprint(employee_id):
                snack_bar = ft.SnackBar(ft.Text("❌ فشل التحقق من البصمة! البصمة لا تطابق هوية الموظف."), bgcolor=ft.Colors.RED)
                page.overlay.append(snack_bar)
                snack_bar.open = True
                page.update()
                return

            # 6. تسجيل الحضور
            result = record_check_in(employee_id, today)
            if result:
                msg = f"✅ تم تسجيل الحضور بنجاح: {first_name}"
                color = ft.Colors.GREEN
                current_username = page.session.get("username")
                users = get_users()
                current_user_id = None
                for u in users:
                    if u[1] == current_username:
                        current_user_id = u[0]
                        break
                if current_user_id:
                    log_action(user_id=current_user_id, action=f"سجّل {current_username} حضور الموظف {first_name}")
                else:
                    log_action(employee_id=employee_id, action=f"تسجيل حضور ذاتي - {first_name}")
            else:
                msg = f"⚠️ تم تسجيل الحضور مسبقًا لهذا الموظف اليوم: {first_name}"
                color = ft.Colors.ORANGE
            snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
            page.overlay.append(snack_bar)
            snack_bar.open = True
            page.update()
        except Exception as ex:
            if not snack_bar:
                snack_bar = ft.SnackBar(ft.Text(str(ex)), bgcolor=ft.Colors.RED)
                page.overlay.append(snack_bar)
                snack_bar.open = True
                page.update()
# ------------------------------تسجيل الانصراف-----------------------
    async def check_out(e):
        nonlocal face_recognition_attempts
        snack_bar = None  # ضمان التعريف
        try:
            # 1. التقاط صورة من الكاميرا
            ret, frame = cap.read()
            if not ret:
                raise Exception("خطأ في الكاميرا!")
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            if not face_encodings:
                face_recognition_attempts += 1
                raise Exception("لم يتم اكتشاف أي وجه! يرجى الوقوف أمام الكاميرا.")
            # 2. التعرف على الوجه
            employee_id, first_name = recognize_face(face_encodings[0])
            if not employee_id or not first_name:
                face_recognition_attempts += 1
                if face_recognition_attempts >= max_face_attempts:
                    print("سيتم عرض كومبوبوكس اختيار الموظف الآن (انصراف)")  # للتأكد من التنفيذ
                    selected = await show_employee_selector()
                    if selected:
                        employee_id, first_name = selected
                        # أكمل العملية من هنا
                    else:
                        snack_bar = ft.SnackBar(ft.Text("تم إلغاء العملية من قبل المستخدم."), bgcolor=ft.Colors.RED)
                        page.overlay.append(snack_bar)
                        snack_bar.open = True
                        page.update()
                        return
                else:
                    snack_bar = ft.SnackBar(ft.Text("⚠️ لم يتم التعرف على الوجه! يرجى المحاولة مرة أخرى."), bgcolor=ft.Colors.RED)
                    page.overlay.append(snack_bar)
                    snack_bar.open = True
                    page.update()
                    return

            # 3. عرض نافذة تأكيد الهوية
            confirmed, bypass = await show_confirmation_dialog(
                employee_id, first_name,
                show_bypass=(face_recognition_attempts >= max_face_attempts)
            )
            if not confirmed:
                if bypass:
                    try:
                        manual_employee = await show_employee_selector()
                    except asyncio.CancelledError:
                        manual_employee = None
                    if manual_employee:
                        employee_id, first_name = manual_employee
                        face_recognition_attempts = 0
                        confirmed = True
                    else:
                        snack_bar = ft.SnackBar(ft.Text("تم إلغاء العملية من قبل المستخدم."), bgcolor=ft.Colors.RED)
                        page.overlay.append(snack_bar)
                        snack_bar.open = True
                        page.update()
                        return
                else:
                    face_recognition_attempts += 1
                    snack_bar = ft.SnackBar(ft.Text("تم إلغاء العملية من قبل المستخدم."), bgcolor=ft.Colors.RED)
                    page.overlay.append(snack_bar)
                    snack_bar.open = True
                    page.update()
                    return

            # إعادة تعيين العداد بعد النجاح
            face_recognition_attempts = 0

            # 4. التحقق من الحضور
            today = datetime.now().date()
            attendance_status = get_attendance_status(employee_id, today)
            
            if not attendance_status or not attendance_status.get('check_in_time'):
                # الموظف لم يحضر اليوم
                msg = f"⚠️ السيد/ة {first_name} لم يحضر/تحضر اليوم بعد!"
                snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.RED)
                page.overlay.append(snack_bar)
                snack_bar.open = True
                page.update()
                return
            
            # تحقق من مرور 5 دقائق على الأقل بين الحضور والانصراف
            check_in_time = attendance_status['check_in_time']
            now = datetime.now()
            if (now - check_in_time).total_seconds() < 5 * 60:
                msg = "لا يمكنك تسجيل الانصراف إلا بعد مرور 5 دقائق على الأقل من تسجيل الحضور."
                snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.ORANGE)
                page.overlay.append(snack_bar)
                snack_bar.open = True
                page.update()
                return
            
            if attendance_status.get('check_out_time'):
                # الموظف قد انصرف اليوم
                check_out_time = attendance_status['check_out_time']
                msg = f"⚠️ السيد/ة {first_name} قد انصرف/ت اليوم في الساعة {check_out_time.strftime('%H:%M')}"
                snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.ORANGE)
                page.overlay.append(snack_bar)
                page.update()
                return
            
            # 5. التحقق من البصمة
            result = await verify_fingerprint(employee_id)
            if not result:
                raise Exception("❌ فشل التحقق من البصمة! البصمة لا تطابق هوية الموظف.")

            # 6. تسجيل الانصراف
            duration = record_check_out(employee_id)
            if duration:
                hours, remainder = divmod(duration.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                msg = f"✅ تم تسجيل الانصراف بنجاح: {first_name} (المدة: {hours} ساعة و{minutes} دقيقة)"
                color = ft.Colors.GREEN
                # --- تسجيل الحدث ---
                current_username = page.session.get("username")
                users = get_users()
                current_user_id = None
                for u in users:
                    if u[1] == current_username:
                        current_user_id = u[0]
                        break
                if current_user_id:
                    log_action(user_id=current_user_id, action=f"سجّل {current_username} انصراف الموظف {first_name}")
                else:
                    log_action(employee_id=employee_id, action=f"تسجيل انصراف ذاتي - {first_name}")
            else:
                msg = f"⚠️ لم يتم تسجيل الحضور لهذا الموظف اليوم: {first_name}"
                color = ft.Colors.RED
            
            snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
            page.overlay.append(snack_bar)
        
        except Exception as ex:
            snack_bar = ft.SnackBar(ft.Text(str(ex)), bgcolor=ft.Colors.RED)
            print(f"خطأ في تسجيل الانصراف: {ex}")
            page.overlay.append(snack_bar)
        
        finally:
            snack_bar.open = True
            page.update()

    restart_camera_button = ft.ElevatedButton(
        "إعادة تشغيل الكاميرا", icon=ft.Icons.CAMERA, on_click=lambda e: restart_camera(),
        bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    # إضافة زر إدارة جهاز البصمة
    async def manage_fingerprint_device(e):
        """إدارة جهاز البصمة"""
        action, new_ip = await show_fingerprint_error_dialog()
        
        if action == "restart":
            success, msg = await restart_fingerprint_device()
            if success:
                snack_bar = ft.SnackBar(
                    ft.Text(f"✅ {msg}"),
                    bgcolor=ft.Colors.GREEN
                )
            else:
                snack_bar = ft.SnackBar(
                    ft.Text(f"❌ {msg}"),
                    bgcolor=ft.Colors.RED
                )
            page.overlay.append(snack_bar)
            snack_bar.open = True
            page.update()
        elif action == "change_ip":
            # تغيير عنوان IP وحفظه
            if new_ip and new_ip.strip():
                success_save, save_msg = await save_fingerprint_ip(new_ip.strip())
                if success_save:
                    # اختبار الاتصال بالعنوان الجديد
                    success_test, test_msg = await check_fingerprint_device()
                    if success_test:
                        snack_bar = ft.SnackBar(
                            ft.Text(f"✅ {save_msg} - {test_msg}"),
                            bgcolor=ft.Colors.GREEN
                        )
                    else:
                        snack_bar = ft.SnackBar(
                            ft.Text(f"✅ {save_msg} - ⚠️ {test_msg}"),
                            bgcolor=ft.Colors.ORANGE
                        )
                else:
                    snack_bar = ft.SnackBar(
                        ft.Text(f"❌ {save_msg}"),
                        bgcolor=ft.Colors.RED
                    )
                page.overlay.append(snack_bar)
                snack_bar.open = True
                page.update()
            else:
                snack_bar = ft.SnackBar(
                    ft.Text("❌ يرجى إدخال عنوان IP صحيح"),
                    bgcolor=ft.Colors.RED
                )
                page.overlay.append(snack_bar)
                snack_bar.open = True
                page.update()

    async def check_fingerprint_status(e):
        """فحص حالة جهاز البصمة"""
        success, msg = await check_fingerprint_device()
        if success:
            snack_bar = ft.SnackBar(
                ft.Text(f"✅ {msg}"),
                bgcolor=ft.Colors.GREEN
            )
        else:
            snack_bar = ft.SnackBar(
                ft.Text(f"❌ {msg}"),
                bgcolor=ft.Colors.RED
            )
        page.overlay.append(snack_bar)
        snack_bar.open = True
        page.update()

    fingerprint_device_button = ft.ElevatedButton(
        "🔐 إدارة جهاز البصمة", 
        icon=ft.Icons.FINGERPRINT, 
        on_click=lambda e: page.run_task(manage_fingerprint_device, e),
        bgcolor=ft.Colors.PURPLE_700, 
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    fingerprint_status_button = ft.ElevatedButton(
        "📊 حالة البصمة", 
        icon=ft.Icons.INFO, 
        on_click=lambda e: page.run_task(check_fingerprint_status, e),
        bgcolor=ft.Colors.CYAN_700, 
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

#------------------------------إدارة جهاز البصمة------------------
    async def save_fingerprint_ip(ip_address):
        """حفظ عنوان IP جهاز البصمة في ملف الإعدادات"""
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read('config.ini')
            
            if 'FINGERPRINT' not in config:
                config['FINGERPRINT'] = {}
            
            config['FINGERPRINT']['ip'] = ip_address
            config['FINGERPRINT']['port'] = '4370'
            
            with open('config.ini', 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            
            return True, "تم حفظ عنوان IP بنجاح"
        except Exception as e:
            return False, f"خطأ في حفظ الإعدادات: {str(e)}"

    async def load_fingerprint_ip():
        """تحميل عنوان IP جهاز البصمة من ملف الإعدادات"""
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read('config.ini')
            
            if 'FINGERPRINT' in config and 'ip' in config['FINGERPRINT']:
                return config['FINGERPRINT']['ip']
            else:
                return "192.168.1.201"  # العنوان الافتراضي
        except Exception as e:
            print(f"خطأ في تحميل إعدادات البصمة: {e}")
            return "192.168.1.201"  # العنوان الافتراضي

    async def restart_fingerprint_device():
        """إعادة تشغيل جهاز البصمة"""
        try:
            # تحميل عنوان IP المحفوظ
            ip = await load_fingerprint_ip()
            # محاولة إعادة الاتصال بالجهاز
            zk = ZK(ip, port=4370, timeout=5)
            conn = zk.connect()
            if conn:
                conn.disconnect()
                return True, "تم الاتصال بجهاز البصمة بنجاح"
            else:
                return False, "فشل الاتصال بجهاز البصمة"
        except Exception as e:
            return False, f"خطأ في الاتصال: {str(e)}"

    async def check_fingerprint_device():
        """فحص حالة جهاز البصمة"""
        try:
            # تحميل عنوان IP المحفوظ
            ip = await load_fingerprint_ip()
            zk = ZK(ip, port=4370, timeout=3)
            conn = zk.connect()
            if conn:
                conn.disconnect()
                return True, "جهاز البصمة متصل ويعمل"
            else:
                return False, "جهاز البصمة غير متصل"
        except Exception as e:
            return False, f"خطأ في الاتصال: {str(e)}"

    async def show_fingerprint_error_dialog():
        """عرض نافذة خطأ جهاز البصمة مع خيارات الحل"""
        action = None
        new_ip = None

        def on_retry(e):
            nonlocal action
            action = "retry"
            dialog.open = False
            page.update()

        def on_restart(e):
            nonlocal action
            action = "restart"
            dialog.open = False
            page.update()

        def on_change_ip(e):
            nonlocal action, new_ip
            action = "change_ip"
            new_ip = ip_input.value
            dialog.open = False
            page.update()

        def on_cancel(e):
            nonlocal action
            action = "cancel"
            dialog.open = False
            page.update()

        # فحص حالة الجهاز
        is_connected, status_msg = await check_fingerprint_device()
        
        # تحميل عنوان IP الحالي
        current_ip = await load_fingerprint_ip()

        # إضافة حقل إدخال عنوان IP
        ip_input = ft.TextField(
            label="عنوان IP جهاز البصمة",
            value=current_ip,
            width=200,
            border_color=ft.Colors.BLUE_400,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("🔐 مشكلة في جهاز البصمة", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Icon(ft.Icons.WARNING_AMBER, size=60, color=ft.Colors.RED_600),
                ft.Text(
                    "جهاز البصمة غير متصل أو غير متاح حالياً.",
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Container(
                    content=ft.Text(
                        f"الحالة: {status_msg}",
                        size=14,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=10,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=8,
                ),
                ft.Text(
                    "البصمة مطلوبة للأمان. يرجى التأكد من توصيل الجهاز.",
                    size=14,
                    color=ft.Colors.ORANGE_800,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Divider(),
                ft.Text(
                    "تغيير عنوان IP الجهاز:",
                    size=14,
                    weight=ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                ip_input,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.ElevatedButton("🔄 إعادة المحاولة", on_click=on_retry, bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE),
                ft.ElevatedButton("⚡ إعادة تشغيل الجهاز", on_click=on_restart, bgcolor=ft.Colors.ORANGE_600, color=ft.Colors.WHITE),
                ft.ElevatedButton("🌐 تغيير IP", on_click=on_change_ip, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                ft.ElevatedButton("❌ إلغاء", on_click=on_cancel, bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

        while dialog.open:
            await asyncio.sleep(0.1)

        return action, new_ip
#------------------------------الصفحة الرئيسية------------------
    # شريط الأدوات العلوي
    admin_toolbar = ft.Container(
        content=ft.Row([
            ft.ElevatedButton(
                'خروج', 
                icon=ft.Icons.CLOSE,
                bgcolor=ft.Colors.RED_700, 
                color=ft.Colors.WHITE,
                on_click=close_page,
                style=ft.ButtonStyle(
                    padding=ft.padding.symmetric(horizontal=20, vertical=10), 
                    shape=ft.RoundedRectangleBorder(radius=10)
                )
            ),
            fingerprint_device_button,
            fingerprint_status_button,
            restart_camera_button,
            camera_dropdown,
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER),
        padding=10,
        margin=ft.margin.only(top=10, bottom=10),
    )
    appbar = ft.Card(admin_toolbar)

    def home_page():
        return ft.Column(
            [
                appbar,
                # شريط علوي أنيق
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CAMERA_ALT, size=32, color=ft.Colors.BLUE_700),
                        ft.Text("نظام الحضور والانصراف", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                    padding=15,
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=15,
                    margin=ft.margin.only(top=0, bottom=10),
                ),
                # الكاميرا والمعاينة
                ft.Container(
                    content=ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("ضع وجهك أمام الكاميرا واضغط على الزر المناسب", size=16, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER),
                                image_preview,
                                ft.Row([
                                    check_in_button,
                                    check_out_button
                                ], alignment=ft.MainAxisAlignment.CENTER, spacing=30),
                            ],
                            spacing=18,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=20,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=15,
                        ),
                        elevation=8,
                        margin=ft.margin.symmetric(horizontal=0, vertical=0),
                    ),
                    margin=ft.margin.symmetric(horizontal=60, vertical=10),
                    border_radius=15,
                ),
            ],
            spacing=18,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    page.add(home_page())
    page.run_task(update_frame)

def main(page:ft.Page):
    page.title = "نظام الحضور والانصراف"

    page.clean()
    create_attendance_system(page)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
