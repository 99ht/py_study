from PyPDF2 import PdfReader, PdfWriter


def split_pdf_pages(input_path, output_folder="output"):
    # 创建输出文件夹（如果不存在）
    import os
    os.makedirs(output_folder, exist_ok=True)

    # 读取PDF文件
    reader = PdfReader(input_path)

    # 遍历每一页
    for page_num in range(len(reader.pages)):
        writer = PdfWriter()
        writer.add_page(reader.pages[page_num])

        # 生成输出文件名（第1页为page_1.pdf）
        output_filename = f"page_{page_num + 1}.pdf"
        output_path = os.path.join(output_folder, output_filename)

        # 写入新文件
        with open(output_path, "wb") as out_pdf:
            writer.write(out_pdf)

    print(f"成功拆分为 {len(reader.pages)} 个文件，保存在 {output_folder} 文件夹")


# 使用示例
if __name__ == "__main__":
    input_pdf = "input.pdf"  # 替换为你的PDF路径
    split_pdf_pages(input_pdf)