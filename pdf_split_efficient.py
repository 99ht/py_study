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


def split_pdf(input_path, output_dir="split_pdfs"):
    doc = fitz.open(input_path)
    output_dir = os.path.splitext(input_path)[0]
    os.makedirs(output_dir, exist_ok=True)
    for page_num in range(len(doc)):
        # 创建新文档并插入单页
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        # 保存文件
        output_path = os.path.join(output_dir, f"{page_num + 1}.pdf")
        new_doc.save(output_path)
        new_doc.close()

    print(f"PDF已拆分为 {len(doc)} 个文件，保存在 '{output_dir}' 目录")


# 使用示例
if __name__ == "__main__":
    pdf_files = get_all_pdf_files()
    for file in pdf_files:
        split_pdf(file)