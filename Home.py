import flet as ft
from flet import Icons, Colors
from dashboard_ui import DashboardPage
from logs_ui import LogsPage
from reports_ui import ReportsPage
from managers_page import EmployeeManagementPage
from add_user_page import AddUserPage
from settings import SettingsPage
from theme_manager import apply_theme_to_page, save_theme_config
from manual_attendance_page import ManualAttendancePage
from datetime import datetime
from zk import ZK  # إضافة الاستيراد
import threading
import time
from db import get_users

def create_home_page(page: ft.Page):
    # إعدادات النافذة
    page.window.maximized = True
    page.window.maximizable = True
    page.window.resizable = True
    page.title = "نظام إدارة الحضور الذكي"
    page.fonts = {"Cairo": "assets/fonts/Cairo-VariableFont_slnt,wght.ttf"}
    page.theme = ft.Theme(font_family="Cairo")
    
    # تطبيق إعدادات المظهر
    apply_theme_to_page(page)
    
    # تحديث لون الخلفية حسب الثيم
    page.bgcolor = ft.Colors.GREY_900 if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLUE_GREY_50

    # الثيمات المخصصة
    PRIMARY_COLOR = "#2C3E50"
    SECONDARY_COLOR = "#3498DB"
    ACCENT_COLOR = "#E74C3C"

    # ------- المتغير الوهمي لحالة البصمة -------
    def check_fingerprint_device():
        try:
            zk = ZK("192.168.1.201", port=4370, timeout=2)
            conn = zk.connect()
            if conn:
                conn.disconnect()
                return True
        except Exception:
            pass
        return False

    fingerprint_connected = check_fingerprint_device()  # تحقق فعلي عند بدء الصفحة
    
    # ------- عنصر الإشعار -------
    fingerprint_status = ft.Container(
        width=16,
        height=16,
        border_radius=8,
        bgcolor=Colors.GREEN if fingerprint_connected else Colors.RED,
        tooltip="جهاز البصمة متصل" if fingerprint_connected else "جهاز البصمة غير متصل",
    )

    def update_fingerprint_status(connected):
        nonlocal fingerprint_connected
        fingerprint_connected = connected
        fingerprint_status.bgcolor = Colors.GREEN if connected else Colors.RED
        fingerprint_status.tooltip = "جهاز البصمة متصل" if connected else "جهاز البصمة غير متصل"
        # إشعار عند تغير الحالة
        msg = "تم الاتصال بجهاز البصمة" if connected else "تم فقد الاتصال بجهاز البصمة"
        color = ft.colors.GREEN if connected else ft.colors.RED
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color, duration=2000)
        page.snack_bar.open = True
        page.update()

    def monitor_fingerprint():
        while True:
            connected = check_fingerprint_device()
            if connected != fingerprint_connected:
                update_fingerprint_status(connected)
            time.sleep(3)  # تحقق كل 3 ثوانٍ

    threading.Thread(target=monitor_fingerprint, daemon=True).start()

    # ------- الدوال المساعدة -------
    def toggle_theme(e):
        # تبديل بين الثيمات وحفظ الإعداد
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = ft.Colors.GREY_900
            save_theme_config('dark')
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = ft.Colors.BLUE_GREY_50
            save_theme_config('light')
        
        apply_theme_to_page(page)
        page.update()

    # ------- تصحيح NavigationDrawer -------
    username = page.session.get("username")
    # جلب الوظائف المسموح بها للمستخدم الحالي
    user_functions = []
    users = get_users()
    for u in users:
        if u[1] == username:
            if u[-1]:
                user_functions = u[-1].split(",")
            break
    # تعريف جميع الوظائف الممكنة مع خصائصها
    all_functions = [
        {"key": "dashboard", "label": "الرئيسية", "icon": ft.Icons.HOME, "selected_icon": ft.Icons.HOME_OUTLINED},
        {"key": "attendance", "label": "الحضور اليدوي", "icon": ft.Icons.FACT_CHECK, "selected_icon": ft.Icons.FACT_CHECK_OUTLINED},
        {"key": "reports", "label": "التقارير", "icon": ft.Icons.REPORT, "selected_icon": ft.Icons.REPORT_OUTLINED},
        {"key": "logs", "label": "السجلات", "icon": ft.Icons.LOCAL_ACTIVITY, "selected_icon": ft.Icons.LOCAL_ACTIVITY_OUTLINED},
        {"key": "management", "label": "الإدارة", "icon": ft.Icons.MANAGE_ACCOUNTS, "selected_icon": ft.Icons.MANAGE_ACCOUNTS_OUTLINED},
        {"key": "add_user", "label": "إضافة مستخدم", "icon": ft.Icons.PERSON_ADD, "selected_icon": ft.Icons.PERSON_ADD_ALT_1},
        {"key": "settings", "label": "الاعدادات", "icon": ft.Icons.SETTINGS, "selected_icon": ft.Icons.SETTINGS_OUTLINED},
    ]
    # بناء قائمة العناصر حسب الوظائف المسموح بها
    nav_items = [
        ft.NavigationDrawerDestination(
            label=f["label"],
            icon=f["icon"],
            selected_icon=f["selected_icon"]
        ) for f in all_functions if f["key"] in user_functions
    ]
    drawer = ft.NavigationDrawer(
        bgcolor=ft.Colors.GREY_800 if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.PRIMARY_CONTAINER,
        indicator_color=ft.Colors.WHITE,
        controls=[
            ft.Card(
                content=ft.Image(src="assets/logo.png",fit=ft.ImageFit.COVER)
            ),
            *nav_items
        ],
        elevation=100,
        on_change=lambda e: switch_view(e.control.selected_index)
    )

    # ------- العناصر الديناميكية -------
    current_theme = "light"

    # دالة للحصول على أحجام متجاوبة بناءً على حجم النافذة
    def get_responsive_sizes():
        window_width = page.window.width or 1200
        window_height = page.window.height or 700
        
        # تحديد الأحجام بناءً على عرض النافذة
        if window_width < 900:  # شاشات صغيرة
            return {
                'nav_height': 50,
                'nav_padding': 15,
                'title_size': 16,
                'date_size': 12,
                'icon_size': 20,
                'logo_size': 30,
                'drawer_width': 250
            }
        elif window_width < 1200:  # شاشات متوسطة
            return {
                'nav_height': 55,
                'nav_padding': 20,
                'title_size': 18,
                'date_size': 13,
                'icon_size': 24,
                'logo_size': 35,
                'drawer_width': 280
            }
        else:  # شاشات كبيرة
            return {
                'nav_height': 60,
                'nav_padding': 25,
                'title_size': 22,
                'date_size': 14,
                'icon_size': 28,
                'logo_size': 40,
                'drawer_width': 300
            }

    # ------- شريط التنقل العلوي -------
    sizes = get_responsive_sizes()
    
    date_display = ft.Text(
        datetime.now().strftime("%Y/%m/%d - %A"),
        size=sizes['date_size'],
        color=ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.WHITE,
        weight=ft.FontWeight.W_500
    )

    def close_page(e):
        # عرض نافذة تأكيد تسجيل الخروج
        def confirm_logout(e):
            # إغلاق نافذة التأكيد
            page.overlay.remove(confirm_dialog)
            page.clean()
            
            # العودة إلى صفحة تسجيل الدخول
            logout_to_login()
            page.update()
        
        def cancel_logout(e):
            # إغلاق نافذة التأكيد فقط
            page.overlay.remove(confirm_dialog)
            page.update()
        
        # إنشاء نافذة التأكيد
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("تأكيد تسجيل الخروج", text_align=ft.TextAlign.CENTER),
            content=ft.Text("هل أنت متأكد من أنك تريد تسجيل الخروج من النظام؟", text_align=ft.TextAlign.CENTER),
            actions=[
                ft.TextButton("إلغاء", on_click=cancel_logout),
                ft.TextButton("تأكيد", on_click=confirm_logout),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        page.update()
    
    def logout_to_login():
        """العودة إلى صفحة تسجيل الدخول"""
        # مسح بيانات الجلسة
        page.session.clear()
        # مسح جميع العناصر من الصفحة
        page.clean()
        # إعادة تشغيل صفحة تسجيل الدخول
        from login_page import main as login_main
        login_main(page)
        page.update()

    nav_bar = ft.Container(
        height=sizes['nav_height'],
        padding=ft.padding.symmetric(horizontal=sizes['nav_padding']),
        bgcolor=ft.Colors.GREY_800 if page.theme_mode == ft.ThemeMode.DARK else PRIMARY_COLOR,
        content=ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.MENU,
                    icon_color=ft.Colors.WHITE,
                    on_click=lambda e: page.open(drawer),
                ),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.FINGERPRINT, color=ft.Colors.WHITE, size=sizes['icon_size']),
                        ft.Text("نظام إدارة الحضور الذكي", 
                               size=sizes['title_size'], 
                               color=ft.Colors.WHITE, 
                               weight=ft.FontWeight.BOLD),
                        ft.Icon(ft.Icons.FACT_CHECK, color=ft.Colors.WHITE, size=sizes['icon_size']),
                    ],
                    spacing=10,
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Row([
                    date_display,
                    ft.Row([  # زر الاعدادت + مؤشر البصمة
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS, 
                            icon_color=ft.Colors.WHITE,
                            tooltip="الاعدادت",
                            on_click=lambda e: switch_view(get_function_index("settings"))
                        ),
                        fingerprint_status
                    ]),
                    ft.IconButton(
                        icon=ft.Icons.DARK_MODE,
                        icon_color=ft.Colors.WHITE,
                        on_click=lambda e: toggle_theme(e),
                        tooltip="تبديل الثيم"
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        icon_color=ft.Colors.WHITE,
                        tooltip="خروج من النظام",
                        on_click=close_page,
                    ),
                ], spacing=10),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        border_radius=20
    )

    theme_btn = ft.IconButton(
        icon=ft.Icons.DARK_MODE,
        icon_color=ft.Colors.WHITE,
        on_click=lambda e: toggle_theme(e),
        tooltip="تبديل الثيم"
    )

    # ------- نظام التبويبات -------
    view_container = ft.Container(expand=True)

    def get_function_index(function_key):
        """الحصول على مؤشر الوظيفة من قائمة الوظائف المتاحة"""
        available_functions = [f["key"] for f in all_functions if f["key"] in user_functions]
        try:
            return available_functions.index(function_key)
        except ValueError:
            return -1

    def switch_view(index):
        # ربط كل وظيفة بالصفحة المناسبة حسب ترتيب nav_items
        if not nav_items:
            return
        
        # التحقق من صحة المؤشر
        if index < 0 or index >= len(nav_items):
            print(f"Warning: Invalid index {index} for nav_items with length {len(nav_items)}")
            return
            
        # الحصول على المفتاح من الوظائف المسموح بها
        available_functions = [f["key"] for f in all_functions if f["key"] in user_functions]
        if index >= len(available_functions):
            print(f"Warning: Index {index} out of range for available_functions with length {len(available_functions)}")
            return
            
        key = available_functions[index]
        
        if key == "dashboard":
            view_container.content = DashboardPage(page)
        elif key == "attendance":
            view_container.content = ManualAttendancePage(page)
        elif key == "reports":
            view_container.content = ReportsPage(page)
        elif key == "logs":
            view_container.content = LogsPage(page)
        elif key == "management":
            view_container.content = EmployeeManagementPage(page)
        elif key == "add_user":
            view_container.content = AddUserPage(page)
        elif key == "settings":
            view_container.content = SettingsPage(page)
        page.update()

    # ------- إضافة Scaffold -------
    scaffold = ft.Column(
        controls=[
            nav_bar,
            ft.Card(
                elevation=100,
                content=ft.Container(
                    padding=ft.padding.symmetric(horizontal=sizes['nav_padding'], vertical=15),
                    content=view_container,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=[ft.Colors.BLUE_200, ft.Colors.BLUE_400],
                    ),
                    border_radius=20,
                    expand=True,
                ),
            )
        ],
        expand=True,
        spacing=0,
        scroll=ft.ScrollMode.ALWAYS
    )
    page.add(scaffold)
    # الخيار الافتراضي: إذا يوجد dashboard اجعله أولاً، إذا لا يوجد والتقارير موجودة اجعلها أولاً
    default_index = 0
    if "dashboard" in user_functions:
        default_index = get_function_index("dashboard")
    elif "reports" in user_functions:
        default_index = get_function_index("reports")
    
    if default_index >= 0:
        drawer.selected_index = default_index
        switch_view(default_index)
    else:
        # إذا لم توجد وظائف متاحة، اعرض رسالة خطأ
        print("Warning: No available functions for user")

# لا تستدعي ft.app هنا، فقط صدّر 
# ft.app(target=create_home_page)