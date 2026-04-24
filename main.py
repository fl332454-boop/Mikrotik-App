import flet as ft
import certifi
import urllib3
import idna
import charset_normalizer
from mikrotik_client import MikrotikClient


def main(page: ft.Page):
    page.title = "مدير الهوت سبوت - مايكروتك"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    # Setup fonts for Arabic
    page.fonts = {
        "Cairo": "https://github.com/google/fonts/raw/main/ofl/cairo/Cairo-Regular.ttf",
        "Cairo-Bold": "https://github.com/google/fonts/raw/main/ofl/cairo/Cairo-Bold.ttf"
    }
    page.theme = ft.Theme(font_family="Cairo")

    client = MikrotikClient()

    # --- UI Components ---
    
    # 1. Login View
    ip_input = ft.TextField(label="IP الراوتر (مثال: 192.168.88.1)", width=300, text_align=ft.TextAlign.RIGHT)
    user_input = ft.TextField(label="اسم المستخدم", width=300, text_align=ft.TextAlign.RIGHT)
    pass_input = ft.TextField(label="كلمة المرور", password=True, can_reveal_password=True, width=300, text_align=ft.TextAlign.RIGHT)
    login_status = ft.Text(value="", color=ft.colors.RED)
    
    # 2. Dashboard View components
    total_users_text = ft.Text(size=20, weight=ft.FontWeight.BOLD)
    active_users_text = ft.Text(size=20, weight=ft.FontWeight.BOLD)
    cpu_text = ft.Text(size=20, weight=ft.FontWeight.BOLD)
    
    # 3. Users View components
    users_list_view = ft.ListView(expand=1, spacing=10, padding=20)
    
    # Add User Form components
    new_user_name = ft.TextField(label="اسم المشترك", text_align=ft.TextAlign.RIGHT)
    new_user_pass = ft.TextField(label="كلمة المرور", text_align=ft.TextAlign.RIGHT)

    # --- Functions ---

    def show_snack(message, color=ft.colors.GREEN):
        page.snack_bar = ft.SnackBar(ft.Text(message, color=ft.colors.WHITE, text_align=ft.TextAlign.CENTER), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def go_to_login(e=None):
        page.views.clear()
        page.views.append(login_view)
        page.update()

    def go_to_dashboard(e=None):
        # Fetch stats before showing dashboard
        users = client.get_hotspot_users()
        active = client.get_active_users()
        sys_res = client.get_system_resource()
        
        total_users_text.value = f"إجمالي المشتركين: {len(users)}"
        active_users_text.value = f"المشتركين النشطين: {len(active)}"
        cpu_text.value = f"استهلاك المعالج: {sys_res.get('cpu-load', '0')}%"
        
        page.views.clear()
        page.views.append(dashboard_view)
        page.update()

    def go_to_users(e=None):
        refresh_users_list()
        page.views.clear()
        page.views.append(users_view)
        page.update()

    def do_login(e):
        login_btn.disabled = True
        page.update()
        success, msg = client.connect(ip_input.value, user_input.value, pass_input.value)
        login_btn.disabled = False
        if success:
            show_snack("تم الاتصال بنجاح!", ft.colors.GREEN)
            go_to_dashboard()
        else:
            login_status.value = msg
        page.update()

    def do_logout(e):
        client.disconnect()
        go_to_login()

    def delete_user(user_id):
        success, msg = client.remove_hotspot_user(user_id)
        if success:
            show_snack("تم الحذف بنجاح")
            refresh_users_list()
        else:
            show_snack(msg, ft.colors.RED)

    def refresh_users_list():
        users = client.get_hotspot_users()
        users_list_view.controls.clear()
        for u in users:
            uid = u.get('.id')
            uname = u.get('name', 'Unknown')
            upass = u.get('password', '***')
            profile = u.get('profile', 'default')
            
            card = ft.Card(
                content=ft.Container(
                    padding=10,
                    content=ft.Row(
                        [
                            ft.IconButton(icon=ft.icons.DELETE, icon_color=ft.colors.RED, on_click=lambda e, uid=uid: delete_user(uid)),
                            ft.Column(
                                [
                                    ft.Text(uname, size=18, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"الباسورد: {upass} | البروفايل: {profile}", size=14, color=ft.colors.GREY_400),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                expand=True
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                )
            )
            users_list_view.controls.append(card)
        page.update()

    def close_add_dlg(e):
        add_user_dlg.open = False
        page.update()

    def do_add_user(e):
        if not new_user_name.value or not new_user_pass.value:
            show_snack("يرجى إدخال الاسم وكلمة المرور", ft.colors.RED)
            return
        
        success, msg = client.add_hotspot_user(new_user_name.value, new_user_pass.value)
        if success:
            show_snack(msg)
            close_add_dlg(None)
            new_user_name.value = ""
            new_user_pass.value = ""
            refresh_users_list()
        else:
            show_snack(msg, ft.colors.RED)

    add_user_dlg = ft.AlertDialog(
        title=ft.Text("إضافة مشترك جديد", text_align=ft.TextAlign.RIGHT),
        content=ft.Column([new_user_name, new_user_pass], tight=True),
        actions=[
            ft.TextButton("إلغاء", on_click=close_add_dlg),
            ft.ElevatedButton("إضافة", on_click=do_add_user, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_add_user(e):
        page.dialog = add_user_dlg
        add_user_dlg.open = True
        page.update()

    # --- Views ---
    login_btn = ft.ElevatedButton("تسجيل الدخول", icon=ft.icons.LOGIN, on_click=do_login, width=300)

    login_view = ft.View(
        "/",
        [
            ft.Column(
                [
                    ft.Icon(ft.icons.WIFI, size=80, color=ft.colors.BLUE),
                    ft.Text("مدير المايكروتك", size=30, weight=ft.FontWeight.BOLD),
                    ft.Text("سجل الدخول للراوتر لإدارة الهوت سبوت", color=ft.colors.GREY_400),
                    ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                    ip_input,
                    user_input,
                    pass_input,
                    login_status,
                    login_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
    )

    dashboard_view = ft.View(
        "/dashboard",
        [
            ft.AppBar(title=ft.Text("الرئيسية"), bgcolor=ft.colors.SURFACE_VARIANT, actions=[
                ft.IconButton(ft.icons.LOGOUT, on_click=do_logout)
            ]),
            ft.Container(
                padding=20,
                content=ft.Column(
                    [
                        ft.Card(
                            content=ft.Container(
                                padding=20,
                                content=ft.Column([
                                    ft.Icon(ft.icons.PEOPLE, size=40, color=ft.colors.BLUE),
                                    total_users_text
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                            ),
                        ),
                        ft.Card(
                            content=ft.Container(
                                padding=20,
                                content=ft.Column([
                                    ft.Icon(ft.icons.WIFI_TETHERING, size=40, color=ft.colors.GREEN),
                                    active_users_text
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                            )
                        ),
                        ft.Card(
                            content=ft.Container(
                                padding=20,
                                content=ft.Column([
                                    ft.Icon(ft.icons.MEMORY, size=40, color=ft.colors.ORANGE),
                                    cpu_text
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                            )
                        ),
                        ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                        ft.ElevatedButton("إدارة المشتركين", icon=ft.icons.MANAGE_ACCOUNTS, on_click=go_to_users, width=200, height=50)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=True
                )
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    users_view = ft.View(
        "/users",
        [
            ft.AppBar(
                title=ft.Text("المشتركين"), 
                bgcolor=ft.colors.SURFACE_VARIANT,
                leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=go_to_dashboard)
            ),
            users_list_view,
            ft.FloatingActionButton(icon=ft.icons.ADD, on_click=open_add_user, bgcolor=ft.colors.BLUE)
        ]
    )

    # Initial view
    go_to_login()

if __name__ == "__main__":
    ft.app(target=main)
