⚠️ This project is for educational and portfolio purposes only. Commercial use is strictly prohibited.

# Attendance Management System

A comprehensive system for managing employee attendance and departure using modern technologies such as facial recognition and fingerprint, with a professional graphical interface that supports the Arabic language.

---

## 📸 Screenshots

A collection of system screenshots showcasing the interfaces and features:

| Image | Description |
|--------|------------|
| ![Screenshot 2025-06-25 161019](assets/images/Screenshot%202025-06-25%20161019.png) | Main system screen or dashboard |
| ![Screenshot 2025-06-24 224051](assets/images/Screenshot%202025-06-24%20224051.png) | Dashboard screen |
| ![Screenshot 2025-06-22 133542](assets/images/Screenshot%202025-06-22%20133542.png) | Fingerprint verification screen |
| ![Screenshot 2025-06-22 133530](assets/images/Screenshot%202025-06-22%20133530.png) | Identity confirmation screen |
| ![Screenshot 2025-06-22 133432](assets/images/Screenshot%202025-06-22%20133432.png) | Login screen |
| ![Screenshot 2025-06-22 133420](assets/images/Screenshot%202025-06-22%20133420.png) | Attendance page entry screen |
| ![Screenshot 2025-06-22 133238](assets/images/Screenshot%202025-06-22%20133238.png) | Reports management screen |
| ![Screenshot 2025-06-22 133225](assets/images/Screenshot%202025-06-22%20133225.png) | Reports management screen |
| ![Screenshot 2025-06-22 133155](assets/images/Screenshot%202025-06-22%20133155.png) | Logs management screen |
| ![Screenshot 2025-06-22 133110](assets/images/Screenshot%202025-06-22%20133110.png) | Employee management screen |
| ![Screenshot 2025-06-22 133037](assets/images/Screenshot%202025-06-22%20133037.png) | User management screen |
| ![Screenshot 2025-06-22 133020](assets/images/Screenshot%202025-06-22%20133020.png) | Users and permissions screen |
| ![Screenshot 2025-06-22 132925](assets/images/Screenshot%202025-06-22%20132925.png) | Advanced settings screen |
| ![Screenshot 2025-06-22 132904](assets/images/Screenshot%202025-06-22%20132904.png) | Manual attendance screen |

---

## Project Contents

```
AttendanceSystem/
│
├── main.py                  # Main entry point of the system
├── Home.py                  # Home page after login
├── login_page.py            # Login page
├── dashboard_ui.py          # Dashboard and statistics interface
├── attendance_page.py       # Attendance system (with camera/fingerprint)
├── manual_attendance_page.py# Manual attendance and departure
├── add_user_page.py         # User management and addition
├── managers_page.py         # Employee management (add/edit/delete)
├── logs_ui.py               # System logs display
├── reports_ui.py            # Attendance and departure reports and export
├── settings.py              # System settings (database, fingerprint, etc.)
├── theme_manager.py         # Theme and color management and application
├── db.py                    # All database operations
├── config.ini               # System and database settings file
├── requirements.txt         # Project dependencies
│
├── assets/                  # Assets (images, logos, fonts, animations)
│   ├── logo.png             # System logo
│   ├── icon.png             # Application icon
│   └── fonts/               # Embedded Arabic fonts
│
└── ...
```

---

## Main Features
- Attendance and departure registration via facial recognition or fingerprint.
- Easy management of employees, users, and their permissions.
- Detailed attendance and departure reports exportable to PDF/Excel.
- Flexible permissions system (Admin, Employee, Supervisor...)
- Full Arabic language support and modern graphical interface.
- Advanced settings (database, backup, fingerprint settings...)
- System activity log (Logs) with filtering and deletion options.
- Appearance customization (dark/light theme, Arabic fonts).

---

## How to Run

1. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Make sure to configure the database settings in `config.ini`.**
3. **Run the system:**
   ```bash
   python main.py
   ```

> **Note:**
> - A running PostgreSQL database is required.
> - Make sure the fonts and images files exist in the `assets` folder.
> - Some features (like fingerprint) require compatible devices, e.g., ZKTeco K40.

---

## License

🔒 License: CC BY-NC 4.0 — No commercial use allowed.

---

## Acknowledgments
This system was developed to facilitate attendance and departure management in organizations and companies, focusing on ease of use and Arabic language support.
<h2>Ahmed Abdullah Nasser Aldhuraibi</h2>
