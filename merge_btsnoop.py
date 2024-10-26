# -*- coding: UTF-8 -*-
import os
import glob

Header = (0x62, 0x74, 0x73, 0x6E, 0x6F, 0x6F, 0x70, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xEA)


def filter_snoop(special_filename):
    with open(special_filename, "rb") as temp_file:
        if bytes(temp_file.read(16)) == bytes(Header):
            return True
    return False


if __name__ == '__main__':
    curr_dir = os.getcwd()
    tar_file_path = curr_dir + r"/all_btsnoop.log"
    if os.path.exists(tar_file_path):
        os.remove(tar_file_path)
    all_file = glob.glob(curr_dir + "/*.*")
    all_file = list(filter(filter_snoop, all_file))
    with open(tar_file_path, "ab") as tar_file:
        tar_file.write(bytes(Header))
        for each_file in all_file:
            with open(each_file, "rb") as file:
                file_payload = file.read()
                file_payload = file_payload[len(Header):]
                tar_file.write(file_payload)
    # with open(tar_file_path, "rb") as tar_file_1:
    #    print(tar_file_1.read())
