import kivy
kivy.require('2.3.1')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import *
from kivy.uix.modalview import ModalView
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout 
import socket
from kivy.utils import platform
if platform == 'android':
    import bluetooth

class MyApp(App):
    def build(self):
        ScrManager = ScreenManager(transition = FadeTransition())
        screens = [Menu(), Devices(), Controler()]
        for i in screens:
            ScrManager.add_widget(i)
        return ScrManager

class Menu(Screen):
    def __init__(self, name="Menu"):
        super(Menu, self).__init__(name=name)
        obj = [
            Button(text = "Подключиться", size_hint = (1, 0.6)),
            Button(text = "Настройки", size_hint = (1, 0.6)),
            Button(text = "Выход", size_hint = (1, 0.2))
        ]
        layout = BoxLayout(orientation = "vertical")
        for i in obj:
            layout.add_widget(i)
        self.add_widget(layout)
        obj[0].on_release = self.toConnect
        obj[2].bind(on_release = lambda x:App.get_running_app().stop())
    
    def toConnect(self):
        self.manager.transition.direction = "right"
        self.manager.current = "device"

class Devices(Screen):
    def __init__(self, name="device"):
        super(Devices, self).__init__(name=name)
        obj = [
            Button(text = "Устройство"),
            Button(text = "Назад")
        ]
        layout = BoxLayout()
        for i in obj:
            layout.add_widget(i)
        self.add_widget(layout)
        obj[1].on_release = self.goBack
        obj[0].on_release = self.next

    def next(self):
        self.manager.transition.direction = "right"
        self.manager.current = "Control"

    def goBack(self):
        self.manager.transition.direction = "left"
        self.manager.current = "Menu"

class Controler(Screen):
    def __init__(self, name="Control"):
        super(Controler, self).__init__(name=name)
        self.connection_type = None  # Добавляем инициализацию connection_type
        self.wifi_socket = None  # Добавляем инициализацию wifi_socket
        self.bt_socket = None  # Добавляем инициализацию bt_socket

        main_layout = BoxLayout(orientation='vertical')
        
        connection = Button(text='Выбрать способ подключения', size_hint=(1, 0.35))
        main_layout.add_widget(connection)

        float_layout = FloatLayout()

        self.light_button = Button(text='Свет',
            size_hint=(None, None),
            size=(60, 60),
            pos_hint={'x': 0, 'center_y': 0.5},
            background_normal='',
            background_color=(0.5, 0.5, 0.5, 1))
        
        back = Button(text='назад',
            size_hint=(None, None),
            size=(50, 50), 
            pos_hint={'x': 1-0.06, 'center_y': 0 + 0.05})
        
        left = Button(text='>',
            size_hint=(None, None),
            size=(60, 60), 
            pos_hint={'x': 0.5 + 0.15, 'center_y': 0.5 })
        
        right = Button(text='<',
            size_hint=(None, None),
            size=(60, 60), 
            pos_hint={'x': 0.5 - 0.15, 'center_y': 0.5})
        
        top = Button(text='^',
            size_hint=(None, None),
            size=(60, 60), 
            pos_hint={'x': 0.5, 'center_y': 0.5 + 0.15})
        
        down = Button(text='v',
            size_hint=(None, None),
            size=(60, 60), 
            pos_hint={'x': 0.5 , 'center_y': 0.5 - 0.15})
        
        float_layout.add_widget(left)
        float_layout.add_widget(right)
        float_layout.add_widget(top)
        float_layout.add_widget(down)

        float_layout.add_widget(back)
        
        float_layout.add_widget(self.light_button)
        main_layout.add_widget(float_layout)
        
        self.add_widget(main_layout)
        
        connection.on_release = self.show_connection_options
        back.on_release = self.goBack

        self.light_button.bind(on_press=self.highlight_light_button, on_release=self.unhighlight_light_button)
        self.light_button.bind(on_release=self.toggle_light)  

        self.light_state = False
        
        self.light_button.bind(on_press=lambda x: self.send_command('LIGHT_TOGGLE'))
        left.bind(on_press=lambda x: self.send_command('LEFT'))
        right.bind(on_press=lambda x: self.send_command('RIGHT'))
        top.bind(on_press=lambda x: self.send_command('FORWARD'))
        down.bind(on_press=lambda x: self.send_command('BACKWARD'))

    def goBack(self):
        self.manager.transition.direction = "left"
        self.manager.current = "device"

    def highlight_light_button(self, instance):
        """Подсвечивает кнопку при нажатии"""
        instance.background_color = (0.7, 0.7, 0.7, 1)
    
    def unhighlight_light_button(self, instance):
        """Возвращает обычный цвет кнопки при отпускании"""
        if self.light_state:
            instance.background_color = (0.2, 0.6, 1, 1)  # Синий (включено)
        else:
            instance.background_color = (0.5, 0.5, 0.5, 1)  # Серый (выключено)
    
    def toggle_light(self, instance):
        """Переключает состояние кнопки 'Свет'"""
        self.light_state = not self.light_state
        
        if self.light_state:
            # Включено - синий цвет
            instance.background_color = (0.2, 0.6, 1, 1)  # Синий
            instance.text = 'Свет'
            # Здесь можно добавить код для включения света
            print("Свет включен")
        else:
            # Выключено - серый цвет
            instance.background_color = (0.5, 0.5, 0.5, 1)  # Серый
            instance.text = 'Свет'
            # Здесь можно добавить код для выключения света
            print("Свет выключен")

    def send_command(self, command):
        """Отправка команды на ESP32 через выбранный интерфейс"""
        if not self.connection_type:
            print("Ошибка: не выбран способ подключения")
            return False
            
        try:
            if self.connection_type == 'Wi-Fi':
                return self._send_wifi_command(command)
            elif self.connection_type == 'Bluetooth':
                return self._send_bluetooth_command(command)
        except Exception as e:
            print(f"Ошибка при отправке команды: {e}")
            return False

    def _send_wifi_command(self, command):
        """Отправка команды через Wi-Fi на ESP32"""
        if not self.wifi_socket:
            # Создаем сокет при первом использовании
            self.wifi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # Подключаемся к ESP32 (IP может быть другим)
                self.wifi_socket.connect(('192.168.4.1', 80))  # Стандартный IP ESP32 в режиме AP
            except Exception as e:
                print(f"Ошибка подключения Wi-Fi: {e}")
                self.wifi_socket = None
                return False
                
        try:
            self.wifi_socket.sendall(command.encode())
            print(f"Команда {command} отправлена по Wi-Fi")
            return True
        except Exception as e:
            print(f"Ошибка отправки Wi-Fi команды: {e}")
            self.wifi_socket = None
            return False

    def _send_bluetooth_command(self, command):
        """Отправка команды через Bluetooth на ESP32"""
        if not self.bt_socket:
            # Поиск устройства ESP32 по имени
            target_name = "ESP32_BT"  # Замените на имя вашего ESP32 в Bluetooth
            target_address = None
            
            print("Поиск Bluetooth устройств...")
            nearby_devices = bluetooth.discover_devices()
            
            for addr in nearby_devices:
                if target_name == bluetooth.lookup_name(addr):
                    target_address = addr
                    break
                    
            if not target_address:
                print("ESP32 не найдено по Bluetooth")
                return False
                
            # UUID для последовательного порта
            uuid = "00001101-0000-1000-8000-00805F9B34FB"
            
            try:
                self.bt_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self.bt_socket.connect((target_address, 1))
            except Exception as e:
                print(f"Ошибка подключения Bluetooth: {e}")
                self.bt_socket = None
                return False
                
        try:
            self.bt_socket.send(command.encode())
            print(f"Команда {command} отправлена по Bluetooth")
            return True
        except Exception as e:
            print(f"Ошибка отправки Bluetooth команды: {e}")
            self.bt_socket = None
            return False

    def is_connected_to_esp_wifi(self):
        """Проверяет, подключен ли телефон к Wi-Fi сети ESP32"""
        if platform == 'android':
            try:
                from jnius import autoclass
                Context = autoclass('android.content.Context')
                WifiManager = autoclass('android.net.wifi.WifiManager')
                
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                wifi_manager = activity.getSystemService(Context.WIFI_SERVICE)
                
                if wifi_manager.isWifiEnabled():
                    wifi_info = wifi_manager.getConnectionInfo()
                    ssid = wifi_info.getSSID().strip('"')
                    return ssid.startswith('ESP32_')  # Замените на SSID вашей ESP32
            except:
                pass
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip_address = s.getsockname()[0]
            s.close()
            return ip_address.startswith('192.168.4.')
        except:
            return False

    def is_bluetooth_available(self):
        """Проверяет, доступен ли Bluetooth"""
        if platform == 'android':
            try:
                from jnius import autoclass
                BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
                adapter = BluetoothAdapter.getDefaultAdapter()
                return adapter is not None and adapter.isEnabled()
            except:
                return False
        return False  # Для других платформ пока считаем, что Bluetooth недоступен

    def show_connection_options(self, instance=None):
        modal = ModalView(size_hint=(1, 0.4), 
                        pos_hint={'x': 0, 'y': 0},
                        background_color=(0.9, 0.9, 0.9, 1),
                        overlay_color=(0, 0, 0, 0.5))
        
        options_box = BoxLayout(orientation='vertical',
                            spacing=10,
                            padding=10)
        
        # Настройка кнопки Wi-Fi
        wifi_connected = self.is_connected_to_esp_wifi()
        wifi_text = "Wi-Fi" if wifi_connected else "Wi-Fi (не подключено)"
        wifi_color = (0.2, 0.6, 1, 1) if wifi_connected else (0.7, 0.7, 0.7, 1)
        wifi_btn = Button(text=wifi_text,
                        background_normal='',
                        background_color=wifi_color,
                        disabled=not wifi_connected)
        
        # Настройка кнопки Bluetooth
        bt_available = self.is_bluetooth_available()
        bt_text = "Bluetooth" if bt_available else "Bluetooth (не подключено)"
        bt_color = (0.4, 0.8, 0.4, 1) if bt_available else (0.7, 0.7, 0.7, 1)
        bluetooth_btn = Button(text=bt_text,
                            background_normal='',
                            background_color=bt_color,
                            disabled=not bt_available)
        
        cancel_btn = Button(text='Отмена',
                        size_hint=(1, 0.4),
                        background_normal='',
                        background_color=(0.8, 0.2, 0.2, 1))
        
        if wifi_connected:
            wifi_btn.bind(on_release=lambda x: self.select_connection('Wi-Fi', modal))
        if bt_available:
            bluetooth_btn.bind(on_release=lambda x: self.select_connection('Bluetooth', modal))
        cancel_btn.bind(on_release=modal.dismiss)
        
        options_box.add_widget(wifi_btn)
        options_box.add_widget(bluetooth_btn)
        options_box.add_widget(cancel_btn)
        
        modal.add_widget(options_box)
        
        modal.opacity = 0
        modal.open()
        anim = Animation(opacity=1, duration=0.3)
        anim.start(modal)
    
    def select_connection(self, method, modal):
        print(f"Выбран способ подключения: {method}")
        modal.dismiss()

if __name__ == "__main__":
    MyApp().run()