import os
import re
import shutil
import sys

folder_prefix = "folder_" #input("请输入您需要打包的文件夹前缀：\r\n")
def organize_files(folder_path):
    for filename in os.listdir(folder_path):
        the_file_path = os.path.join(folder_path, filename)
        if os.path.isfile(the_file_path): #遍历所有文件
            if the_file_path == current_run_file_path or the_file_path == current_run_exe_path:
                continue
            file_type = os.path.splitext(filename)[1].lower() #获取文件类型
            try:
                file_type_real = re.findall(r"\b\w+\b", file_type)[0]
                file_dir = os.path.join(folder_path, f"{folder_prefix}{file_type_real}")
                if not os.path.exists(file_dir):
                    os.makedirs(file_dir)
                shutil.move(os.path.join(folder_path, filename), file_dir)
            except Exception as e:
                continue


def filter_spacial_folder(folder_path):
    match = re.search(rf"\b{folder_prefix}\w+", folder_path)
    if match is not None:
        return True
    else:
        return False


def folder_rename_after(idx, folder_path):
    if os.path.isdir(folder_path):
        dir_path = os.path.dirname(folder_path)  #获取父目录
        dir_name = os.path.basename(folder_path) #获取文件路径
        renamed_folder = os.path.join(dir_path, f"{dir_name}")
        os.rename(folder_path, renamed_folder)


# 使用示例
if __name__ == "__main__":
    current_dir = os.getcwd()
    current_run_file_path = os.path.abspath(__file__) #当前执行的py文件路径
    current_run_exe_path = sys.executable #当前执行的exe文件路径
    organize_files(os.getcwd())
    filter_folder = list(filter(filter_spacial_folder, os.listdir(current_dir)))
    for idx, folder in enumerate(filter_folder, start=1):
        folder_rename_after(idx, os.path.join(current_dir, folder))
