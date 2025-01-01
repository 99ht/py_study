import PyPDF2
import openpyxl as op
import os
from datetime import datetime

def read_pdf_with_pypdf2(file_path):
    with open(file_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text = page.extract_text()
            start_index = text.find("序号")
            end_index = text.find("页码", start_index)

            if start_index != -1 and end_index != -1:
                result = text[start_index:end_index]
                #print(result)
                #newline_count = result.count('\n') + result.count('\r\n')
                #print(f"文本包含 {newline_count} 行")
                lines = [line.strip() for line in result.strip().split('\n') if line.strip()]
                for line in lines:
                    dis_list = line.split(' ')
                    if dis_list[0] == "序号":
                        continue
                    # 从后向前删除不需要的元素
                    indices_to_remove = [8, 5, 3, 1, 0]
                    for index in indices_to_remove:
                        if 0 <= index < len(dis_list):
                            del dis_list[index]
                        else:
                            print(f"无效的索引: {index}")
                    dis_list[2] = dis_list[2] + '——' + dis_list[3]
                    del dis_list[3]
                    dis_list.insert(2, "市内交通费")
                    dis_list.insert(3, "外出支持nt项目")
                    dis_list.insert(5, "增值税电子普通发票")
                    # 尝试将金额转换为浮点数
                    try:
                        dis_list[6] = float(dis_list[6])
                    except (ValueError, IndexError):
                        print(f"无法将 {dis_list[6]} 转换为数字，跳过此行")
                        continue
                    try:
                        dis_list[0] = f"{curr_year}年" + dis_list[0].split('-')[0] + "月" + dis_list[0].split('-')[1] + "日"
                        # dis_list[0] = f"{curr_year}/" + dis_list[0].split('-')[0] + "/" + dis_list[0].split('-')[1]
                    except (ValueError, IndexError):
                        print(f"无法将 {dis_list[0]} 转换为年月日，跳过此行")
                        continue
                    #dis_list[0] = dis_list[0].replace('-', '/')
                    ws.append(dis_list)
            else:
                print("未找到起始或结束字符串")


fileName = '滴滴出行行程报销单.xlsx'
if os.path.exists(fileName):
    os.remove(fileName)
wb = op.Workbook()  # 创建工作簿对象
ws = wb['Sheet']  # 创建子表
curr_year = datetime.now().year
read_pdf_with_pypdf2("滴滴出行行程报销单.pdf")
wb.save(fileName)
