import pdf2docx
import os

#读取当前目录所有pdf文件
def get_all_pdf_files():
    current_directory = os.getcwd()
    pdf_files = []
    print(os.listdir(current_directory))
    for file in os.listdir(current_directory):
        if file.lower().endswith('.pdf'):
            pdf_file_path = os.path.join(current_directory, file)
            pdf_files.append(pdf_file_path)
    return pdf_files


pdf_files = get_all_pdf_files()
for pdf_file in pdf_files:
    cv = pdf2docx.Converter(pdf_file) # 转换PDF到Word(pdf2docx部分版本不支持with as)
    output_word_path = os.path.splitext(pdf_file)[0] + '.docx'  #需要生成的文件名
    cv.convert(output_word_path) #执行实际的转换操作，将 PDF 内容写入到 Word 文件中
    cv.close()