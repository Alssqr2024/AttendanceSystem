⚠️ This project is for educational and portfolio purposes only. Commercial use is strictly prohibited.

# نظام إدارة الحضور والانصراف (Attendance Management System)

نظام متكامل لإدارة حضور وانصراف الموظفين باستخدام تقنيات حديثة مثل التعرف على الوجه والبصمة، مع واجهة رسومية احترافية تدعم اللغة العربية.

---

## 📸 Screenshots

A collection of system screenshots illustrating the interfaces and features:

| Image | Description |
|--------|------------|
| ![Screenshot 2025-06-25 161019](assets/images/Screenshot%202025-06-25%20161019.png) | Main system screen or dashboard |
| ![Screenshot 2025-06-24 224051](assets/images/Screenshot%202025-06-24%20224051.png) | Dashboard screen |
| ![Screenshot 2025-06-22 133542](assets/images/Screenshot%202025-06-22%20133542.png) | Fingerprint verification screen |
| ![Screenshot 2025-06-22 133530](assets/images/Screenshot%202025-06-22%20133530.png) | Identity confirmation screen |
| ![Screenshot 2025-06-22 133432](assets/images/Screenshot%202025-06-22%20133432.png) | Login screen |
| ![Screenshot 2025-06-22 133420](assets/images/Screenshot%202025-06-22%20133420.png) | Attendance page entry screen |
| ![Screenshot 2025-06-22 133238](assets/images/Screenshot%202025-06-22%20133238.png) | Reports management screen |
| ![Screenshot 2025-06-22 133225](assets/images/Screenshot%202025-06-22%20133225.png) | Reports administration screen |
| ![Screenshot 2025-06-22 133155](assets/images/Screenshot%202025-06-22%20133155.png) | Logs management screen |
| ![Screenshot 2025-06-22 133110](assets/images/Screenshot%202025-06-22%20133110.png) | Employee management screen |
| ![Screenshot 2025-06-22 133037](assets/images/Screenshot%202025-06-22%20133037.png) | User management screen |
| ![Screenshot 2025-06-22 133020](assets/images/Screenshot%202025-06-22%20133020.png) | Users and permissions screen |
| ![Screenshot 2025-06-22 132925](assets/images/Screenshot%202025-06-22%20132925.png) | Advanced settings screen |
| ![Screenshot 2025-06-22 132904](assets/images/Screenshot%202025-06-22%20132904.png) | Manual attendance screen |

---

## محتويات المشروع

```
AttendanceSystem/
│
├── main.py                  # نقطة تشغيل النظام الرئيسية
├── Home.py                  # الصفحة الرئيسية بعد تسجيل الدخول
├── login_page.py            # صفحة تسجيل الدخول
├── dashboard_ui.py          # واجهة لوحة التحكم والإحصائيات
├── attendance_page.py       # نظام الحضور والانصراف (بكاميرا/بصمة)
├── manual_attendance_page.py# الحضور والانصراف اليدوي
├── add_user_page.py         # إدارة وإضافة المستخدمين
├── managers_page.py         # إدارة الموظفين (إضافة/تعديل/حذف)
├── logs_ui.py               # عرض سجلات النظام
├── reports_ui.py            # تقارير الحضور والانصراف وتصديرها
├── settings.py              # إعدادات النظام (قاعدة البيانات، البصمة، إلخ)
├── theme_manager.py         # إدارة وتطبيق الثيمات والألوان
├── db.py                    # جميع عمليات قاعدة البيانات
├── config.ini               # ملف إعدادات النظام وقاعدة البيانات
├── requirements.txt         # المتطلبات البرمجية للمشروع
│
├── assets/                  # الموارد (صور، شعارات، خطوط، رسوم متحركة)
│   ├── logo.png             # شعار النظام
│   ├── icon.png             # أيقونة التطبيق
│   └── fonts/               # خطوط عربية مدمجة
│
└── ...
```

---

## المميزات الرئيسية
- تسجيل الحضور والانصراف عبر التعرف على الوجه أو البصمة.
- إدارة الموظفين والمستخدمين وصلاحياتهم بسهولة.
- تقارير حضور وانصراف مفصلة وقابلة للتصدير PDF/Excel.
- نظام صلاحيات مرن (مدير، موظف، مشرف...)
- دعم كامل للغة العربية وواجهة رسومية عصرية.
- إعدادات متقدمة (قاعدة بيانات، نسخ احتياطي، إعدادات البصمة...)
- سجل نشاطات النظام (Logs) مع إمكانية التصفية والحذف.
- تخصيص المظهر (ثيم داكن/فاتح، خطوط عربية).

---

## طريقة التشغيل

1. **تثبيت المتطلبات:**
   ```bash
   pip install -r requirements.txt
   ```
2. **تأكد من ضبط إعدادات قاعدة البيانات في `config.ini`.**
3. **تشغيل النظام:**
   ```bash
   python main.py
   ```

> **ملاحظة:**
> - يجب توفر قاعدة بيانات PostgreSQL مفعلة.
> - تأكد من وجود ملفات الخطوط والصور في مجلد `assets`.
> - بعض الميزات (مثل البصمة) تتطلب أجهزة متوافقة.ZKTeco K40

---

## License

🔒 License: CC BY-NC 4.0 — No commercial use allowed.

---

## شكر وتقدير
تم تطوير هذا النظام لتسهيل إدارة الحضور والانصراف في المؤسسات والشركات، مع التركيز على سهولة الاستخدام ودعم اللغة العربية.
<h2>Ahmed Abdullah Nasser Aldhuraibi</h2>
