# 安装：始终使用 pip install PyMuPDF
# 导入：始终使用 import fitz
# 本质：PyMuPDF 是包名，fitz 是模块名，二者指向同一个库
import fitz  # PyMuPDF
import os


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


def pdf_files_re_sort(filter_files):
    pdf_files_num = []
    pdf_files_no_num = []
    for pdf_file in filter_files:
        try:  # 纯数字文件名放到一个列表
            flag = int(os.path.splitext(os.path.basename(pdf_file))[0])
            pdf_files_num.append(pdf_file)
        except Exception as e:
            pdf_files_no_num.append(pdf_file)
            continue
    pdf_files_num = sorted(pdf_files_num, key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
    return pdf_files_num + pdf_files_no_num
    # pdf_files_num.extend(pdf_files_no_num) # 也可以实现列表相加

def merge_pdf_pages(pdf_files, output_file):
    doc = fitz.open() # 创建新文档
    for file in pdf_files:
        doc_temp = fitz.open(file)
        doc.insert_pdf(doc_temp, from_page=0, to_page=len(doc_temp))
    doc.save(output_file)
    doc.close()


if __name__ == "__main__":
    output_pdf_file = "Merged_PDF.pdf"
    pdf_files_all = get_all_pdf_files()
    pdf_files_re_sorted = pdf_files_re_sort(pdf_files_all)
    merge_pdf_pages(pdf_files_re_sorted, output_pdf_file)