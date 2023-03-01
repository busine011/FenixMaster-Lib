import time, json, re, random, os, configparser, requests, hashlib, sys, ctypes
from colorama import Fore, Style
import uiautomator2 as u2;
from xml.dom.minidom import parseString

class UpdateNeeded(Exception):
    pass

class NextStep(Exception):
    def __init__(self, *args: object) -> None:
        if not __version__ == "!launcher_version!":
            raise UpdateNeeded()

        Helper.check_sign("!launcher_hash!")
        super().__init__(*args)
    pass

class Config:
    def get(segment, key, value = False):
        config = configparser.ConfigParser()
        config.read("config.ini")

        if key in config[segment]:
            return config[segment][key]
        else:
            return value

class Helper:
    def log(text: str, color: Fore = Fore.CYAN):
        print(f"{color}[*]{Style.RESET_ALL} {text}")

    def clear_log():
        os.system('cls')

    def read_file(filename):
        if os.path.exists(filename):
            return open(filename).read()

        return False

    def write_file(file, text):
        f = open(file, "w", encoding="utf-8")
        f.write(text)
        f.close()

    def get_devices():
        devices = Helper.read_file('devices.ini').split("\n")

        if len(devices) > 1:
            for i, device in enumerate(devices):
                c = i+1
                print(f"{Style.BRIGHT}{Fore.CYAN}[{Fore.RED}{c}{Fore.CYAN}] {device}")

            select = input(f"\n[{Fore.RED}>{Fore.CYAN}] Select Device: {Style.RESET_ALL}")
            return devices[int(select)-1]

        elif len(devices) == 1:
            return devices[0]

        return False

    def setup_device(d: u2.Device):
        d.shell("appops set com.facebook.orca SYSTEM_ALERT_WINDOW ignore")
        d.shell("appops set com.facebook.orca POST_NOTIFICATION ignore")
        d.shell("appops set com.facebook.spam SYSTEM_ALERT_WINDOW ignore")
        d.shell("appops set com.facebook.spam POST_NOTIFICATION ignore")
        d.shell("appops set com.facebook.katana POST_NOTIFICATION ignore")
        d.shell("settings put global heads_up_notifications_enabled 0") 
        d.shell("settings put secure show_ime_with_hard_keyboard 1")
        d.set_fastinput_ime(True)

    def connect_device():
        device = Helper.get_devices()
        if not device:
            raise Exception('Devices List Empty')

        d = u2.connect(device)
        if not d.uiautomator.running():
            Helper.clear_log()
            Helper.log("Conectando con el dispositivo")

        Helper.setup_device(d)
        os.system("mode con: cols=40 lines=10")
        ctypes.windll.kernel32.SetConsoleTitleW(f'{device} | Messenger Bot')        
        return d

    def check_sign(hash):
        h = hashlib.sha256()
        h.update("!seed!".encode())
        with open(sys.argv[0], 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                h.update(chunk)
        if not h.hexdigest() == hash:
            raise Exception('https solid error')

class Profile:
    def get():
        if Config.get('PROFILE', 'API') == "list":
            profiles = Helper.read_file('profiles.ini')
            if not profiles:
                raise Exception('Profile List File Not Found')

            profiles = profiles.split("\n")
            if len(profiles) < 1:
                raise Exception('Profile List Empty')

            profile = profiles.pop().split(":")
            if len(profile) > 1:
                Helper.write_file('profiles.ini', "\n".join(profiles))
                return Profile(profile[0], profile[1])

        else:
            res = requests.get(Config.get('PROFILE', 'API'))

            if not res.status_code == 200:
                raise Exception('Profile API Error')

            profile = res.json()
            if type(profile) is list:
                profile = profile[0]

            return Profile(
                profile[Config.get('PROFILE', 'USERNAME_KEY', 'username')],
                profile[Config.get('PROFILE', 'PASSWORD_KEY', 'password')]
                )

        return False

    def mona():
        profiles = Helper.read_file('monas.ini')
        if not profiles:
            raise Exception('Mona List File Not Found')

        profiles = profiles.split("\n")
        if len(profiles) < 1:
            raise Exception('Profile List Empty')

        profile = profiles[random.randint(0, len(profiles)-1)].split(':')
        return Profile(profile[0], profile[1])

    def chat():
        profiles = Helper.read_file('chats.ini')
        if not profiles:
            raise Exception('Chat List File Not Found')

        profiles = profiles.split("\n")
        if len(profiles) < 1:
            raise Exception('Chat List Empty')

        return profiles[random.randint(0, len(profiles)-1)]  
        
    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password

class Permalink:
    def get():
        r = requests.get( Config.get('MESSAGE', 'API') )
        if(r.status_code == 200):
            mensaje = r.json()
            if type(mensaje) is dict:
                return Permalink(mensaje[ Config.get('MESSAGE', 'KEY') ])

            elif type(mensaje) is list:
                return Permalink(mensaje[0][ Config.get('MESSAGE', 'KEY') ])

    def __init__(self, link) -> None:
        self.link = link

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
    c_user: str
    chat_user: str
    message_to_send: str

    def setup_watcher(d: u2.Device):
        d.watcher("CALL").when("//*[@text='ANSWER']").when("//*[@text='DECLINE']").click()
        d.watcher("APP_CLOSE").when("//*[@text='Close app']").when("//*[@text='Wait']").click()
        d.watcher.start(0)

    def switch(d: u2.Device):
        d.app_stop('com.facebook.spam')
        owner = d.shell("stat -c '%U' /data/data/com.facebook.spam/").output
        owner = owner.strip()

        d.shell("su -c 'rm -rf /data/data/com.facebook.spam/*' ")
        d.shell("su -c 'cp -RFp /data/data/com.facebook.orca/app_light_prefs /data/data/com.facebook.spam/' ")
        d.shell(f"su -c 'chown -R {owner}:{owner} /data/data/com.facebook.spam/app_light_prefs' ")

        d.shell(f"su -c 'mv /data/data/com.facebook.spam/app_light_prefs/com.facebook.orca /data/data/com.facebook.spam/app_light_prefs/com.facebook.spam' ")
        d.shell(f"su -c 'mv /data/data/com.facebook.spam/app_light_prefs/com.facebook.orca /data/data/com.facebook.spam/app_light_prefs/com.facebook.spam' ")

        d.shell(f"su -c 'am start -S com.facebook.spam/com.facebook.orca.auth.StartScreenActivity' ")

    def __init__(self, d: u2.Device, package: str = 'com.facebook.orca') -> None:
        username_input = d.xpath("//*[@content-desc='Phone Number or Email'] | //*[@content-desc='Phone number or email']")
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
            if True:
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
    # Static Functions
    def setup_watcher(d: u2.Device):
        d.watcher("CALL").when("//*[@text='ANSWER']").when("//*[@text='DECLINE']").click()
        d.watcher("APP_CLOSE").when("//*[@text='Close app']").when("//*[@text='Wait']").click()
        d.watcher("FB_PERMISSION").when("//*[@content-desc='OK']").when("//*[@content-desc='NOT NOW']").click()
        d.watcher.start(0)

    # Public Functions
    def __init__(self, d: u2.Device, package: str = 'com.facebook.katana') -> None:
        username_input = d.xpath("//*[@content-desc='Username'] | //*[@content-desc='Mobile number or email']")
        password_input = d.xpath("//*[@password='true']")
        login_btn = d.xpath("//*[@content-desc='Log In'] | //*[@content-desc='Log in']")
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

    def login(self, username: str, password: str) -> None:
        if self.username_input.exists and self.password_input.exists:
            if self.d(description="Mobile number or email").exists:
                self.username_input.set_text(username)
            else:
                while not self.username_input.get_text() == username:
                    self.username_input.set_text(username)

            if hasattr(self.password_input, "clear_text"):
                self.password_input.clear_text()
            self.password_input.set_text(password)

            self.login_btn.click()
            self.d.sleep(1)

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

raise NextStep("start")