"""
مدير المظهر - تطبيق إعدادات المظهر على جميع صفحات النظام
"""

import flet as ft
import configparser
import os

def setup_page_theme(page: ft.Page, title: str = None):
    """إعداد المظهر الأساسي للصفحة"""
    if title:
        page.title = title
    
    # قراءة إعدادات المظهر من ملف التكوين
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    theme_mode = config.get('Appearance', 'theme', fallback='light')
    
    if theme_mode == 'dark':
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#212121"  # GREY_900
    else:
        page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = "#ECEFF1"  # BLUE_GREY_50
    
    return page

def get_text_color(page: ft.Page):
    """الحصول على لون النص المناسب للثيم الحالي"""
    if page.theme_mode == ft.ThemeMode.DARK:
        return "#FFFFFF"  # WHITE
    else:
        return "#000000"  # BLACK

def get_card_bg_color(page: ft.Page):
    """الحصول على لون خلفية البطاقات المناسب للثيم الحالي"""
    if page.theme_mode == ft.ThemeMode.DARK:
        return "#424242"  # GREY_800
    else:
        return "#FFFFFF"  # WHITE

def get_primary_color(page: ft.Page):
    """الحصول على اللون الأساسي"""
    return "#1976D2"  # BLUE_700

def get_secondary_color(page: ft.Page):
    """الحصول على اللون الثانوي"""
    return "#388E3C"  # GREEN_700

def get_table_header_color(page: ft.Page):
    """الحصول على لون رأس الجدول"""
    return "#BBDEFB"  # BLUE_100

def get_table_bg_color(page: ft.Page):
    """الحصول على لون خلفية الجدول"""
    return "#FFFFFF"  # WHITE

def get_report_font_path():
    """الحصول على مسار خط التقارير"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config.get('Appearance', 'report_font', fallback='assets/fonts/Amiri-Italic.ttf')

def apply_theme_to_page(page: ft.Page):
    """تطبيق المظهر على الصفحة"""
    setup_page_theme(page)
    return page

def save_theme_config(theme_name: str):
    """حفظ إعداد الثيم في ملف التكوين"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    if not config.has_section('Appearance'):
        config.add_section('Appearance')
    
    config.set('Appearance', 'theme', theme_name)
    
    with open('config.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile) 