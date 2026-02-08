"""
PDF广告文字和二维码移除工具
用于处理PDF文件中试卷图片底部的广告文字和二维码
"""

import cv2
import numpy as np
from PIL import Image
import os
import sys
import io

class PDFAdRemover:
    def __init__(self, ad_height_percent=0.15):
        """
        初始化广告移除器
        
        Args:
            ad_height_percent: 广告区域占图片高度的百分比,默认15%
        """
        self.ad_height_percent = ad_height_percent
    
    def detect_qrcode(self, image):
        """
        检测图片中的二维码
        
        Args:
            image: OpenCV图像对象
            
        Returns:
            二维码位置列表 [(x, y, w, h), ...]
        """
        detector = cv2.QRCodeDetector()
        value, points, straight_qrcode = detector.detectAndDecode(image)
        
        if points is not None:
            # 转换points为矩形坐标
            points = points.astype(int)
            x = int(np.min(points[:, 0]))
            y = int(np.min(points[:, 1]))
            w = int(np.max(points[:, 0]) - x)
            h = int(np.max(points[:, 1]) - y)
            return [(x, y, w, h)]
        return []
    
    def detect_text_area(self, image, bottom_region):
        """
        检测底部区域的文字区域
        
        Args:
            image: 完整图像
            bottom_region: 底部区域图像
            
        Returns:
            文字区域列表
        """
        # 转换为灰度图
        gray = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2GRAY)
        
        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 使用形态学操作检测文字区域
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # 查找轮廓
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        image_height = image.shape[0]
        bottom_start = int(image_height * (1 - self.ad_height_percent))
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # 调整y坐标到原图坐标系
            y_absolute = bottom_start + y
            
            # 过滤掉太小的区域
            if w > 50 and h > 10:
                text_regions.append((x, y_absolute, w, h))
        
        return text_regions
    
    def remove_advertisement(self, image_path, output_path=None):
        """
        移除图片底部的广告文字和二维码
        
        Args:
            image_path: 输入图片路径
            output_path: 输出图片路径,如果为None则覆盖原文件
            
        Returns:
            处理后的图片路径
        """
        # 读取图片
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图片: {image_path}")
        
        height, width = image.shape[:2]
        ad_height = int(height * self.ad_height_percent)
        bottom_start = height - ad_height
        
        # 提取底部区域
        bottom_region = image[bottom_start:height, 0:width]
        
        # 检测二维码
        qrcode_regions = self.detect_qrcode(bottom_region)
        
        # 检测文字区域
        text_regions = self.detect_text_area(image, bottom_region)
        
        # 合并所有需要移除的区域
        all_regions = qrcode_regions + text_regions
        
        # 移除广告区域
        if all_regions:
            # 创建白色覆盖层
            white_overlay = np.ones((ad_height, width, 3), dtype=np.uint8) * 255
            
            # 检测广告区域是否有文字或二维码
            if qrcode_regions or text_regions:
                # 如果检测到广告内容,则覆盖整个底部区域
                image[bottom_start:height, 0:width] = white_overlay
            else:
                # 如果没有检测到明显的广告内容,检查底部是否为纯色或接近纯色
                # 计算底部区域的颜色方差
                region_std = np.std(bottom_region)
                if region_std < 30:  # 如果颜色变化很小,可能是广告区域
                    image[bottom_start:height, 0:width] = white_overlay
        
        # 保存结果
        if output_path is None:
            output_path = image_path
        
        cv2.imwrite(output_path, image)
        return output_path
    
    def batch_process_pdf_images(self, pdf_path, output_dir=None):
        """
        批量处理PDF中的所有图片
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录,如果为None则在原目录创建"cleaned"子目录
            
        Returns:
            处理后的图片路径列表
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("请先安装pymupdf: pip install pymupdf")
            return []
        
        # 设置输出目录
        if output_dir is None:
            base_dir = os.path.dirname(pdf_path)
            output_dir = os.path.join(base_dir, "cleaned")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 打开PDF文件
        print(f"正在打开PDF: {pdf_path}")
        pdf_document = fitz.open(pdf_path)
        
        processed_images = []
        for i, page in enumerate(pdf_document):
            # 将页面转换为图片
            zoom = 2  # 放大倍数,提高清晰度
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # 转换为PIL Image
            img_data = pix.tobytes("png")
            from PIL import Image
            pil_image = Image.open(io.BytesIO(img_data))
            
            # 保存临时图片
            temp_path = os.path.join(output_dir, f"temp_page_{i}.png")
            pil_image.save(temp_path)
            
            # 处理图片
            output_path = os.path.join(output_dir, f"page_{i}.png")
            result_path = self.remove_advertisement(temp_path, output_path)
            processed_images.append(result_path)
            
            # 删除临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            print(f"已处理第 {i+1}/{len(pdf_document)} 页")
        
        pdf_document.close()
        return processed_images
    
    def batch_process_pdf_to_pdf(self, pdf_path, output_pdf_path=None):
        """
        批量处理PDF并生成新的PDF文件
        
        Args:
            pdf_path: 输入PDF文件路径
            output_pdf_path: 输出PDF文件路径,如果为None则在原目录添加"_cleaned"后缀
            
        Returns:
            处理后的PDF文件路径
        """
        try:
            import fitz  # PyMuPDF
            import io
        except ImportError:
            print("请先安装pymupdf: pip install pymupdf")
            return None
        
        # 设置输出PDF路径
        if output_pdf_path is None:
            base_name = os.path.splitext(pdf_path)[0]
            output_pdf_path = f"{base_name}_cleaned.pdf"
        
        # 打开PDF文件
        print(f"正在打开PDF: {pdf_path}")
        pdf_document = fitz.open(pdf_path)
        
        # 创建新的PDF文档
        output_pdf = fitz.open()
        
        for i, page in enumerate(pdf_document):
            # 将页面转换为图片
            zoom = 2  # 放大倍数,提高清晰度
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # 转换为PIL Image
            img_data = pix.tobytes("png")
            from PIL import Image
            pil_image = Image.open(io.BytesIO(img_data))
            
            # 保存临时图片
            temp_path = f"temp_page_{i}.png"
            pil_image.save(temp_path)
            
            # 处理图片
            cleaned_path = f"cleaned_page_{i}.png"
            self.remove_advertisement(temp_path, cleaned_path)
            
            # 将处理后的图片转换回PDF页面
            cleaned_img = Image.open(cleaned_path)
            img_bytes = io.BytesIO()
            cleaned_img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            
            # 创建新页面
            new_page = output_pdf.new_page(
                width=page.rect.width,
                height=page.rect.height
            )
            new_page.insert_image(
                new_page.rect,
                stream=img_bytes.getvalue()
            )
            
            # 删除临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(cleaned_path):
                os.remove(cleaned_path)
            
            print(f"已处理第 {i+1}/{len(pdf_document)} 页")
        
        # 保存输出PDF
        output_pdf.save(output_pdf_path)
        output_pdf.close()
        pdf_document.close()
        
        print(f"处理完成! 输出文件: {output_pdf_path}")
        return output_pdf_path


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  处理单个图片: python pdf_ad_remover.py <图片路径>")
        print("  处理PDF文件为图片: python pdf_ad_remover.py <PDF路径> --pdf-img")
        print("  处理PDF文件为PDF: python pdf_ad_remover.py <PDF路径> --pdf")
        return
    
    input_path = sys.argv[1]
    
    if not os.path.exists(input_path):
        print(f"错误: 文件不存在: {input_path}")
        return
    
    # 创建广告移除器
    remover = PDFAdRemover(ad_height_percent=0.15)
    
    # 检查是否为PDF文件
    if len(sys.argv) > 2:
        if sys.argv[2] == "--pdf":
            # 处理PDF文件为PDF
            print(f"开始处理PDF文件为PDF: {input_path}")
            output_pdf = remover.batch_process_pdf_to_pdf(input_path)
            
            if output_pdf:
                print(f"\n处理完成! 输出文件: {output_pdf}")
            else:
                print("处理失败!")
                
        elif sys.argv[2] == "--pdf-img":
            # 处理PDF文件为图片
            print(f"开始处理PDF文件为图片: {input_path}")
            processed_images = remover.batch_process_pdf_images(input_path)
            
            if processed_images:
                print(f"\n处理完成! 共处理 {len(processed_images)} 页")
                print(f"输出目录: {os.path.dirname(processed_images[0])}")
            else:
                print("处理失败!")
        else:
            print(f"未知选项: {sys.argv[2]}")
            print("可用选项: --pdf, --pdf-img")
    else:
        # 处理单个图片
        print(f"开始处理图片: {input_path}")
        output_path = input_path.replace('.', '_cleaned.')
        result = remover.remove_advertisement(input_path, output_path)
        print(f"处理完成! 输出文件: {result}")


if __name__ == "__main__":
    main()