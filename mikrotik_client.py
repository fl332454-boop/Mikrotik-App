import routeros_api

class MikrotikClient:
    def __init__(self):
        self.connection = None
        self.api = None
        self.host = ""
        self.username = ""
        self.password = ""

    def connect(self, host, username, password):
        try:
            self.host = host
            self.username = username
            self.password = password
            
            # Connect to RouterOS using plaintext login (required for v6.43+ without SSL)
            self.connection = routeros_api.RouterOsApiPool(
                host, 
                username=username, 
                password=password, 
                plaintext_login=True
            )
            self.api = self.connection.get_api()
            return True, "تم الاتصال بنجاح"
        except Exception as e:
            return False, f"خطأ في الاتصال: {str(e)}"

    def disconnect(self):
        if self.connection:
            self.connection.disconnect()
            self.connection = None
            self.api = None

    def get_hotspot_users(self):
        if not self.api:
            return []
        try:
            resource = self.api.get_resource('/ip/hotspot/user')
            return resource.get()
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []

    def add_hotspot_user(self, name, password, profile="default"):
        if not self.api:
            return False, "غير متصل بالراوتر"
        try:
            resource = self.api.get_resource('/ip/hotspot/user')
            resource.add(name=name, password=password, profile=profile)
            return True, "تمت إضافة المستخدم بنجاح"
        except Exception as e:
            return False, f"خطأ: {str(e)}"

    def remove_hotspot_user(self, user_id):
        if not self.api:
            return False, "غير متصل بالراوتر"
        try:
            resource = self.api.get_resource('/ip/hotspot/user')
            resource.remove(id=user_id)
            return True, "تم الحذف بنجاح"
        except Exception as e:
            return False, f"خطأ: {str(e)}"

    def get_system_resource(self):
        if not self.api:
            return {}
        try:
            resource = self.api.get_resource('/system/resource')
            return resource.get()[0]
        except Exception as e:
            return {}

    def get_active_users(self):
        if not self.api:
            return []
        try:
            resource = self.api.get_resource('/ip/hotspot/active')
            return resource.get()
        except Exception as e:
            return []
