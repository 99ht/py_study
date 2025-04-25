import os
from send2trash import send2trash

current_dir = os.getcwd()  # 获取当前工作目录
cleaned_folder = "已删除的空文件夹.txt"

def safe_remove(file_path):
    with open(cleaned_folder, mode="a", encoding="utf-8") as cleaned_file:
        try:
            send2trash(file_path)  # 发送到回收站
            cleaned_file.write(f"{file_path}\n")
        except Exception as e:
            print(f"删除失败！原因：{e}, 路径：{file_path}")

if __name__ == "__main__":
    if os.path.exists(cleaned_folder):
        os.remove(cleaned_folder)
    for root, dirs, files in os.walk(current_dir, topdown=False):
        # print(os.listdir(root))
        # 判断目录是否为空（包括隐藏文件/文件夹）
        if not os.listdir(root):
            try:
                safe_remove(root)
            except OSError as e:
                continue