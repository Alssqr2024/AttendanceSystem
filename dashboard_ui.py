import flet as ft
from db import get_daily_stats, get_logs
from datetime import datetime

class DashboardPage(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.spacing = 25
        self.scroll = ft.ScrollMode.ADAPTIVE
        self.padding = ft.padding.all(25)

        # ألوان احترافية
        PRIMARY_COLOR = "#1E3A8A"
        SECONDARY_COLOR = "#3B82F6"
        SUCCESS_COLOR = "#059669"
        DANGER_COLOR = "#DC2626"
        WARNING_COLOR = "#D97706"
        INFO_COLOR = "#0891B2"
        LIGHT_BG = "#F8FAFC"
        CARD_BG = "#FFFFFF"

        def create_stats_card(title, value, icon, gradient_colors, trend=None, trend_value=None):
            return ft.Container(
                height=140,
                padding=20,
                border_radius=16,
                bgcolor=CARD_BG,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=15,
                    color="#1A000000",
                    offset=ft.Offset(0, 4)
                ),
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Container(
                                    width=50,
                                    height=50,
                                    border_radius=12,
                                    gradient=ft.LinearGradient(
                                        begin=ft.alignment.top_left,
                                        end=ft.alignment.bottom_right,
                                        colors=gradient_colors
                                    ),
                                    content=ft.Icon(icon, color=ft.Colors.WHITE, size=24),
                                    alignment=ft.alignment.center
                                ),
                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                    spacing=4,
                                    controls=[
                                        ft.Text(title, size=14, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                                        ft.Text(value, size=32, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD)
                                    ]
                                )
                            ]
                        ),
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.TRENDING_UP if trend == "up" else ft.Icons.TRENDING_DOWN,
                                    color=SUCCESS_COLOR if trend == "up" else DANGER_COLOR,
                                    size=16
                                ),
                                ft.Text(
                                    f"{trend_value}% من الأمس" if trend_value else "مقارنة بالأمس",
                                    size=12,
                                    color=ft.Colors.GREY_500,
                                    weight=ft.FontWeight.W_500
                                )
                            ],
                            spacing=6
                        ) if trend else ft.Container(height=0)
                    ]
                )
            )

        def create_activity_item(time, activity, details, icon, color):
            return ft.Container(
                padding=ft.padding.all(16),
                border_radius=12,
                bgcolor=CARD_BG,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=8,
                    color="#1A000000",
                    offset=ft.Offset(0, 2)
                ),
                content=ft.Row(
                    spacing=16,
                    controls=[
                        ft.Container(
                            width=40,
                            height=40,
                            border_radius=10,
                            bgcolor=color,
                            content=ft.Icon(icon, color=ft.Colors.WHITE, size=20),
                            alignment=ft.alignment.center
                        ),
                        ft.Column(
                            expand=True,
                            spacing=4,
                            controls=[
                                ft.Text(activity, size=16, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK),
                                ft.Text(details, size=14, color=ft.Colors.GREY_600)
                            ]
                        ),
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            spacing=2,
                            controls=[
                                ft.Text(time.split('\n')[0], size=11, color=ft.Colors.GREY_500, weight=ft.FontWeight.W_500),
                                ft.Text(time.split('\n')[1] if '\n' in time else "", size=11, color=ft.Colors.GREY_400, weight=ft.FontWeight.W_400)
                            ]
                        )
                    ]
                )
            )

        def update_stats():
            present, absent, total = get_daily_stats()
            present_card.content.controls[0].controls[1].controls[1].value = str(present)
            absent_card.content.controls[0].controls[1].controls[1].value = str(absent)
            total_employees_card.content.controls[0].controls[1].controls[1].value = str(total)

            if total > 0:
                present_percentage = (present / total) * 100
                absent_percentage = (absent / total) * 100
                pie_chart.sections[0].value = present_percentage
                pie_chart.sections[0].title = f"{present_percentage:.1f}%"
                pie_chart.sections[1].value = absent_percentage
                pie_chart.sections[1].title = f"{absent_percentage:.1f}%"
            else:
                pie_chart.sections[0].value = 0
                pie_chart.sections[0].title = "0%"
                pie_chart.sections[1].value = 100
                pie_chart.sections[1].title = "0%"
                pie_chart.sections[1].color = ft.Colors.GREY_300
            self.page.update()

        def load_recent_activities():
            logs = get_logs()[:10]
            activities_column.controls.clear()
            activities_column.controls.append(
                ft.Container(
                    padding=ft.padding.only(bottom=16),
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.HISTORY, color=PRIMARY_COLOR, size=24),
                            ft.Text("آخر الأنشطة", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
                        ],
                        spacing=12
                    )
                )
            )
            for log in logs:
                if "حضور" in log[2]:
                    icon = ft.Icons.LOGIN
                    color = SUCCESS_COLOR
                elif "انصراف" in log[2]:
                    icon = ft.Icons.LOGOUT
                    color = WARNING_COLOR
                elif "تسجيل" in log[2]:
                    icon = ft.Icons.PERSON_ADD
                    color = INFO_COLOR
                else:
                    icon = ft.Icons.INFO
                    color = PRIMARY_COLOR
                
                # تنسيق التاريخ والوقت
                timestamp = log[3]
                if isinstance(timestamp, datetime):
                    date_str = timestamp.strftime("%Y/%m/%d")
                    time_str = timestamp.strftime("%H:%M")
                else:
                    date_str = "غير محدد"
                    time_str = "غير محدد"
                
                activities_column.controls.append(
                    create_activity_item(
                        f"{date_str}\n{time_str}",
                        log[2],
                        log[1],
                        icon,
                        color
                    )
                )
            if not logs:
                activities_column.controls.append(
                    ft.Container(
                        padding=ft.padding.all(40),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.HISTORY, color=ft.Colors.GREY_400, size=48),
                                ft.Text("لا توجد أنشطة حديثة", size=16, color=ft.Colors.GREY_500, weight=ft.FontWeight.W_500)
                            ],
                            spacing=12
                        )
                    )
                )
            self.page.update()

        present_card = create_stats_card("حضور اليوم", "0", ft.Icons.CHECK_CIRCLE_OUTLINED, [SUCCESS_COLOR, "#10B981"], "up", 5.2)
        absent_card = create_stats_card("غياب اليوم", "0", ft.Icons.HIGHLIGHT_OFF, [DANGER_COLOR, "#EF4444"], "down", 2.1)
        total_employees_card = create_stats_card("إجمالي الموظفين", "0", ft.Icons.PEOPLE_OUTLINE, [PRIMARY_COLOR, SECONDARY_COLOR])

        pie_chart = ft.PieChart(
            sections=[
                ft.PieChartSection(0, title="0%", color=SUCCESS_COLOR, radius=60, title_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=14)),
                ft.PieChartSection(0, title="0%", color=DANGER_COLOR, radius=60, title_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=14)),
            ],
            center_space_radius=50,
            sections_space=2,
            expand=True
        )

        legend = ft.Container(
            padding=ft.padding.all(16),
            border_radius=12,
            bgcolor=LIGHT_BG,
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(width=16, height=16, bgcolor=SUCCESS_COLOR, border_radius=4),
                            ft.Text("حضور", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK)
                        ],
                        spacing=8
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(width=16, height=16, bgcolor=DANGER_COLOR, border_radius=4),
                            ft.Text("غياب", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK)
                        ],
                        spacing=8
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=32
            )
        )

        header_section = ft.Container(
            padding=ft.padding.only(bottom=20),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text("لوحة التحكم", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                    ft.Text(f"آخر تحديث: {datetime.now().strftime('%Y/%m/%d - %A %H:%M')}", size=14, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500)
                ]
            )
        )

        stats_section = ft.ResponsiveRow(
            controls=[
                ft.Column(col={"sm": 12, "md": 4}, controls=[present_card]),
                ft.Column(col={"sm": 12, "md": 4}, controls=[absent_card]),
                ft.Column(col={"sm": 12, "md": 4}, controls=[total_employees_card]),
            ],
            spacing=20,
            run_spacing=20
        )

        chart_section = ft.Container(
            padding=ft.padding.all(24),
            border_radius=16,
            bgcolor=CARD_BG,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color="#1A000000",
                offset=ft.Offset(0, 4)
            ),
            content=ft.Column(
                spacing=20,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PIE_CHART, color=PRIMARY_COLOR, size=24),
                            ft.Text("نسبة الحضور والغياب", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
                        ],
                        spacing=12
                    ),
                    ft.Container(content=pie_chart, height=200, alignment=ft.alignment.center),
                    legend
                ]
            )
        )

        activities_column = ft.Column(spacing=12, expand=True, scroll=ft.ScrollMode.ADAPTIVE)

        self.controls = [
            header_section,
            stats_section,
            ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        col={"sm": 12, "lg": 7},
                        controls=[
                            ft.Container(
                                height=370,
                                padding=ft.padding.all(24),
                                border_radius=16,
                                bgcolor=CARD_BG,
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=15,
                                    color="#1A000000",
                                    offset=ft.Offset(0, 4)
                                ),
                                content=activities_column
                            )
                        ]
                    ),
                    ft.Column(col={"sm": 12, "lg": 5}, controls=[chart_section])
                ],
                spacing=20,
                run_spacing=20
            )
        ]
        update_stats()
        load_recent_activities() 

# def main(page: ft.Page):
#     page.title = "Dashboard"
#     page.theme_mode = ft.ThemeMode.LIGHT
#     page.theme = ft.Theme(
#         color_scheme=ft.ColorScheme(
#             primary="#1976D2",
#             secondary="#388E3C",
#             surface="#FFFFFF",
#             background="#F5F5F5",
#         )
#     )
#     page.add(DashboardPage(page))
# ft.app(target=main)