import flet as ft
from db import add_user, get_users, delete_user, update_user
from functools import partial

class AddUserPage(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page = page
        
        self.expand = True
        self.alignment = ft.MainAxisAlignment.START
        self.spacing = 10

        self.initialize_ui_components()
        self.build_ui()
        self.refresh_table()

    def initialize_ui_components(self):
        # معرفة صلاحية المستخدم الحالي
        # حقول الإدخال
        self.username_field = self.create_text_field("اسم المستخدم", ft.Icons.PERSON_OUTLINE, tooltip="أدخل اسم المستخدم الذي سيستخدم لتسجيل الدخول")
        self.password_field = self.create_text_field("كلمة المرور", ft.Icons.LOCK_OUTLINE, True, tooltip="أدخل كلمة مرور قوية للمستخدم")
        # الوظائف الممكنة
        self.all_functions = [
            ("dashboard", "الرئيسية"),
            ("attendance", "الحصور اليدوي"),
            ("reports", "التقارير"),
            ("logs", "السجلات"),
            ("management", "الإدارة"),
            ("add_user", "إضافة مستخدم"),
            ("settings", "الإعدادات")
        ]
        # قائمة CheckBox للوظائف
        self.functions_checks = [
            ft.Checkbox(label=label, value=False, key=key, check_color=ft.Colors.WHITE, fill_color=ft.Colors.CYAN_400)
            for key, label in self.all_functions
        ]
        # الجدول
        self.users_table = ft.DataTable(
            columns=[],
            rows=[],
            expand=True,
            border=ft.border.all(1, ft.Colors.BLACK),
            border_radius=10,
            heading_row_color=ft.Colors.CYAN_800,
            heading_row_height=45,
            data_row_min_height=50,
            divider_thickness=0.5,
            horizontal_lines=ft.border.BorderSide(0.5, "#E2E8F0"),
            heading_text_style=ft.TextStyle(
                color="white",
                weight="bold",
                font_family="arabic"
            ),
        )

        # حقل البحث
        self.search_field = ft.TextField(
            label="بحث بالإسم",
            prefix_icon=ft.Icons.SEARCH,
            width=300,
            border_radius=10,
            on_change=self.on_search_change,
            tooltip="ابحث عن مستخدم معين عن طريق كتابة اسمه",
        )

    def create_text_field(self, label, icon, is_password=False, tooltip=None):
        return ft.TextField(
            label=label,
            prefix_icon=icon,
            password=is_password,
            can_reveal_password=is_password,
            border_radius=10,
            width=280,
            tooltip=tooltip,
        )

    def build_ui(self):
        # زر الإضافة
        add_button = ft.ElevatedButton(
            "إضافة مستخدم",
            icon=ft.Icons.PERSON_ADD,
            width=280,
            height=50,
            on_click=self.add_user_clicked,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            tooltip="إضافة مستخدم جديد إلى النظام بالبيانات المحددة",
        )

        # اللوحة اليسرى (لوحة الإدخال)
        form_panel = ft.Container(
            width=350,
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.CYAN_800,
            border_radius=15,
            content=ft.Column(
                controls=[
                    self.username_field,
                    self.password_field,
                    ft.Divider(height=10, color="transparent"),
                    ft.Text("حدد الوظائف:", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Column(self.functions_checks, scroll=ft.ScrollMode.AUTO, spacing=5),
                        height=200,
                        border=ft.border.all(1, ft.Colors.WHITE24),
                        padding=10,
                        border_radius=10,
                    ),
                    ft.Divider(height=10, color="transparent"),
                    add_button
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

        # جدول المستخدمين
        scrollable_table = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=False,
            controls=[self.users_table],
        )

        # اللوحة اليمنى (الجدول)
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
            content=ft.Text("إدارة المستخدمين", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align='center'),
            bgcolor=ft.Colors.CYAN_800,
            padding=15,
            border_radius=15,
            width=1400,
        )

        # بناء الواجهة النهائية
        self.controls = [
            appbar,
            ft.Row(
                [form_panel, table_panel],
                vertical_alignment=ft.CrossAxisAlignment.START,
                expand=True
            )
        ]

    def on_search_change(self, e):
        self.refresh_table(search_term=e.control.value)

    def refresh_table(self, search_term=None):
        users = get_users()
        columns = [
            ft.DataColumn(ft.Text("اسم المستخدم", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("الوظائف", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("الإجراءات", weight=ft.FontWeight.BOLD)),
        ]
        rows = []
        for user in users:
            if search_term and search_term.strip().lower() not in user[1].lower():
                continue
            functions_display = "، ".join([
                label for key, label in self.all_functions if user[3] and key in (user[3] or "")
            ])
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(user[1])),
                        ft.DataCell(ft.Text(functions_display)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color=ft.Colors.BLUE,
                                    on_click=lambda e, u=user[1]: self.edit_user_dialog(u),
                                    tooltip="تعديل بيانات المستخدم المحدد",
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ft.Colors.RED,
                                    on_click=lambda e, u=user[1]: self.delete_user(u),
                                    tooltip="حذف المستخدم المحدد من النظام",
                                )
                            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER)
                        )
                    ]
                )
            )
        self.users_table.columns = columns
        self.users_table.rows = rows
        self.page.update()

    def edit_user_dialog(self, username):
        user_data = next((u for u in get_users() if u[1] == username), None)  # user[1] هو اسم المستخدم
        if not user_data:
            self.show_snackbar("المستخدم غير موجود!", ft.Colors.RED)
            return
        old_password = user_data[2]  # user[2] هو كلمة المرور
        old_functions = user_data[3] or ""
        edit_username = ft.TextField(
            label="اسم المستخدم",
            value=user_data[1],
            read_only=False,  # السماح بالتعديل
            width=350,
            on_change=lambda e: None  # إصلاح مشكلة الكيبورد في بعض الحالات
        )
        edit_password = ft.TextField(
            label="كلمة المرور الجديدة (اتركها فارغة للحفاظ على القديمة)",
            password=True,
            can_reveal_password=True,
            width=350
        )
        edit_functions_checks = [
            ft.Checkbox(label=label, value=(key in old_functions.split(",")), key=key, fill_color=ft.Colors.CYAN_800)
            for key, label in self.all_functions
        ]

        dialog_content = ft.Column(
            [
                edit_username,
                edit_password,
                ft.Divider(height=5, color="transparent"),
                ft.Text("حدد الوظائف المسموح بها:", size=16),
                ft.Container(
                    content=ft.Column(
                        controls=edit_functions_checks,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    height=200,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=10,
                    padding=10
                ),
            ],
            spacing=15,
            height=400,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        def save_changes(e):
            new_username = edit_username.value.strip()
            new_password = edit_password.value.strip()
            new_functions = ",".join([cb.key for cb in edit_functions_checks if cb.value])
            final_password = new_password if new_password else old_password
            current_username = self.page.session.get("username")
            from db import get_users, log_action
            users = get_users()
            user_id = None
            for u in users:
                if u[1] == current_username:
                    user_id = u[0]
                    break
            # إذا تم تغيير اسم المستخدم، نفذ التعديل مع الاسم الجديد
            if new_username != username:
                if add_user(new_username, final_password, new_functions):
                    delete_user(username)
                    log_action(user_id=user_id, action=f"غيّر المستخدم {current_username} اسم المستخدم من {username} إلى {new_username}")
                    self.show_snackbar("تم تغيير اسم المستخدم والتحديث بنجاح", ft.Colors.GREEN)
                else:
                    self.show_snackbar("اسم المستخدم الجديد مستخدم بالفعل!", ft.Colors.RED)
                    return
            else:
                if update_user(username, final_password, new_functions):
                    log_action(user_id=user_id, action=f"عدّل المستخدم {current_username} بيانات المستخدم {username}")
                    self.show_snackbar("تم التحديث بنجاح", ft.Colors.GREEN)
                else:
                    self.show_snackbar("فشل في التحديث!", ft.Colors.RED)
            self.refresh_table()
            dlg.open = False
            self.page.update()
        dlg = ft.AlertDialog(
            title=ft.Text("تعديل المستخدم"),
            content=dialog_content,
            actions=[
                ft.TextButton("إلغاء", on_click=lambda e: (setattr(dlg, 'open', False), self.page.update())),
                ft.TextButton("حفظ", on_click=save_changes, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def add_user_clicked(self, e):
        username = self.username_field.value.strip()
        password = self.password_field.value.strip()
        selected_functions = [cb.key for cb in self.functions_checks if cb.value]
        functions_str = ",".join(selected_functions)
        if not all([username, password]):
            self.show_snackbar("❗ يرجى ملء جميع الحقول", ft.Colors.RED)
            return
        if add_user(username, password, functions_str):
            # تسجيل الحدث
            current_username = self.page.session.get("username")
            from db import get_users, log_action
            users = get_users()
            user_id = None
            for u in users:
                if u[1] == current_username:
                    user_id = u[0]
                    break
            log_action(user_id=user_id, action=f"أضاف المستخدم {current_username} مستخدمًا جديدًا باسم {username}")
            self.show_snackbar("✔ تمت الإضافة بنجاح", ft.Colors.GREEN)
            self.clear_fields()
            self.refresh_table()
        else:
            self.show_snackbar("❌ فشل في الإضافة! اسم مستخدم موجود", ft.Colors.RED)

    def delete_user(self, username):
        def confirm_delete(e):
            from db import get_users, log_action
            users = get_users()
            current_username = self.page.session.get("username")
            user_id = None
            for u in users:
                if u[1] == current_username:
                    user_id = u[0]
                    break
            if user_id is not None:
                from db import delete_user_logs
                delete_user_logs(user_id)
            if delete_user(username):
                log_action(user_id=user_id, action=f"حذف المستخدم {current_username} المستخدم {username}")
                self.show_snackbar(f"تم حذف {username}", ft.Colors.GREEN)
                self.refresh_table()
            dlg.open = False
            self.page.update()
        dlg = ft.AlertDialog(
            title=ft.Text("تأكيد الحذف"),
            content=ft.Text(f"هل تريد حذف المستخدم {username}؟"),
            actions=[
                ft.TextButton("نعم", on_click=confirm_delete),
                ft.TextButton("لا", on_click=lambda e: setattr(dlg, 'open', False))
            ]
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def show_snackbar(self, message, color):
        snackbar = ft.SnackBar(
            ft.Text(message, color="white"),
            bgcolor=color,
            behavior=ft.SnackBarBehavior.FLOATING,
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        if snackbar not in self.page.overlay:
            self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def clear_fields(self):
        self.username_field.value = ""
        self.password_field.value = ""
        for cb in self.functions_checks:
            cb.value = False
        self.page.update()

    def did_mount(self):
        self.refresh_table()

# أضف هذا الكود في نهاية ملف add_user_page.py
def main(page: ft.Page):
    page.title = "نظام إدارة المستخدمين"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 10
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.fonts = {"arabic": "assets/fonts/Cairo-VariableFont_slnt,wght.ttf"}
    page.add(AddUserPage(page))

if __name__ == "__main__":
    ft.app(target=main)