# -*- coding: utf-8 -*-
import flet as ft
from datetime import datetime, date
import asyncio
from db import record_check_in, record_check_out, log_action, get_employees, get_users
import os
import glob

# ألوان عصرية مع تدرجات
PRIMARY_GRADIENT = ft.LinearGradient(
    begin=ft.alignment.top_left,
    end=ft.alignment.bottom_right,
    colors=["#00BCD4", "#0097A7"]
)

SUCCESS_GRADIENT = ft.LinearGradient(
    begin=ft.alignment.top_left,
    end=ft.alignment.bottom_right,
    colors=["#11998e", "#38ef7d"]
)

DANGER_GRADIENT = ft.LinearGradient(
    begin=ft.alignment.top_left,
    end=ft.alignment.bottom_right,
    colors=["#ff416c", "#ff4b2b"]
)

WARNING_GRADIENT = ft.LinearGradient(
    begin=ft.alignment.top_left,
    end=ft.alignment.bottom_right,
    colors=["#f7971e", "#ffd200"]
)

INFO_GRADIENT = ft.LinearGradient(
    begin=ft.alignment.top_left,
    end=ft.alignment.bottom_right,
    colors=["#4facfe", "#00f2fe"]
)

# ألوان ثابتة
PRIMARY_COLOR = "#00BCD4"
SUCCESS_COLOR = "#11998e"
DANGER_COLOR = "#ff416c"
WARNING_COLOR = "#f7971e"
INFO_COLOR = "#4facfe"
LIGHT_BG = "#f8fafc"
CARD_BG = "#ffffff"
GLASS_BG = "rgba(255, 255, 255, 0.25)"

class ModernCard(ft.Container):
    def __init__(self, content, **kwargs):
        super().__init__(
            content=content,
            bgcolor=CARD_BG,
            border_radius=20,
            padding=24,
            margin=ft.margin.only(bottom=16),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 8)
            ),
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.GREY_400)),
            **kwargs
        )

class GlassCard(ft.Container):
    def __init__(self, content, **kwargs):
        super().__init__(
            content=content,
            bgcolor=GLASS_BG,
            border_radius=20,
            padding=20,
            margin=ft.margin.only(bottom=16),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            **kwargs
        )

class GradientButton(ft.Container):
    def __init__(self, text, icon, gradient, on_click=None, disabled=False, **kwargs):
        super().__init__(
            content=ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(icon, color=ft.Colors.WHITE, size=20),
                    ft.Text(text, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=16),
                ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.TRANSPARENT,
                    padding=ft.padding.symmetric(horizontal=32, vertical=16),
                    shape=ft.RoundedRectangleBorder(radius=15),
                    elevation=0,
                ),
                on_click=on_click,
                disabled=disabled,
            ),
            gradient=gradient,
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                offset=ft.Offset(0, 6)
            ),
            width=180,
            height=56,
            **kwargs
        )

class ModernAvatar(ft.Container):
    def __init__(self, initials, color, size=80):
        super().__init__(
            content=ft.Text(
                initials,
                size=size // 2,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                text_align=ft.TextAlign.CENTER,
            ),
            width=size,
            height=size,
            border_radius=size // 2,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[color, ft.Colors.with_opacity(0.8, color)]
            ),
            alignment=ft.alignment.center,
            border=ft.border.all(3, ft.Colors.WHITE),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.3, color),
                offset=ft.Offset(0, 8)
            ),
        )

class ManualAttendancePage(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page = page
        # إعداد اللغة
        self.language = page.session.get("language") or "ar"
        self.selected_employee = None
        self.current_date = date.today()
        self.check_in_btn = None
        self.check_out_btn = None
        self.status_icon = ft.Icon(ft.Icons.INFO, color=INFO_COLOR, size=24)
        self.status_color = INFO_COLOR
        
        # إعدادات الصفحة
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 24
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.bgcolor = LIGHT_BG
        
        # تنظيف الصور المؤقتة
        self.cleanup_temp_photos()
        self.build_ui()

    def cleanup_temp_photos(self):
        try:
            photos_dir = os.path.join(os.getcwd(), "temp_photos")
            if os.path.exists(photos_dir):
                for file_path in glob.glob(os.path.join(photos_dir, "*.jpg")):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
        except Exception:
            pass

    def build_ui(self):
        # مؤشر الحالة - يجب تعريفه قبل استخدامه في كارد اختيار الموظف
        self.status_indicator = GlassCard(
            content=ft.Card(ft.Row([
                self.status_icon,
                ft.Text(
                    "جاهز لتسجيل الحضور والانصراف",
                    size=18,
                    weight=ft.FontWeight.W_500,
                    color=self.status_color,
                ),
            ], spacing=15, alignment=ft.MainAxisAlignment.CENTER),
            width=600,
        ))

        # Header مع تدرج لوني
        header = ft.Container(
            content=ft.Column([
                # العنوان الرئيسي
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.FACT_CHECK, size=28, color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                        border_radius=8,
                        padding=4,
                    ),
                    ft.Text(
                        "نظام الحضور والانصراف اليدوي",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                # التاريخ
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CALENDAR_TODAY, color=ft.Colors.WHITE, size=14),
                        ft.Text(
                            f"التاريخ: {self.current_date.strftime('%Y-%m-%d')}",
                            size=12,
                            weight=ft.FontWeight.W_500,
                            color=ft.Colors.WHITE,
                        ),
                    ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            gradient=PRIMARY_GRADIENT,
            border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
            padding=ft.padding.only(top=12, bottom=12, left=16, right=16),
            margin=ft.margin.only(bottom=18),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color=ft.Colors.with_opacity(0.18, PRIMARY_COLOR),
                offset=ft.Offset(0, 8)
            ),
        )

        # قسم اختيار الموظف - في الأعلى
        employee_selection = ModernCard(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.PERSON_SEARCH, size=20, color=ft.Colors.WHITE),
                        gradient=WARNING_GRADIENT,
                        border_radius=8,
                        padding=4,
                    ),
                    ft.Text(
                        "اختيار الموظف",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=PRIMARY_COLOR,
                    ),
                ], spacing=8),
                ft.Container(
                    content=ft.Dropdown(
                        label="اختر الموظف من القائمة",
                        hint_text="اضغط هنا لاختيار موظف",
                        width=350,
                        border_color=ft.Colors.TRANSPARENT,
                        focused_border_color=PRIMARY_COLOR,
                        on_change=self.on_employee_selected,
                        text_style=ft.TextStyle(size=14, color=ft.Colors.BLACK),
                        label_style=ft.TextStyle(color=ft.Colors.BLACK),
                        hint_style=ft.TextStyle(color=ft.Colors.BLACK),
                    ),
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.GREY_400),
                    border_radius=10,
                    padding=ft.padding.only(left=10, right=10, top=3, bottom=3),
                ),
                self.status_indicator,
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=400,
        )

        # بطاقة معلومات الموظف - في الوسط
        self.employee_info_card = ModernCard(
            content=ft.Container(
                content=ft.Text("سيتم عرض معلومات الموظف هنا", color=PRIMARY_COLOR),
                alignment=ft.alignment.center,
                expand=True,
                
            ),
            visible=False,
            width=400,
        )

        # أزرار التحضير والانصراف
        self.check_in_btn = GradientButton(
            text="تسجيل التحضير",
            icon=ft.Icons.LOGIN,
            gradient=SUCCESS_GRADIENT,
            on_click=self.check_in_employee,
            disabled=True,
        )
        
        self.check_out_btn = GradientButton(
            text="تسجيل الانصراف",
            icon=ft.Icons.LOGOUT,
            gradient=DANGER_GRADIENT,
            on_click=self.check_out_employee,
            disabled=True,
        )

        # بطاقة الأزرار - في الأسفل
        attendance_card = ModernCard(
            content=ft.Container(
                content=ft.Column([
                    # عنوان القسم
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.ACCESS_TIME, size=28, color=ft.Colors.WHITE),
                            gradient=INFO_GRADIENT,
                            border_radius=10,
                            padding=8,
                        ),
                        ft.Text(
                            "تسجيل الحضور والانصراف",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=PRIMARY_COLOR,
                        ),
                    ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                    
                    # الأزرار
                    ft.Container(
                        content=ft.Row([
                            self.check_in_btn,
                            ft.VerticalDivider(width=15, color=ft.Colors.TRANSPARENT),
                            self.check_out_btn,
                        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        expand=True,
                    ),
                ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True,
                height=230
            ),
            width=500,
            
        )

        # صف البطاقات - معلومات الموظف والأزرار في صف واحد
        cards_row = ft.Row([
            self.employee_info_card,
            ft.VerticalDivider(width=20, color=ft.Colors.TRANSPARENT),
            attendance_card,
        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)

        # ترتيب العناصر بشكل منطقي: Header -> اختيار الموظف -> صف البطاقات -> الحالة
        self.controls = [
            header,
            employee_selection,
            cards_row,
        ]
        
        # تحميل الموظفين
        self.load_employees()

    def load_employees(self):
        try:
            employees = get_employees()
            dropdown = self.controls[1].content.controls[1].content
            
            dropdown.options = [
                ft.dropdown.Option(
                    key="",
                    text="اختر موظف من القائمة",
                    disabled=True,
                )
            ]
            
            for emp in employees:
                if len(emp) >= 7:
                    emp_id, first_name, email, phone, position, department, face_data = emp[:7]
                    dropdown.options.append(
                        ft.dropdown.Option(
                            key=str(emp_id),
                            text=f"{first_name} - {position} ({department})",
                        )
                    )
            
            self.page.update()
            
        except Exception as e:
            self.show_status(f"خطأ في تحميل قائمة الموظفين: {str(e)}", DANGER_COLOR, ft.Icons.ERROR)

    def on_employee_selected(self, e):
        if not e.control.value or e.control.value == "":
            self.hide_employee_info()
            self.disable_attendance_buttons()
            return
        
        try:
            employees = get_employees()
            selected_emp = None
            
            for emp in employees:
                if str(emp[0]) == e.control.value:
                    selected_emp = emp
                    break
            
            if selected_emp:
                self.selected_employee = selected_emp
                self.update_employee_info(selected_emp)
                self.enable_attendance_buttons()
                self.show_status(f"تم اختيار الموظف: {selected_emp[1]}", SUCCESS_COLOR, ft.Icons.CHECK_CIRCLE)
            else:
                self.show_status("لم يتم العثور على الموظف المحدد", DANGER_COLOR, ft.Icons.ERROR)
                
        except Exception as error:
            self.show_status(f"خطأ في اختيار الموظف: {str(error)}", DANGER_COLOR, ft.Icons.ERROR)

    def update_employee_info(self, employee_data):
        if len(employee_data) >= 7:
            emp_id, first_name, email, phone, position, department, face_data = employee_data[:7]
            photo_data = employee_data[7] if len(employee_data) > 7 else None
        else:
            return
        
        # إنشاء صورة الموظف
        employee_photo = self.create_employee_photo(face_data, first_name, photo_data)
        
        info_content = ft.Container(
            content=ft.Column([
                # عنوان القسم
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.PERSON, size=28, color=ft.Colors.WHITE),
                        gradient=SUCCESS_GRADIENT,
                        border_radius=10,
                        padding=8,
                    ),
                    ft.Text(
                        "معلومات الموظف",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=SUCCESS_COLOR,
                    ),
                ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                
                # معلومات الموظف
                ft.Container(
                    content=ft.Row([
                        # صورة الموظف على اليسار
                        ft.Container(
                            content=employee_photo,
                            alignment=ft.alignment.center,
                            width=120,
                        ),
                        
                        ft.VerticalDivider(width=20, color=ft.Colors.TRANSPARENT),
                        
                        # معلومات الموظف على اليمين
                        ft.Container(
                            content=ft.Column([
                                self.create_info_row(ft.Icons.BADGE, "الاسم:", first_name),
                                self.create_info_row(ft.Icons.EMAIL, "البريد:", email),
                                self.create_info_row(ft.Icons.PHONE, "الهاتف:", phone),
                                self.create_info_row(ft.Icons.WORK, "المنصب:", position),
                                self.create_info_row(ft.Icons.BUSINESS, "القسم:", department),
                            ], spacing=0),
                            padding=20,
                            bgcolor=ft.Colors.with_opacity(0.05, INFO_COLOR),
                            border_radius=15,
                            expand=True,
                        ),
                    ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                    expand=True,
                ),
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True,
        )
        
        self.employee_info_card.content = info_content
        self.employee_info_card.visible = True
        self.page.update()

    def create_info_row(self, icon, label, value):
        return ft.Row([
            ft.Icon(icon, color=PRIMARY_COLOR, size=20),
            ft.Text(label, weight=ft.FontWeight.W_500, size=14, color=PRIMARY_COLOR),
            ft.Text(value, weight=ft.FontWeight.W_500, size=14, color=PRIMARY_COLOR),
        ], spacing=10)

    def create_employee_photo(self, face_data, name, photo_data=None):
        try:
            if photo_data and len(photo_data) > 0:
                import base64
                photos_dir = os.path.join(os.getcwd(), "temp_photos")
                if not os.path.exists(photos_dir):
                    os.makedirs(photos_dir)
                temp_filename = f"photo_{name.replace(' ', '_')}_{id(photo_data)}.jpg"
                temp_path = os.path.join(photos_dir, temp_filename)
                with open(temp_path, 'wb') as f:
                    f.write(photo_data)
                if os.path.exists(temp_path):
                    try:
                        return ft.Container(
                            content=ft.Image(
                                src=temp_path,
                                width=100,
                                height=100,
                                fit=ft.ImageFit.COVER,
                                error_content=ft.Text("خطأ في تحميل الصورة", size=12),
                                repeat=ft.ImageRepeat.NO_REPEAT,
                            ),
                            border_radius=50,
                            border=ft.border.all(3, ft.Colors.WHITE),
                            bgcolor=ft.Colors.GREY_100,
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=20,
                                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                                offset=ft.Offset(0, 8)
                            ),
                        )
                    except Exception:
                        try:
                            with open(temp_path, 'rb') as f:
                                image_data = f.read()
                            image_base64 = base64.b64encode(image_data).decode()
                            return ft.Container(
                                content=ft.Image(
                                    src=f"data:image/jpeg;base64,{image_base64}",
                                    width=100,
                                    height=100,
                                    fit=ft.ImageFit.COVER,
                                    error_content=ft.Text("خطأ في تحميل الصورة", size=12),
                                    repeat=ft.ImageRepeat.NO_REPEAT,
                                ),
                                border_radius=50,
                                border=ft.border.all(3, ft.Colors.WHITE),
                                bgcolor=ft.Colors.GREY_100,
                                shadow=ft.BoxShadow(
                                    spread_radius=0,
                                    blur_radius=20,
                                    color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                                    offset=ft.Offset(0, 8)
                                ),
                            )
                        except Exception:
                            return self.create_avatar_with_initials(name, INFO_COLOR)
                else:
                    return self.create_avatar_with_initials(name, INFO_COLOR)
            else:
                return self.create_avatar_with_initials(name, INFO_COLOR)
        except Exception:
            return self.create_avatar_with_initials(name, ft.Colors.GREY_600)

    def create_avatar_with_initials(self, name, color):
        words = name.split()
        if len(words) >= 2:
            initials = words[0][0] + words[1][0]
        else:
            initials = name[:2]
        initials = initials.upper()
        
        return ModernAvatar(initials, color, 100)

    def hide_employee_info(self):
        self.employee_info_card.visible = False
        self.page.update()

    def enable_attendance_buttons(self):
        self.check_in_btn.content.disabled = False
        self.check_out_btn.content.disabled = False
        self.page.update()

    def disable_attendance_buttons(self):
        if self.check_in_btn and self.check_out_btn:
            self.check_in_btn.content.disabled = True
            self.check_out_btn.content.disabled = True
            self.page.update()

    async def check_in_employee(self, e):
        if not self.selected_employee:
            self.show_status("يرجى اختيار موظف أولاً", DANGER_COLOR, ft.Icons.ERROR)
            return
        
        emp_id = self.selected_employee[0]
        first_name = self.selected_employee[1]
        
        try:
            # جلب user_id من الجلسة إذا كان متاحاً
            current_username = self.page.session.get("username")
            users = get_users()
            user_id = next((u[0] for u in users if u[1] == current_username), None)
            success = record_check_in(emp_id, self.current_date)
            
            if success:
                self.show_status(
                    f"تم تسجيل التحضير بنجاح للموظف: {first_name}",
                    SUCCESS_COLOR, ft.Icons.CHECK_CIRCLE
                )
                log_action(employee_id=emp_id, action=f"تحضير يدوي - {first_name}", user_id=user_id)
                
                self.check_in_btn.content.disabled = True
                self.page.update()
                
                await asyncio.sleep(2)
                self.check_in_btn.content.disabled = False
                self.page.update()
            else:
                self.show_status(
                    f"تم تسجيل التحضير مسبقاً للموظف: {first_name}",
                    WARNING_COLOR, ft.Icons.WARNING
                )
                
        except Exception as error:
            self.show_status(f"خطأ في تسجيل التحضير: {str(error)}", DANGER_COLOR, ft.Icons.ERROR)

    async def check_out_employee(self, e):
        if not self.selected_employee:
            self.show_status("يرجى اختيار موظف أولاً", DANGER_COLOR, ft.Icons.ERROR)
            return
        
        emp_id = self.selected_employee[0]
        first_name = self.selected_employee[1]
        
        try:
            # جلب user_id من الجلسة إذا كان متاحاً
            current_username = self.page.session.get("username")
            users = get_users()
            user_id = next((u[0] for u in users if u[1] == current_username), None)
            success = record_check_out(emp_id)
            
            if success:
                self.show_status(
                    f"تم تسجيل الانصراف بنجاح للموظف: {first_name}",
                    SUCCESS_COLOR, ft.Icons.CHECK_CIRCLE
                )
                log_action(employee_id=emp_id, action=f"انصراف يدوي - {first_name}", user_id=user_id)
                
                self.check_out_btn.content.disabled = True
                self.page.update()
                
                await asyncio.sleep(2)
                self.check_out_btn.content.disabled = False
                self.page.update()
            else:
                self.show_status(
                    f"لم يتم العثور على تسجيل حضور للموظف: {first_name}",
                    WARNING_COLOR, ft.Icons.WARNING
                )
                
        except Exception as error:
            self.show_status(f"خطأ في تسجيل الانصراف: {str(error)}", DANGER_COLOR, ft.Icons.ERROR)

    def show_status(self, message, color, icon=ft.Icons.INFO):
        self.status_icon.name = icon
        self.status_icon.color = color
        self.status_color = color
        self.status_indicator.content.content.controls[1].value = message
        self.status_indicator.content.content.controls[1].color = color
        self.page.update()

def main(page: ft.Page):
    page.title = "نظام التحضير والانصراف اليدوي - التصميم العصري"
    page.window.width = 1200
    page.window.height = 900
    page.window.resizable = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = LIGHT_BG
    page.padding = 0
    page.rtl = True
    
    manual_page = ManualAttendancePage(page)
    page.add(manual_page)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)