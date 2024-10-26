# 引用uiautomator2包
import uiautomator2 as u2
import time
import subprocess
# 使用设备唯一标志码链接设备，其中9phqaetw是通过adb获取的设备标志码
# d = u2.connect('2fd210e5')
# d = u2.connect('192.168.1.101:39329')  # adb设定端口：adb tcpip 5566
d = u2.connect()  # 当前只有一个设备时可以用这个
print("adb已连接")
d.unlock()  # 解锁屏幕
time.sleep(0.2)
d.swipe(400, 1200, 400, 200)  # 上划，左上角是0,0
time.sleep(0.2)
subprocess.run("123456")  # 输入锁屏密码
time.sleep(0.2)
d(text="微信").click()  # 打开微信


# ########################---手机手势操作---########################################
# d.unlock()  # 解锁屏幕
# d.swipe(400, 1200, 400, 200)  # 上划，左上角是0,0
# time.sleep(0.2)  # 等待手机反应2秒钟
# d.press("home")  # 点击home键
# time.sleep(0.2)  # 等待手机反应2秒钟
# d.press("back")  # 点击back键
# time.sleep(0.2)  # 等待手机反应2秒钟
# d.press("volume_up")  # 音量+
# d.press("volume_down")  # 音量-
# d.press("volume_mute")  # 静音
# d(text="微信").click()
# ####################################################################################

# ########################---输入框输入固定字符---########################################
# def run_adb_command(command):
#     result = subprocess.run(command, capture_output=True, text=True, shell=True)
#     if result.returncode != 0:
#         print(f"Error: {result.stderr}")
#     else:
#         print(f"Output: {result.stdout}")  # f-string 的基本语法是在字符串前面加上一个 f 或 F，然后在字符串内部使用 {} 来嵌入表达式或变量。
#
#
# # 调用 adb 命令
# run_adb_command("adb devices")
# run_adb_command("adb shell input text 123456")
# ####################################################################################
