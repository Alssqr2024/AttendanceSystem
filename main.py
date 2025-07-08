# -*- coding: utf-8 -*-
"""
نظام إدارة الحضور والانصراف
Attendance Management System
"""

import flet as ft
import os
import sys
from db import initialize_connection_pool
from login_page import main as login_main

def main(page: ft.Page):
    """الدالة الرئيسية للتطبيق"""
    # إعدادات الصفحة الأساسية
    page.title = "نظام إدارة الحضور والانصراف"
    
    # إعدادات النافذة
    page.window.width = 1200
    page.window.height = 700
    page.window.min_width = 800
    page.window.min_height = 600
    page.window.center()
    page.window.resizable = True
    page.window.maximizable = True
    
    # إعداد الخطوط
    page.fonts = {
        "Cairo": "assets/fonts/Cairo-VariableFont_slnt,wght.ttf",
        "Amiri": "assets/fonts/Amiri-Italic.ttf"
    }
    page.theme = ft.Theme(font_family="Cairo")
    
    # تهيئة قاعدة البيانات إذا كان ذلك مطلوباً
    if hasattr(sys.modules.get('db'), 'initialize_connection_pool'):
        initialize_connection_pool()
    
    # تشغيل صفحة تسجيل الدخول
    login_main(page)

if __name__ == "__main__":
    # التحقق من وجود الملفات المطلوبة
    required_files = [
        "assets/fonts/Cairo-VariableFont_slnt,wght.ttf",
        "assets/fonts/Amiri-Italic.ttf",
        "config.ini"
    ]
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    if missing_files:
        print("ملفات مفقودة:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        print("\nيرجى التأكد من وجود جميع الملفات المطلوبة.")
        sys.exit(1)
    # تشغيل التطبيق
    ft.app(target=main, assets_dir="assets") 