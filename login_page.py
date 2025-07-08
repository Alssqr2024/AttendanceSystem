# -*- coding: utf-8 -*-
import flet as ft
from datetime import datetime
from db import get_users, check_user_password
from attendance_page import create_attendance_system
from Home import create_home_page
import asyncio
import threading
import time


def main(page: ft.Page):
    # إعدادات الصفحة العامة
    page.title = "نظام الحضور الذكي"
    page.window.maximizable = True
    page.window.resizable = True
    page.window.maximized = True
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # دالة للحصول على أحجام متجاوبة بناءً على حجم النافذة
    def get_responsive_sizes():
        window_width = page.window.width or 1200
        window_height = page.window.height or 700
        
        # تحديد الأحجام بناءً على عرض النافذة
        if window_width < 900:  # شاشات صغيرة
            return {
                'card_width': min(350, window_width - 40),
                'field_width': min(300, window_width - 60),
                'button_width': min(280, window_width - 80),
                'icon_size': 30,
                'title_size': 20,
                'text_size': 14,
                'padding': 15
            }
        elif window_width < 1200:  # شاشات متوسطة
            return {
                'card_width': min(450, window_width - 40),
                'field_width': min(380, window_width - 60),
                'button_width': min(350, window_width - 80),
                'icon_size': 35,
                'title_size': 24,
                'text_size': 15,
                'padding': 20
            }
        else:  # شاشات كبيرة
            return {
                'card_width': min(600, window_width - 40),
                'field_width': min(400, window_width - 60),
                'button_width': min(400, window_width - 80),
                'icon_size': 40,
                'title_size': 28,
                'text_size': 16,
                'padding': 30
            }

#-----------------------دالة فتح صفحة التحضير -----------------------
    def Attendance_Page(e):
        page.clean()
        create_attendance_system(page)
        page.update()
    def change_tab(e):
        index = e.control.selected_index
        tab_content.content = tab_pages[index]
        page.update()
#-----------------------دالة إغلاق الصفحة-----------------------
    def close_page(e):
        page.window_close()
#-----------------------دالة إنشاء واجهة تسجيل الحضور والانصراف-----------------------
    def build_attendance_ui():
        sizes = get_responsive_sizes()
        
        today_date = ft.Text(
            datetime.now().strftime("%Y/%m/%d - %A"),
            size=sizes['text_size'],
            color=ft.Colors.BLUE_700,
            weight="bold"
        )

        current_time = ft.Text(
            datetime.now().strftime("%H:%M:%S"),
            size=sizes['text_size'] + 4,
            color=ft.Colors.GREEN_700,
            weight="bold"
        )

        def update_time():
            current_time.value = datetime.now().strftime("%H:%M:%S")
            page.update()

        page.on_interval = 1, lambda _: update_time()

        # تحديد حجم الأيقونة بناءً على حجم الشاشة
        fingerprint_icon_size = min(200, sizes['card_width'] - 60)
        if sizes['card_width'] < 400:
            fingerprint_icon_size = 150
        elif sizes['card_width'] < 500:
            fingerprint_icon_size = 180

        attendance_card = ft.Card(
            elevation=8,
            content=ft.Container(
                padding=sizes['padding'],
                border_radius=15,
                bgcolor=ft.Colors.WHITE,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.FINGERPRINT, size=sizes['icon_size'], color=ft.Colors.GREEN_700),
                        ft.Text("تسجيل الحضور والانصراف (تحقق ثنائي)", 
                               size=sizes['title_size'], 
                               weight="bold", 
                               color=ft.Colors.BLUE_700),
                    ], alignment="center", spacing=15),
                    ft.Divider(height=30, color="transparent"),
                    ft.Card(
                        content=ft.Icon(ft.Icons.FINGERPRINT, size=fingerprint_icon_size),
                        color=ft.Colors.GREY_100,
                        shadow_color=ft.Colors.BLUE_700,
                        elevation=40
                    ),
                    ft.Row([
                        ft.ElevatedButton("تسجيل الحضور والانصراف",
                                          on_click=Attendance_Page,
                                          bgcolor=ft.Colors.GREEN_700,
                                          color=ft.Colors.WHITE,
                                          width=sizes['button_width'],
                                          height=45),
                    ], alignment="center", spacing=20),
                    ft.Divider(height=30, color="transparent"),
                    ft.Row([today_date, current_time], alignment="center", spacing=20),
                    ft.Text("لن يتم تسجيل الحضور أو الانصراف إلا بعد التحقق بالبصمة والوجه.",
                            size=sizes['text_size'] - 2, 
                            color=ft.Colors.GREY_700, 
                            text_align="center")
                ],
                    horizontal_alignment="center",
                    spacing=10),
                width=sizes['card_width']
            )
        )
        return ft.Container(content=ft.Column([ft.Row([attendance_card], alignment="center")],
                                              alignment=ft.MainAxisAlignment.CENTER,
                                              horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=sizes['padding'] // 2)
    #-----------------------دالة إنشاء واجهة تسجيل الدخول-----------------------
    def build_login_ui():
        sizes = get_responsive_sizes()
        
        username_field = ft.TextField(
            color=ft.Colors.BLACK,
            label="اسم المستخدم",
            hint_text="أدخل اسم المستخدم",
            prefix_icon=ft.Icon(ft.Icons.PERSON, color=ft.Colors.GREEN_700),
            border_radius=15,
            border_color=ft.Colors.BLUE_700,
            focused_border_color=ft.Colors.GREEN_700,
            width=sizes['field_width'],
            height=60,
            text_size=sizes['text_size'],
            filled=True,
            fill_color=ft.Colors.GREY_100
        )

        password_field = ft.TextField(
            label="كلمة المرور",
            hint_text="أدخل كلمة المرور",
            color=ft.Colors.BLACK,
            prefix_icon=ft.Icon(ft.Icons.LOCK, color=ft.Colors.GREEN_700),
            password=True,
            can_reveal_password=True,
            border_radius=15,
            border_color=ft.Colors.BLUE_700,
            focused_border_color=ft.Colors.GREEN_700,
            width=sizes['field_width'],
            height=60,
            text_size=sizes['text_size'],
            filled=True,
            fill_color=ft.Colors.GREY_100
        )

        login_button = ft.ElevatedButton(
            content=ft.Text("تسجيل الدخول", size=sizes['text_size'] + 2, weight="bold"),
            width=sizes['button_width'],
            height=50,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            elevation=5,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=lambda e: page.run_task(login_clicked, e, username_field.value, password_field.value)
        )
        
        def forgot_password(e):
            dialog = ft.AlertDialog(
                title=ft.Text("استعادة كلمة المرور", weight="bold", color=ft.Colors.BLUE_700),
                content=ft.Text(
                    "يرجى التواصل مع مدير النظام أو فريق الدعم لاستعادة كلمة المرور الخاصة بك.",
                    text_align="right",
                    color=ft.Colors.BLACK,
                    size=15
                ),
                actions=[
                    ft.TextButton("إغلاق", on_click=lambda e: setattr(dialog, 'open', False))
                ],
                actions_alignment="end",
                open=True
            )
            if dialog not in page.overlay:
                page.overlay.append(dialog)
            dialog.open = True
            page.update()

        login_card = ft.Card(
            elevation=8,
            content=ft.Container(
                padding=sizes['padding'],
                border_radius=15,
                bgcolor=ft.Colors.WHITE,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.LOCK_PERSON, size=sizes['icon_size'], color=ft.Colors.GREEN_700),
                                ft.Text("تسجيل دخول المدير", size=sizes['title_size'], weight="bold", color=ft.Colors.BLUE_700),
                            ],
                            alignment="center",
                            spacing=15
                        ),
                        ft.Divider(height=30, color="transparent"),
                        username_field,
                        ft.Divider(height=15, color="transparent"),
                        password_field,
                        ft.Divider(height=30, color="transparent"),
                        login_button,
                        ft.Divider(height=20, color="transparent"),
                        ft.TextButton(
                            content=ft.Text("نسيت كلمة المرور؟", size=sizes['text_size'] - 2, color=ft.Colors.GREEN_700),
                            on_click=forgot_password
                        )
                    ],
                    horizontal_alignment="center",
                    spacing=5
                ),
                width=sizes['card_width']
            )
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([login_card], alignment="center"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=sizes['padding'] // 2
        )
#-----------------------دالة تسجيل الدخول-----------------------
    async def login_clicked(e, username, password):
        if check_user_password(username, password):
            users = get_users()
            current_user_id = None
            for user in users:
                if user[1] == username:
                    current_user_id = user[0]  # حفظ رقم المستخدم
                    break
            
            # حفظ اسم المستخدم في الجلسة
            page.session.set("username", username)
            
            # إظهار رسالة نجاح
            snack_bar = ft.SnackBar(
                content=ft.Text(f"مرحباً {username}! جاري التوجيه إلى لوحة التحكم..."),
                bgcolor=ft.Colors.GREEN_700
            )
            page.overlay.append(snack_bar)
            snack_bar.open = True
            page.update()
            
            # الانتقال إلى الصفحة الرئيسية بعد ثانيتين
            async def navigate_to_home():
                await asyncio.sleep(2)
                page.clean()
                create_home_page(page)
                page.update()
            
            # تشغيل الانتقال بشكل غير متزامن
            page.run_task(navigate_to_home)
        else:
            # إظهار رسالة خطأ
            snack_bar = ft.SnackBar(
                content=ft.Text("خطأ في اسم المستخدم أو كلمة المرور!"),
                bgcolor=ft.Colors.RED
            )
            page.overlay.append(snack_bar)
            snack_bar.open = True
            page.update()

    # إنشاء التبويبات
    tab_pages = [build_attendance_ui(), build_login_ui()]
    tab_content = ft.Container(content=tab_pages[0], expand=True)

    # تعريف التبويبات المتجاوبة
    sizes = get_responsive_sizes()
    tab_text_size = sizes['text_size'] + 2 if sizes['text_size'] > 14 else 16
    
    tabs = ft.Tabs(
        tab_alignment=ft.TabAlignment.CENTER,
        selected_index=0,
        label_color=ft.Colors.BLUE_700,
        label_text_style=ft.TextStyle(size=tab_text_size),
        unselected_label_color="black",
        unselected_label_text_style=ft.TextStyle(size=max(10, tab_text_size - 4)),
        on_change=change_tab,
        tabs=[
            ft.Tab(text="تسجيل الحضور والانصراف", icon=ft.Icons.FINGERPRINT),
            ft.Tab(text="تسجيل دخول المدير", icon=ft.Icons.MANAGE_ACCOUNTS_SHARP)
        ]
    )

    footer = ft.Container(
        content=ft.Text("© 2025 نظام إدارة الحضور الذكي - جميع الحقوق محفوظة", 
                       size=max(12, sizes['text_size'] - 4), 
                       color=ft.Colors.GREY_700, 
                       text_align="center"),
        padding=sizes['padding'] // 2,
        bgcolor=ft.Colors.GREY_100,
        alignment=ft.alignment.center
    )

    # صفحة التعليمات
    def show_instructions(e=None):
        instructions_text = (
            """
            تعليمات استخدام نظام الحضور الذكي:
            1. قم بتسجيل الدخول باستخدام اسم المستخدم وكلمة المرور الخاصة بك.
            2. يمكنك تسجيل الحضور والانصراف من خلال التبويب المخصص لذلك.
            3. يجب التحقق بالبصمة والوجه لإتمام عملية التسجيل.
            4. في حال نسيان كلمة المرور، استخدم خيار "نسيت كلمة المرور؟".
            5. يمكنك التنقل بين التبويبات للوصول إلى مختلف وظائف النظام.
            6. تأكد من تسجيل الخروج بعد الانتهاء من استخدام النظام.
            
            لمزيد من الدعم أو الاستفسارات:
            تواصل مع الدعم الفني: ahmedaldhuraibi@gmail.com
            """
        )
        dialog = ft.AlertDialog(
            title=ft.Text("تعليمات النظام", weight="bold", color=ft.Colors.BLUE_700),
            content=ft.Text(instructions_text, text_align="right", color=ft.Colors.BLACK, size=15),
            actions=[
                ft.TextButton("إغلاق", on_click=lambda e: setattr(dialog, 'open', False))
            ],
            actions_alignment="end",
            open=True
        )
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()

    # AppBar متجاوب
    appbar_title_size = sizes['title_size'] - 4 if sizes['title_size'] > 20 else 18
    
    page.add(
        ft.AppBar(
            title=ft.Text("نظام الحضور الذكي", 
                         weight="bold", 
                         color=ft.Colors.WHITE,
                         size=appbar_title_size), 
            center_title=True, 
            bgcolor=ft.Colors.BLUE_700,
            actions=[
                ft.IconButton(ft.Icons.INFO, icon_color=ft.Colors.WHITE, tooltip="تعليمات النظام", on_click=show_instructions),
                ft.IconButton(icon=ft.Icons.LOGOUT, 
                             icon_color=ft.Colors.WHITE, 
                             tooltip="خروج من النظام", 
                             on_click=close_page)
            ]
        ),
        ft.Card(
            elevation=8, 
            content=ft.Container(
                padding=sizes['padding'] // 2, 
                bgcolor=ft.Colors.WHITE, 
                border_radius=15, 
                content=tabs
            )
        ),
        ft.Column([
            ft.Divider(height=2, color=ft.Colors.BLUE_700), 
            tab_content, 
            footer
        ], spacing=0, expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)