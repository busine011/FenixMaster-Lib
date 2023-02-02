import time, json, re, random
import uiautomator2 as u2;
from xml.dom.minidom import parseString

class Automator:
    d: u2.Device
    package: str
    username_input: u2.UiObject
    password_input: u2.UiObject
    login_btn: u2.UiObject
    def __init__(self, d: u2.Device, package: str, username_input: u2.UiObject, password_input: u2.UiObject, login_btn: u2.UiObject) -> None:
        self.d = d
        self.package = package
        self.username_input = username_input
        self.password_input = password_input
        self.login_btn = login_btn
        pass

    def start(self, activity: str = None):
        if activity == None:
            self.d.app_start(self.package)
        else:
            self.d.shell(f"su -c 'am start -S {self.package}/{activity}' ")

    def close(self):
        self.d.app_stop(self.package)

    def clear(self):
        self.d.app_clear(self.package)

    def login(self, username: str, password: str) -> None:
        if self.username_input.exists and self.password_input.exists:
            while not self.username_input.get_text() == username:
                self.username_input.set_text(username)

            if hasattr(self.password_input, "clear_text"):
                self.password_input.clear_text()
            self.password_input.set_text(password)

            self.login_btn.click()
            self.d.sleep(1)

    def wait(self, object: u2.UiObject) -> bool:
        while object.exists:
            self.d.sleep(1)
        else:
            return True
        
    def wait_load(self) -> bool:
        return self.wait(self.d(className='android.widget.ProgressBar'))

class Messenger(Automator):
    chat_user: str
    message_to_send: str
    def __init__(self, d: u2.Device, package: str = 'com.facebook.orca') -> None:
        username_input = d(description='Phone Number or Email')
        password_input = d(description='Password')
        login_btn = d(description='LOG IN')
        super().__init__(d, package, username_input, password_input, login_btn)

    def clear(self):
        self.d.shell("su -c 'rm -rf /data/data/com.facebook.orca/app_light_prefs/com.facebook.orca/authentication /data/data/com.facebook.orca/app_light_prefs/com.facebook.orca/logged_in_*' ")

    def open_login(self):
        self.clear()
        self.start('com.facebook.messenger.neue.MainActivity')

    def is_logged(self):
        login_file = self.d.shell("su -c 'cat /data/data/com.facebook.orca/app_light_prefs/com.facebook.orca/authentication'")
        if 'c_user' in login_file.output:
            authentication_json = json.loads(re.search("\[.*\]", login_file.output).group())
            for item in authentication_json:
                if item['name'] == 'c_user':
                    self.c_user = item['value']

            return True
        else:
            return False

    def open_chat(self, user: str):
        self.chat_user = user
        
        # self.close()
        self.d.open_url(f'https://m.me/{self.chat_user}')

    def send_message(self, message: str):
        self.message_to_send = message
        
        self.d.set_fastinput_ime(True)
        self.d(text="Ok").click_gone()
        self.d(text='Aa').click_exists(timeout=10)
        if self.wait(self.d(text="Type a message…")):
            self.d.send_keys(self.message_to_send)

        self.d(description='Send').click_exists(timeout=10)

    def resend_message(self, limit: int = 100, interval: float = 1):
        count = 0
        resolution = self.d.window_size()        
        while count < limit:
            if self.d.wait_activity("com.facebook.messaging.sharing.broadcastflow.BroadcastFlowActivity", timeout=60):
                sent_btns = self.d.xpath("//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[*]/android.view.ViewGroup[1]/android.view.ViewGroup[1][@content-desc=\"\"]").all()
                if len(sent_btns) > 0:
                    for elem in sent_btns:
                        if count < limit:
                            interval = interval*random.uniform(0.1, 1)
                            time.sleep(interval)
                            
                            pos = elem.center()
                            posX = pos[0]+random.randint(-10, 10)
                            posY = pos[1]+random.randint(-10, 10)
                            self.d.click(posX, posY)
                            count += 1

                    print(f"{count} Mensajes Enviados")
                    self.d.swipe((resolution[0] / 2), (resolution[1]/1.3), (resolution[0] / 2), 0)
                    time.sleep(1)
                else:
                    break

class Facebook(Automator):
    def __init__(self, d: u2.Device, package: str = 'com.facebook.katana') -> None:
        username_input = d(description='Username')
        password_input = d(description='Password')
        login_btn = d(description='Log In')
        super().__init__(d, package, username_input, password_input, login_btn)

    def clear(self):
        self.close()
        self.d.shell("su -c 'am start com.facebook.katana/com.facebook.katana.LogoutActivity'")

    def open_login(self):
        self.clear()
        if self.wait_load():
            while not self.username_input.exists and not self.password_input.exists:
                self.d(description="Close").click_exists()
                self.d(text="Log Into Another Account").click_exists()

    def is_logged(self):
        if self.wait_load():
            if not ( self.d(text='OK').exists() or self.d(text='TRY AGAIN').exists() or self.d(description='Back').exists() ):
                self.d.sleep(3)

            self.d.sleep(1)
            
            
        login_file = self.d.shell("su -c 'cat /data/data/com.facebook.katana/app_light_prefs/com.facebook.katana/authentication'")
        if 'c_user' in login_file.output:
            authentication_json = json.loads(re.search("\[.*\]", login_file.output).group())
            for item in authentication_json:
                if item['name'] == 'c_user':
                    return item['value']
        else:
            return False

class Lite(Automator):
    def __init__(self, d: u2.Device, package: str = 'com.facebook.lite') -> None:
        username_input = d(className="android.widget.MultiAutoCompleteTextView")[0]
        password_input = d(className="android.widget.MultiAutoCompleteTextView")[1]
        login_btn = d.xpath('//android.view.ViewGroup[2]/android.view.View[1]')
        super().__init__(d, package, username_input, password_input, login_btn)

    def is_logged(self):
        login_file = self.d.shell('cat /data/data/com.facebook.lite/shared_prefs/com.facebook.lite.xml')
        if not 'No such file or directory' in login_file.output:
            dom = parseString(login_file.output)
            elements = dom.getElementsByTagName('long')
            for element in elements:
                if element.getAttribute('name') == 'current_user_id':
                    if not element.getAttribute('value') == '0':
                        return element.getAttribute('value')

        return False

    def open_login(self):
        self.clear()
        self.d.shell("pm grant com.facebook.lite android.permission.READ_CONTACTS")

        self.start()
        if self.wait_load():
            while not self.username_input.exists and not self.password_input.exists:
                logins_btn = self.d.xpath('//android.view.ViewGroup[1]/android.view.ViewGroup[2]').all()
                if len(logins_btn) > 0:
                    logins_btn[-1].click()