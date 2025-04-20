sum = 0;
with open("app_temp.txt", "w", encoding="utf-8") as tar_file:
    with open("app.lst", "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip().split() #strip移除空白字符，包括空格、制表符、换行符等
            try:
                if (line[3] == ".bss" and line[4][:2] == "00"):
                    hex_num = int(line[4], 16) #第二个参数16表示读取按照16进制
                    sum += hex_num
                    tar_file.write(line[3] + " " + line[4] + " " + line[5] + "\n")
            except ValueError:
                continue
        print(sum)      #打印10进制
        print(hex(sum)) #打印16进制