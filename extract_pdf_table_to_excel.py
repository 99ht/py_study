import pdfplumber
import openpyxl as op
import os
from datetime import datetime

null_line = [" "] #不同页以及不同的表需要用空行隔开(不同页隔2行,同页不同表隔1行)

def extract_and_merge_pdf_tables(pdf_path):
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # 提取当前页的所有表格
            tables = page.extract_tables()
            #print(tables)
            for table in tables: #对tables 列表里的每个表格进行遍历
                merged_table = []
                for row in table: #对当前表格里的每一行进行遍历
                    merged_row = []
                    for cell in row: #对当前行里的每个单元格进行遍历
                        if cell is not None:
                            # 拼合换行的文字
                            merged_cell = ''.join(cell.splitlines())
                            merged_row.append(merged_cell)
                        else:
                            merged_row.append(None)
                    ws.append(merged_row)
                    merged_table.append(merged_row)
                ws.append(null_line)
                all_tables.append(merged_table)
            ws.append(null_line)
    return all_tables

def adjust_custom_format(tables):
    try:
        new_table = []
        for table in tables:
            new_row = []
            del table[0]
            for row in table:
                date = row[2][0:5]
                del row[6]
                del row[3]
                del row[1]
                del row[0]
                row[0] = row[0][-2:]
                row.insert(0, date)
                row[2] = row[2] + "--" + row[3]
                del row[3]
                row.insert(2, "市内交通费")
                row.insert(3, "外出岍丞支持项目")
                row.insert(5, "增值税电子普通发票")
                # 尝试将金额转换为浮点数
                try:
                    row[6] = float(row[6])
                except (ValueError, IndexError):
                    print(f"无法将 {row[6]} 转换为数字，跳过此行")
                    continue
                try:
                    row[0] = f"{curr_year}年" + row[0].split('-')[0] + "月" + row[0].split('-')[1] + "日"
                    # row[0] = f"{curr_year}/" + row[0].split('-')[0] + "/" + row[0].split('-')[1]
                except (ValueError, IndexError):
                    print(f"无法将 {row[0]} 转换为年月日，跳过此行")
                    continue
                new_cell = []
                #print(type(new_cell))
                for cell in row:
                    #print(type(cell))
                    new_cell.append(cell)
                ws2.append(new_cell)
                new_row.append(row)
            new_table.append(new_row)
        #print(new_table)
    except Exception as e:  #捕获所有异常
        print(f"存在无法转为特定格式表格的问题,EEROR错误类型：{e}");
    return new_table


#读取当前目录所有pdf文件
def get_all_pdf_files():
    current_directory = os.getcwd()
    pdf_files = []
    #print(os.listdir(current_directory))
    for file in os.listdir(current_directory):
        if file.lower().endswith('.pdf'):
            pdf_file_path = os.path.join(current_directory, file)
            pdf_files.append(pdf_file_path)
    return pdf_files


pdf_files = get_all_pdf_files()
for pdf_file in pdf_files:
    wb = op.Workbook()
    ws = wb.active  # 创建子表
    ws.title = "从pdf提取的sheet"
    tables = extract_and_merge_pdf_tables(pdf_file)
    if tables: #没有table就不保存excel文件了
        ws2 = wb.create_sheet(title="按照固定格式生成的sheet")
        output_excel_path = os.path.splitext(pdf_file)[0] + '.xlsx'  #需要生成的文件名
        curr_year = datetime.now().year
        costom_tables = adjust_custom_format(tables)
        if not costom_tables:  #表格不存在需要删除对应的子表
            wb.remove(ws2)
        wb.save(output_excel_path)  # 替换为你想要保存的 Excel 文件路径
