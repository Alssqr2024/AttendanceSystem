import flet as ft
from db import get_attendance_records, get_employee_names, get_departments, log_action, get_users
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import arabic_reshaper
from bidi.algorithm import get_display
import os
import configparser

class ReportsPage(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20

        # تسجيل حدث فتح الواجهة
        # log_action(employee_id=None, action="فتح واجهة التقارير")

        # إنشاء تدرج لوني للخلفية
        gradient_container = ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=["#BBDEFB", "#64B5F6"],  # BLUE_100, BLUE_300
            ),
            height=80,
            content=ft.Text(
                "تقارير الحضور والانصراف",
                size=24,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
                color="#0D47A1",  # BLUE_900
            ),
            alignment=ft.alignment.center,
        )

        employee_names = get_employee_names()
        departments = get_departments()

        # عناصر التصفية
        self.filter_date_type = ft.Dropdown(
            label="نوع التاريخ",
            hint_text="اختر نوع التاريخ",
            tooltip="اختر نوع التاريخ للفلترة (اليوم، الشهر، السنة)",
            options=[
                ft.dropdown.Option("اليوم"),
                ft.dropdown.Option("الشهر"),
                ft.dropdown.Option("السنة"),
            ],
            width=150,
            bgcolor="#FFFFFF",  # WHITE
            border_radius=10,
        )

        self.filter_department = ft.Dropdown(
            label="القسم",
            hint_text="اختر القسم",
            tooltip="اختر قسم الموظف للفلترة",
            options=[ft.dropdown.Option(dept) for dept in departments],
            width=150,
            bgcolor="#FFFFFF",  # WHITE
            border_radius=10,
        )

        self.filter_employee_name = ft.Dropdown(
            label="اسم الموظف",
            hint_text="اختر الموظف",
            tooltip="اختر اسم الموظف المحدد للفلترة",
            options=[ft.dropdown.Option(name) for name in employee_names],
            width=150,
            bgcolor="#FFFFFF",  # WHITE
            border_radius=10,
        )

        # DatePicker في overlay
        self.date_picker = ft.DatePicker(
            first_date=datetime(2023, 1, 1),
            last_date=datetime.now(),
            help_text="اختر تاريخًا",
        )
        self.page.overlay.append(self.date_picker)

        def on_date_selected(e):
            if self.date_picker.value:
                selected_date = self.date_picker.value.strftime('%Y-%m-%d')
                if self.active_date_field == 'start':
                    self.start_date_input.value = selected_date
                elif self.active_date_field == 'end':
                    self.end_date_input.value = selected_date
                self.page.update()
        self.date_picker.on_change = on_date_selected

        # حقول التاريخ مع suffix_icon بدلاً من prefix_icon
        self.start_date_input = ft.TextField(
            label="من تاريخ",
            hint_text="اختر تاريخ البدء",
            tooltip="اختر تاريخ بداية الفترة المطلوبة",
            width=180,
            bgcolor="#FFFFFF",  # WHITE
            border_radius=10,
            read_only=True,
            text_align=ft.TextAlign.RIGHT,
            suffix_icon=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                tooltip="اختر من تاريخ",
                on_click=lambda _: self.open_date_picker("start"),
            ),
        )
        self.end_date_input = ft.TextField(
            label="إلى تاريخ",
            hint_text="اختر تاريخ الانتهاء",
            tooltip="اختر تاريخ نهاية الفترة المطلوبة",
            width=180,
            bgcolor="#FFFFFF",  # WHITE
            border_radius=10,
            read_only=True,
            text_align=ft.TextAlign.RIGHT,
            suffix_icon=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                tooltip="اختر إلى تاريخ",
                on_click=lambda _: self.open_date_picker("end"),
            ),
        )

        # متغير لتتبع الحقل النشط
        self.active_date_field = None

        # جدول التقارير
        self.report_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("اسم الموظف", weight=ft.FontWeight.BOLD, color="#000000")),
                ft.DataColumn(ft.Text("القسم", weight=ft.FontWeight.BOLD, color="#000000")),
                ft.DataColumn(ft.Text("وقت الحضور", weight=ft.FontWeight.BOLD, color="#000000")),
                ft.DataColumn(ft.Text("وقت الانصراف", weight=ft.FontWeight.BOLD, color="#000000")),
                ft.DataColumn(ft.Text("الوقت المستغرق", weight=ft.FontWeight.BOLD, color="#000000")),
            ],
            rows=[],
            bgcolor="#FFFFFF",  # WHITE
            border_radius=10,
            border=ft.border.all(1, "#000000"),  # BLACK
            column_spacing=50,
            horizontal_lines=ft.BorderSide(1, "#E0E0E0"),  # GREY_300
            vertical_lines=ft.BorderSide(1, "#E0E0E0"),  # GREY_300
            heading_row_color="#BBDEFB",  # BLUE_100
        )

        # جدول التقارير مع تمرير منفصل
        scrollable_table = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            auto_scroll=False,
            controls=[self.report_table],
        )

        # قائمة تصدير التقرير
        self.export_format_dropdown = ft.Dropdown(
            label="صيغة التصدير",
            hint_text="اختر الصيغة",
            tooltip="اختر صيغة ملف التصدير (CSV أو PDF)",
            options=[
                ft.dropdown.Option("CSV"),
                ft.dropdown.Option("PDF"),
            ],
            value="CSV",
            width=180,
            bgcolor="#FFFFFF",  # WHITE
            border_radius=10,
        )

        # دالة تصدير التقارير إلى PDF
        def export_to_pdf(records, file_path):
            # تسجيل الخط العربي من الإعدادات
            font_path = 'assets/fonts/Amiri-Italic.ttf'
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
                font_name = 'ArabicFont'
            else:
                # Fallback font if the specified one doesn't exist
                pdfmetrics.registerFont(TTFont('ArabicFont', 'assets/fonts/Amiri-Italic.ttf'))
                font_name = 'ArabicFont'

            # إنشاء المستند
            doc = SimpleDocTemplate(file_path, pagesize=letter)

            # إعداد البيانات للجدول
            data = [["Employee Name", "Department", "Check-In Time", "Check-Out Time", "Duration"]]
            for record in records:
                # Correctly unpack record data
                employee_name, department, check_in_time, check_out_time, duration_obj = (
                    record[1], record[2], str(record[4] or ''), str(record[5] or ''), record[7]
                )

                # Format duration to HH:MM
                if duration_obj:
                    total_seconds = int(duration_obj.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    duration_str = f"{hours:02d}:{minutes:02d}"
                else:
                    duration_str = "N/A"

                # معالجة النصوص العربية
                reshaped_employee_name = arabic_reshaper.reshape(employee_name)
                reshaped_department = arabic_reshaper.reshape(department)
                bidi_employee_name = get_display(reshaped_employee_name)
                bidi_department = get_display(reshaped_department)

                # إضافة السجلات إلى البيانات
                data.append([bidi_employee_name, bidi_department, check_in_time, check_out_time, duration_str])

            # إنشاء الجدول
            table = Table(data)

            # تخصيص نمط الجدول
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),  # المحاذاة إلى اليمين للنصوص العربية
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # خط العناوين بالإنجليزية
                ('FONTNAME', (0, 1), (-1, -1), font_name),  # Use the registered font
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            table.setStyle(style)

            # بناء المستند
            elements = [table]
            doc.build(elements)

        # قائمة البيانات المصفاة
        self.filtered_data = []

        def get_current_user_id():
            current_username = self.page.session.get("username")
            users = get_users()
            user_id = None
            for u in users:
                if u[1] == current_username:
                    user_id = u[0]
                    break
            return user_id

        # دالة لعرض التقارير وفقًا لمعايير التصفية
        def display_and_filter_reports():
            start_date = self.start_date_input.value
            end_date = self.end_date_input.value
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
            except ValueError:
                log_action(user_id=get_current_user_id(), action="تاريخ غير صحيح في الفلتر")
                show_snack_bar(self.page, "تاريخ غير صحيح!", "#F44336")  # RED
                return

            records = get_attendance_records()
            self.filtered_data = []
            for record in records:
                date = record[6]  # تاريخ الحضور
                
                # فحص أن التاريخ ليس None
                if date is None:
                    continue
                
                if self.filter_date_type.value == "اليوم" and date != datetime.now().date():
                    continue
                if self.filter_date_type.value == "الشهر" and date.month != datetime.now().month:
                    continue
                if self.filter_date_type.value == "السنة" and date.year != datetime.now().year:
                    continue
                if start_date and date < start_date:
                    continue
                if end_date and date > end_date:
                    continue
                if self.filter_department.value and self.filter_department.value != record[2]:
                    continue
                if self.filter_employee_name.value and self.filter_employee_name.value != record[1]:
                    continue
                self.filtered_data.append(record)

            # تسجيل حدث مع تفاصيل الفلتر
            filter_details = []
            if self.filter_date_type.value:
                filter_details.append(f"نوع التاريخ: {self.filter_date_type.value}")
            if self.filter_department.value:
                filter_details.append(f"القسم: {self.filter_department.value}")
            if self.filter_employee_name.value:
                filter_details.append(f"الموظف: {self.filter_employee_name.value}")
            if self.start_date_input.value:
                filter_details.append(f"من: {self.start_date_input.value}")
            if self.end_date_input.value:
                filter_details.append(f"إلى: {self.end_date_input.value}")

            log_action(
                user_id=get_current_user_id(),
                action=f"عرض تقارير الحضور مع الفلترات: {', '.join(filter_details)}"
            )

            if not self.filtered_data:
                log_action(user_id=get_current_user_id(), action="لا توجد بيانات مطابقة للفلتر")
                show_snack_bar(self.page, "لا توجد بيانات تطابق معايير التصفية!", "#F44336")  # RED
                return

            self.report_table.rows.clear()
            for record in self.filtered_data:
                duration = record[7]
                if duration:
                    total_seconds = int(duration.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    duration_str = f"{hours:02d}:{minutes:02d}"
                else:
                    duration_str = "--:--"

                self.report_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(record[1], color="#000000")),
                            ft.DataCell(ft.Text(record[2], color="#000000")),
                            ft.DataCell(ft.Text(str(record[4] or ''), color="#000000")),
                            ft.DataCell(ft.Text(str(record[5] or ''), color="#000000")),
                            ft.DataCell(ft.Text(duration_str, color="#000000")),
                        ]
                    )
                )
            self.page.update()

        # دالة تصدير البيانات
        def export_report(e):
            if not self.filtered_data:
                log_action(user_id=get_current_user_id(), action="محاولة تصدير بدون بيانات")
                show_snack_bar(self.page, "لا توجد بيانات مصفاة للتصدير!", "#F44336")  # RED
                return

            log_action(user_id=get_current_user_id(), action=f"بدء تصدير {self.export_format_dropdown.value}")
            folder_picker.get_directory_path()

        # دالة اختيار المجلد
        folder_picker = ft.FilePicker()
        self.page.overlay.append(folder_picker)
        self.page.update()

        def on_folder_selected(e):
            if not e.path:
                log_action(user_id=get_current_user_id(), action="محاولة تصدير بدون اختيار مجلد")
                show_snack_bar(self.page, "لم يتم اختيار مجلد!", "#F44336")  # RED
                return

            file_extension = self.export_format_dropdown.value.lower()
            file_name = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
            file_path = os.path.join(e.path, file_name)

            try:
                if self.export_format_dropdown.value == "CSV":
                    df = pd.DataFrame(
                        self.filtered_data,
                        columns=["EmployeeID", "EmployeeName", "Department", "CheckInTime", "CheckOutTime", "Date", "Duration"],
                    )
                    df.to_csv(file_path, index=False, encoding="utf-8-sig")
                    log_action(user_id=get_current_user_id(), action=f"تم تصدير CSV: {file_name}")
                    self.show_success_message(f"تم التصدير بنجاح: {file_name}")
                elif self.export_format_dropdown.value == "PDF":
                    export_to_pdf(self.filtered_data, file_path)
                    log_action(user_id=get_current_user_id(), action=f"تم تصدير PDF: {file_name}")
                    self.show_success_message(f"تم التصدير بنجاح: {file_name}")
            except Exception as ex:
                log_action(user_id=get_current_user_id(), action=f"فشل التصدير: {str(ex)[:100]}")
                show_snack_bar(self.page, f"خطأ في التصدير: {str(ex)}", "#F44336")  # RED

        folder_picker.on_result = on_folder_selected

        # دالة عرض رسالة SnackBar
        def show_snack_bar(page, message, color):
            snack_bar = ft.SnackBar(
                ft.Text(message,text_align='center',weight=ft.FontWeight.BOLD),
                bgcolor=color,
                duration=3000,
                show_close_icon=True,
                
            )
            page.snack_bar = snack_bar
            snack_bar.open = True
            page.update()

        # أيقونة إلغاء التصفية
        clear_filters_icon = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="إلغاء التصفية",
            on_click=lambda e: self.clear_all_filters(),
            icon_color="#1976D2",  # BLUE_700
        )

        # زر عرض التقارير
        show_reports_button = ft.ElevatedButton(
            "عرض التقارير",
            icon=ft.Icons.VISIBILITY,
            tooltip="عرض التقارير حسب الفلاتر المحددة",
            on_click=lambda e: (
                display_and_filter_reports(),
            ),
            bgcolor="#1976D2",  # BLUE_700
            color="#FFFFFF",  # WHITE
            style=ft.ButtonStyle(
                padding=ft.padding.all(15),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            animate_opacity=300,
        )

        # زر تصدير التقرير
        export_reports_button = ft.ElevatedButton(
            "تصدير التقرير",
            icon=ft.Icons.DOWNLOAD,
            tooltip="تصدير التقرير إلى ملف (CSV أو PDF)",
            on_click=lambda e: (
                log_action(employee_id=None, action="النقر على زر التصدير"),
                export_report(e),
            ),
            bgcolor="#388E3C",  # GREEN_700
            color="#FFFFFF",  # WHITE
            style=ft.ButtonStyle(
                padding=ft.padding.all(15),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            animate_scale=ft.Animation(300, ft.AnimationCurve.BOUNCE_OUT),
        )

        # زر حذف جميع السجلات
        delete_all_records_button = ft.ElevatedButton(
            "حذف جميع السجلات",
            icon=ft.Icons.DELETE_FOREVER,
            tooltip="حذف جميع سجلات الحضور والانصراف (إجراء لا يمكن التراجع عنه)",
            on_click=lambda e: self.show_delete_confirmation(),
            bgcolor="#B71C1C",  # RED_800
            color="#FFFFFF",  # WHITE
            style=ft.ButtonStyle(
                padding=ft.padding.all(15),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )

        # تخطيط الصفحة
        self.controls = [
            gradient_container,
            ft.Column(
                [
                    # صف الفلاتر الأساسية
                    ft.Container(
                        content=ft.Row([
                            self.filter_date_type,
                            self.filter_department,
                            self.filter_employee_name,
                            self.start_date_input,
                            self.end_date_input,
                            clear_filters_icon,
                        ],
                        vertical_alignment=ft.MainAxisAlignment.CENTER,
                        alignment="center",
                        spacing=15),
                        padding=ft.padding.all(20),
                        bgcolor="#FFFFFF",  # WHITE
                        border_radius=15,
                        border=ft.border.all(1, "#EEEEEE"),  # GREY_200
                    ),
                    
                    # صف الأزرار
                    ft.Container(
                        content=ft.Row([
                            show_reports_button,
                            self.export_format_dropdown,
                            export_reports_button,
                            delete_all_records_button,
                        ],
                        vertical_alignment=ft.MainAxisAlignment.CENTER,
                        alignment="center",
                        spacing=20),
                        padding=ft.padding.all(20),
                        bgcolor="#FFFFFF",  # WHITE
                        border_radius=15,
                        border=ft.border.all(1, "#EEEEEE"),  # GREY_200
                    ),
                    
                    # جدول التقارير مع تمرير منفصل
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "نتائج البحث",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color="#0D47A1",  # BLUE_900
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(
                                height=400,
                                content=scrollable_table,
                                border=ft.border.all(1, "#E0E0E0"),  # GREY_300
                                border_radius=10,
                            ),
                        ]),
                        padding=ft.padding.all(20),
                        bgcolor="#FFFFFF",  # WHITE
                        border_radius=15,
                        border=ft.border.all(1, "#EEEEEE"),  # GREY_200
                        expand=True,
                    ),
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
        ]

    def open_date_picker(self, field: str):
        self.active_date_field = field
        current_field = self.start_date_input if field == "start" else self.end_date_input
        if current_field.value:
            try:
                self.date_picker.value = datetime.strptime(current_field.value, "%Y-%m-%d")
            except Exception:
                self.date_picker.value = datetime.now()
        else:
            self.date_picker.value = datetime.now()
        self.page.open(self.date_picker)

    def clear_all_filters(self):
        self.filter_date_type.value = None
        self.filter_department.value = None
        self.filter_employee_name.value = None
        self.start_date_input.value = ""
        self.end_date_input.value = ""
        self.page.update()

    def show_delete_confirmation(self):
        """عرض نافذة تأكيد حذف جميع السجلات"""
        def confirm_delete(e):
            self.delete_all_records()
            dialog.open = False
            self.page.update()

        def cancel_delete(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ تأكيد الحذف", color="#B71C1C", weight=ft.FontWeight.BOLD),  # RED_800
            content=ft.Text(
                "هل أنت متأكد من حذف جميع سجلات الحضور والانصراف؟\n\n"
                "⚠️ هذا الإجراء لا يمكن التراجع عنه!",
                size=16,
                color="#D32F2F",  # RED_700
            ),
            actions=[
                ft.TextButton("إلغاء", on_click=cancel_delete),
                ft.TextButton(
                    "حذف جميع السجلات",
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(color="#B71C1C"),  # RED_800
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def delete_all_records(self):
        """حذف جميع سجلات الحضور والانصراف من قاعدة البيانات"""
        try:
            from db import delete_all_attendance_records, log_action, get_users
            
            # حذف جميع السجلات
            success = delete_all_attendance_records()
            
            if success:
                # تسجيل الحدث
                current_username = self.page.session.get("username")
                users = get_users()
                user_id = None
                for u in users:
                    if u[1] == current_username:
                        user_id = u[0]
                        break
                
                log_action(user_id=user_id, action=f"حذف المستخدم {current_username} جميع سجلات الحضور والانصراف")
                
                # عرض رسالة نجاح
                self.show_success_message("تم حذف جميع السجلات بنجاح")
                
                # إعادة تعيين الحقول
                self.clear_all_filters()
                
                # مسح الجدول
                self.report_table.rows.clear()
                self.filtered_data = []
                self.page.update()
            else:
                self.show_error_message("فشل في حذف السجلات")
                
        except Exception as e:
            self.show_error_message(f"خطأ في حذف السجلات: {str(e)}")

    def show_success_message(self, message):
        """عرض رسالة نجاح"""
        snack_bar = ft.SnackBar(
            ft.Text(message, text_align='center', weight=ft.FontWeight.BOLD),
            bgcolor="#4CAF50",  # GREEN
            duration=3000,
            show_close_icon=True,
        )
        self.page.snack_bar = snack_bar
        snack_bar.open = True
        self.page.update()

    def show_error_message(self, message):
        """عرض رسالة خطأ"""
        snack_bar = ft.SnackBar(
            ft.Text(message, text_align='center', weight=ft.FontWeight.BOLD),
            bgcolor="#F44336",  # RED
            duration=3000,
            show_close_icon=True,
        )
        self.page.snack_bar = snack_bar
        snack_bar.open = True
        self.page.update()

# # تشغيل التطبيق
# def main(page: ft.Page):
#     page.title = "تقارير الحضور والانصراف"
#     page.fonts = {"Cairo": "assets/fonts/Cairo-VariableFont_slnt,wght.ttf"}
#     page.theme = ft.Theme(font_family="Cairo")
#     page.padding = 0  # Remove padding to allow the container to fill the page
#     page.scroll = False  # Disable scrolling on the main page

#     reports_page = ReportsPage(page)
#     page.add(reports_page)

# ft.app(target=main)