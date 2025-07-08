import flet as ft
from db import get_logs, get_employee_names, delete_all_logs, get_users, log_action  # استيراد دالة حذف السجلات
from datetime import datetime

class LogsPage(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page = page
        
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20

        # الحصول على السجلات من قاعدة البيانات
        logs = get_logs()

        # دمج أسماء الموظفين مع أسماء المستخدمين
        employee_names = get_employee_names()
        user_names = [u[1] for u in get_users()]
        all_names = list(sorted(set(employee_names + user_names)))
        filter_employee_name = ft.Dropdown(
            options=[ft.dropdown.Option(emp) for emp in all_names],
            label="تصفية حسب اسم الموظف",
            hint_text="اختر الموظف",
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
        )
        # DatePicker في overlay
        self.date_picker = ft.DatePicker(
            first_date=datetime(2023, 1, 1),
            last_date=datetime.now(),
            help_text="اختر تاريخًا",
        )
        self.page.overlay.append(self.date_picker)

        # متغير لتتبع الحقل النشط
        self.active_date_field = None

        def on_date_selected(e):
            if self.date_picker.value:
                selected_date = self.date_picker.value.strftime('%Y-%m-%d')
                if self.active_date_field == 'start':
                    start_date_input.value = selected_date
                elif self.active_date_field == 'end':
                    end_date_input.value = selected_date
                self.page.update()
        self.date_picker.on_change = on_date_selected

        def open_date_picker(field):
            self.active_date_field = field
            current_field = start_date_input if field == "start" else end_date_input
            if current_field.value:
                try:
                    self.date_picker.value = datetime.strptime(current_field.value, "%Y-%m-%d")
                except Exception:
                    self.date_picker.value = datetime.now()
            else:
                self.date_picker.value = datetime.now()
            self.page.open(self.date_picker)

        start_date_input = ft.TextField(
            label="من تاريخ",
            width=150,
            border_radius=10,
            read_only=True,
            suffix_icon=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                tooltip="اختر من تاريخ",
                on_click=lambda _: open_date_picker("start"),
            ),
        )
        end_date_input = ft.TextField(
            label="إلى تاريخ",
            width=150,
            border_radius=10,
            read_only=True,
            suffix_icon=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                tooltip="اختر إلى تاريخ",
                on_click=lambda _: open_date_picker("end"),
            ),
        )

        # جدول عرض السجلات
        logs_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("اسم الموظف", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)),
                ft.DataColumn(ft.Text("الإجراء", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)),
                ft.DataColumn(ft.Text("التاريخ والوقت", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)),
            ],
            rows=[],
            data_row_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.BLACK),
            column_spacing=50,
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_300),
            vertical_lines=ft.BorderSide(1, ft.Colors.GREY_300),
            heading_row_color=ft.Colors.BLUE_100,
        )

        # إضافة الجدول إلى ListView لتمكين التمرير
        scrollable_table = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            auto_scroll=False,
            controls=[logs_table],
        )

        # دالة لعرض السجلات وتحديث البيانات المصفاة
        def display_and_filter_logs():
            start_date = start_date_input.value
            end_date = end_date_input.value
            # التحقق من صحة التواريخ
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
            except ValueError:
                show_snack_bar(self.page, "تاريخ غير صحيح!", ft.Colors.RED)
                return

            # تطبيق التصفية
            filtered_logs = []
            for log in logs:
                log_timestamp = log[3].date()  # التاريخ في السجل
                employee_name, action, timestamp = log[1], log[2], str(log[3])
                if start_date and log_timestamp < start_date:
                    continue
                if end_date and log_timestamp > end_date:
                    continue
                if filter_employee_name.value and filter_employee_name.value != employee_name:
                    continue
                filtered_logs.append((employee_name, action, timestamp))

            # عرض السجلات
            if not filtered_logs:
                show_snack_bar(self.page, "لا توجد سجلات تطابق معايير التصفية!", ft.Colors.RED)
                return

            logs_table.rows.clear()
            for log in filtered_logs:
                employee_name, action, timestamp = log
                logs_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(employee_name, color=ft.Colors.BLACK)),
                            ft.DataCell(ft.Text(action, color=ft.Colors.BLACK)),
                            ft.DataCell(ft.Text(timestamp, color=ft.Colors.BLACK)),
                        ]
                    )
                )
            self.page.update()

        # دالة حذف جميع السجلات
        def delete_all_logs_click(e):
            def close_dlg(e):
                confirm_dialog.open = False  # إغلاق النافذة عند الضغط على "لا"
                self.page.update()

            def delete_and_close(e):
                try:
                    delete_all_logs()  # استدعاء دالة حذف السجلات من قاعدة البيانات
                    logs_table.rows.clear()  # مسح الجدول
                    # --- تسجيل الحدث باسم المستخدم الحالي ---
                    current_username = self.page.session.get("username")
                    users = get_users()
                    user_id = None
                    for u in users:
                        if u[1] == current_username:
                            user_id = u[0]
                            break
                    if user_id:
                        log_action(user_id=user_id, action=f"حذف جميع السجلات بواسطة {current_username}")
                    show_snack_bar(self.page, "تم حذف جميع السجلات بنجاح!", ft.Colors.GREEN)
                except Exception as ex:
                    show_snack_bar(self.page, f"حدث خطأ أثناء حذف السجلات: {str(ex)}", ft.Colors.RED)
                finally:
                    confirm_dialog.open = False  # إغلاق النافذة بعد الحذف
                    self.page.update()

            # نافذة تأكيد الحذف
            confirm_dialog = ft.AlertDialog(
                title=ft.Text("تأكيد الحذف"),
                content=ft.Text("هل أنت متأكد من رغبتك في حذف جميع السجلات؟"),
                actions=[
                    ft.TextButton("نعم", on_click=delete_and_close),
                    ft.TextButton("لا", on_click=close_dlg),
                ],
                modal=True,
            )
            page.dialog = confirm_dialog
            confirm_dialog.open = True
            page.update()

        # دالة لعرض رسائل SnackBar
        def show_snack_bar(page, message, color):
            snack_bar = ft.SnackBar(
                ft.Text(message),
                bgcolor=color,
                duration=3000,
            )
            page.snack_bar = snack_bar
            snack_bar.open = True
            page.update()
    
        # زر عرض السجلات
        show_logs_button = ft.ElevatedButton(
            "عرض السجلات",
            icon=ft.Icons.VISIBILITY,
            on_click=lambda e: display_and_filter_logs(),
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        )

        # زر حذف جميع السجلات
        delete_all_logs_button = ft.ElevatedButton(
            "حذف جميع السجلات",
            icon=ft.Icons.DELETE_FOREVER,
            on_click=delete_all_logs_click,
            bgcolor=ft.Colors.RED_700,
            color=ft.Colors.WHITE,
        )

        # إضافة العناصر إلى الصفحة
        self.controls = [
            ft.Text("سجلات النظام", size=25, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
            ft.Row([filter_employee_name,start_date_input, end_date_input], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Row([show_logs_button, delete_all_logs_button], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Container(
                height=400,  # ارتفاع ثابت للجدول مع شريط التمرير
                border=ft.border.all(1, ft.Colors.YELLOW),
                border_radius=10,
                content=scrollable_table,
            ),
        ]

# تشغيل التطبيق
# def main(page: ft.Page):
#     page.title = "سجلات النظام"
#     page.vertical_alignment = ft.MainAxisAlignment.CENTER
#     page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
#     page.scroll = ft.ScrollMode.AUTO
#     page.padding = 20
#     page.theme_mode = ft.ThemeMode.LIGHT
#     page.bgcolor = ft.Colors.BLUE_GREY_50

#     # إضافة الصفحة الرئيسية
#     page.add(LogsPage(page))

# ft.app(target=main)