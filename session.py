import re
import math
import string
from itertools import product
from lxml import etree as ET

from appium import webdriver
from android import AndroidDeviceHandler
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import By

class AppiumSessionHandler:
    def __init__(self):
        self.driver = None
        self.device_handler = AndroidDeviceHandler()
        self.device_handler.clear_app_data("io.appium.settings")
        self.device_handler.clear_app_data("io.appium.uiautomator2.server")
        self.device_handler.clear_app_data("io.appium.uiautomator2.server.test")
        self.device_handler._run_adb_command("forward --remove-all")

    def start_session(self):
        hub_url = f"http://localhost:4723/wd/hub"
        options = UiAutomator2Options()
        options.device_name = "device"
        options.platform_name = "Android"
        options.automation_name = "UiAutomator2"
        options.new_command_timeout = 86400
        options.use_json_source = True
        options.system_port = 8200
        options.auto_grant_permissions = True
        options.auto_accept_alerts = True    
        self.driver = webdriver.Remote(command_executor=hub_url, options=options)
        self.driver.update_settings({"allowInvisibleElements": True})
        self.driver.implicitly_wait(10)

    def stop_session(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None
        else:
            print("No session to stop.")

    def get_driver(self):
        if self.driver is None:
            raise Exception("Session not started. Call start_session() first.")
        return self.driver
    
    def go_back(self):
        self.driver.back()
        return "driver.back()"
    
    def hide_keyboard(self):
        self.driver.hide_keyboard()
        return "driver.hide_keyboard()"
    
    def lock(self):
        self.driver.lock()
        return "driver.lock()"
    
    def unlock(self):
        self.driver.unlock()
        return "driver.unlock()"
    
    def background_app(self):
        self.driver.background_app(3)
        return "driver.background_app(3)"
    
    def open_notifications(self):
        self.driver.open_notifications()
        return "driver.open_notifications()"
    
    def get_base_code(self):
        return """from appium import webdriver\nfrom appium.options.android import UiAutomator2Options\nfrom appium.webdriver.common.appiumby import By\n\noptions = UiAutomator2Options()\noptions.device_name = 'device'\noptions.platform_name = 'Android'\noptions.automation_name = 'UiAutomator2'\noptions.new_command_timeout = 86400\noptions.use_json_source = True\noptions.system_port = 8200\noptions.auto_grant_permissions = True\noptions.auto_accept_alerts = True\ndriver = webdriver.Remote(command_executor='http://localhost:4723/wd/hub', options=options)\ndriver.update_settings({'allowInvisibleElements': true})\ndriver.implicitly_wait(10)\n"""
    
    def click(self, x: int, y: int):
        code = ''
        element = self._find_closest_element(x, y)
        if element is not None:
            xpath = element.get('xpath')
            code = f"element = driver.find_element(By.XPATH, \"{xpath}\")\nelement.click();"
        self.driver.tap([(x, y)], 100)
        return code
    
    def type(self, text: str):
        enter = text.endswith("|enter")
        if enter:
            text = text.replace('|enter', '')
        if text == 'delete':
            self.driver.press_keycode(67)
            return "driver.press_keycode(67)"
        element = self._find_focused_element()
        if element is not None:
            xpath = element.get('xpath')
            code = f'element = driver.find_element(By.XPATH, "{xpath}")\nelement.send_keys("{text}");'
        else:
            code = ''
        self.driver.execute_script("mobile: type", {"text": text})
        if enter:
            self.driver.press_keycode(66)
            code += "\ndriver.press_keycode(66)"
        return code
        
    def clear(self, x: int, y: int):
        code = ''        
        element = self._find_closest_element(x, y)
        if element is not None and element.get('class') == 'android.widget.EditText':
            xpath = element.get('xpath')
            element = self.driver.find_element(By.XPATH, xpath)
            element.clear()
            code = f"element = driver.find_element(By.XPATH, '{xpath}')\nelement.clear()"
        return code
    
    def scroll(self, text: str):
        code = ''
        text = text.replace('scroll:', '')
        dict = text.split(',')
        direction = dict[0]
        start_x = int(dict[1])
        start_y = int(dict[2])
        value = 350
        
        directions = {
            "up": lambda: self.driver.swipe(start_x, start_y + value, start_x, start_y - value),
            "down": lambda: self.driver.swipe(start_x, start_y - value, start_x, start_y + value),
            "left": lambda: self.driver.swipe(start_x + value, start_y, start_x - value, start_y),
            "right": lambda: self.driver.swipe(start_x - value, start_y, start_x + value, start_y)
        }
        element = self._find_closest_element(start_x, start_y)
        if element is not None:
            xpath = element.get('xpath')
        action = directions.get(direction.lower())
        if action:
            action()
        else:
            return None
        
    def _parse_bounds(self, bounds):
        """
        Parses the bounds string in the format '[x1,y1][x2,y2]' and returns a tuple of integers.
        """
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
        return tuple(map(int, match.groups())) if match else None

    def _get_center(self, bounds):
        """
        Calculates the center coordinates of the given bounds (x1, y1, x2, y2).
        Returns a tuple of the center coordinates (center_x, center_y).
        """
        x1, y1, x2, y2 = bounds
        return (x1 + x2) / 2, (y1 + y2) / 2

    def _distance(self, x1, y1, x2, y2):
        """
        Calculates the Euclidean distance between two points (x1, y1) and (x2, y2).
        Returns the distance as a float.
        """
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def _find_closest_element(self, x, y):
        """
        Parses the XML string and finds the closest element to the given coordinates (x, y).
        Returns the XPath for the closest element based on its attributes.
        """
        dump = self.driver.page_source
        if dump.startswith('<?xml'):
            dump = dump[dump.index('?>') + 2:]
        root = ET.fromstring(dump)

        self.add_tag_id(root)

        closest_distance = float('inf')
        closest_element = None

        for elem in root.iter():
            bounds = elem.get('bounds')
            if bounds:
                parsed_bounds = self._parse_bounds(bounds)
                if parsed_bounds:
                    center_x, center_y = self._get_center(parsed_bounds)
                    current_distance = self._distance(x, y, center_x, center_y)

                    if current_distance <= closest_distance:
                        closest_distance = current_distance
                        closest_element = elem

        if closest_element is not None:
            return { 
                'class': closest_element.get('class'), 
                'text': closest_element.get('text'), 
                'name': closest_element.get('name'), 
                'hint': closest_element.get('hint'), 
                'content-desc': closest_element.get('content-desc'),
                'resource-id': closest_element.get('resource-id'),
                'xpath': self.get_xpath(root, closest_element.get('tagId'))
            }
        else:
            return None
    
    def _find_focused_element(self):
        """
        Parses the XML string and finds the first element with focused=true.
        Returns the element's attributes as a dictionary.
        """
        dump = self.driver.page_source
        if dump.startswith('<?xml'):
            dump = dump[dump.index('?>') + 2:]
        root = ET.fromstring(dump)
        self.add_tag_id(root)

        # Iterate over elements to find the first focused element
        for elem in root.iter():
            if elem.get('focused') == 'true':
                return {
                    'class': elem.get('class'),
                    'text': elem.get('text'),
                    'name': elem.get('name'),
                    'hint': elem.get('hint'),
                    'content-desc': elem.get('content-desc'),
                    'resource-id': elem.get('resource-id'),
                    'xpath': self.get_xpath(root, elem.get('tagId'))
                }
        
        return None
    
    def add_tag_id(self, root):
        letters = string.ascii_uppercase
        tag_id_list = [''.join(pair) for pair in product(letters, repeat=2)]
        counter = 0
        for elem in root.iter():
            tag_id = tag_id_list[counter]
            elem.set("tagId", f"{tag_id}")
            counter += 1

    def get_xpath(self, root, tag):
        parent_map = {child: parent for parent in root.iter() for child in parent}
        node = root.find(f".//*[@tagId='{tag}']")
        attributes = [
            'text', 'name',
            'resource-id', 'accessibility-id', 'content-desc', 'contentDescription',
            'label', 'value', 'placeholder', 'hint',
            'class', 'type',
            'enabled', 'visible', 'accessible', 'checkable', 'checked', 
            'clickable', 'focusable', 'focused', 'scrollable', 'long-clickable', 
            'password', 'selected', 'displayed', 'instance'
        ]
        path = []
        current_element = node
        while current_element is not None:
            parent = parent_map.get(current_element)
            siblings = parent.findall(current_element.tag) if parent is not None else []
            if len(siblings) > 1:
                index = siblings.index(current_element) + 1
                path.append(f"{current_element.tag}[{index}]")
            else:
                path.append(current_element.tag)
            current_element = parent
        path.reverse()
        xpath1 = "/" + "/".join(path)

        # lxml allows for xpath processing here
        lxml_element = root.xpath(xpath1)[0]
        conditions = []
        for attr in attributes:
            if lxml_element.get(attr):
                conditions.append(f"@{attr}={repr(lxml_element.get(attr))}")
                xpath2 = f"{lxml_element.tag}[" + " and ".join(conditions) + "]"
                if len(root.xpath(f"//{xpath2}")) == 1:
                    return f"//{xpath2}"
        
        return f"{xpath1}"
    

    


    