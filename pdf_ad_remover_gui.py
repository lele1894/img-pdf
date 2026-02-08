"""
PDF广告文字和二维码移除工具 - GUI版本
用于处理PDF文件中试卷图片底部的广告文字和二维码
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
from pdf_ad_remover import PDFAdRemover


class PDFAdRemoverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF广告移除工具")
        self.root.geometry("600x400")
        
        self.pdf_file_path = None
        self.output_dir = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建GUI组件"""
        # 标题
        title_label = tk.Label(
            self.root, 
            text="PDF广告移除工具", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # 说明文字
        desc_label = tk.Label(
            self.root,
            text="移除PDF文件中试卷图片底部的广告文字和二维码",
            font=("Arial", 10),
            fg="gray"
        )
        desc_label.pack(pady=5)
        
        # 文件选择框架
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=10, padx=20, fill="x")
        
        # PDF文件选择
        pdf_label = tk.Label(file_frame, text="PDF文件:", font=("Arial", 10))
        pdf_label.pack(anchor="w")
        
        pdf_entry_frame = tk.Frame(file_frame)
        pdf_entry_frame.pack(fill="x", pady=5)
        
        self.pdf_entry = tk.Entry(pdf_entry_frame, width=50)
        self.pdf_entry.pack(side="left", fill="x", expand=True)
        
        pdf_button = tk.Button(
            pdf_entry_frame, 
            text="浏览...", 
            command=self.select_pdf_file,
            width=10
        )
        pdf_button.pack(side="left", padx=5)
        
        # 输出目录选择
        output_label = tk.Label(file_frame, text="输出目录:", font=("Arial", 10))
        output_label.pack(anchor="w", pady=(10, 0))
        
        output_entry_frame = tk.Frame(file_frame)
        output_entry_frame.pack(fill="x", pady=5)
        
        self.output_entry = tk.Entry(output_entry_frame, width=50)
        self.output_entry.pack(side="left", fill="x", expand=True)
        
        output_button = tk.Button(
            output_entry_frame,
            text="浏览...",
            command=self.select_output_dir,
            width=10
        )
        output_button.pack(side="left", padx=5)
        
        # 设置框架
        settings_frame = tk.Frame(self.root)
        settings_frame.pack(pady=20, padx=20, fill="x")
        
        # 广告高度百分比
        ad_height_label = tk.Label(settings_frame, text="广告区域高度(%):", font=("Arial", 10))
        ad_height_label.pack(anchor="w")
        
        self.ad_height_var = tk.DoubleVar(value=15)
        ad_height_scale = tk.Scale(
            settings_frame,
            from_=5,
            to=30,
            orient="horizontal",
            variable=self.ad_height_var,
            length=400
        )
        ad_height_scale.pack(fill="x", pady=5)
        
        # 处理按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.process_button = tk.Button(
            button_frame,
            text="开始处理",
            command=self.start_processing,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=20,
            height=2
        )
        self.process_button.pack()
        
        # 进度条
        self.progress = ttk.Progressbar(
            self.root,
            mode="indeterminate",
            length=400
        )
        self.progress.pack(pady=10)
        
        # 状态标签
        self.status_label = tk.Label(
            self.root,
            text="准备就绪",
            font=("Arial", 10),
            fg="blue"
        )
        self.status_label.pack(pady=5)
    
    def select_pdf_file(self):
        """选择PDF文件"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        if file_path:
            self.pdf_file_path = file_path
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, file_path)
            
            # 自动设置输出目录
            base_dir = os.path.dirname(file_path)
            self.output_dir = os.path.join(base_dir, "cleaned")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, self.output_dir)
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = filedialog.askdirectory(title="选择输出目录")
        
        if dir_path:
            self.output_dir = dir_path
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, dir_path)
    
    def start_processing(self):
        """开始处理"""
        # 验证输入
        if not self.pdf_file_path or not os.path.exists(self.pdf_file_path):
            messagebox.showerror("错误", "请选择有效的PDF文件!")
            return
        
        if not self.output_dir:
            self.output_dir = os.path.join(os.path.dirname(self.pdf_file_path), "cleaned")
        
        # 禁用按钮,防止重复点击
        self.process_button.config(state="disabled", text="处理中...")
        self.progress.start()
        self.status_label.config(text="正在处理...")
        
        # 在新线程中处理,避免阻塞GUI
        thread = threading.Thread(target=self.process_pdf)
        thread.start()
    
    def process_pdf(self):
        """处理PDF文件"""
        try:
            # 创建广告移除器
            ad_height_percent = self.ad_height_var.get() / 100
            remover = PDFAdRemover(ad_height_percent=ad_height_percent)
            
            # 处理PDF
            processed_images = remover.batch_process_pdf_images(
                self.pdf_file_path,
                self.output_dir
            )
            
            # 处理完成
            self.root.after(0, lambda: self.processing_completed(True, len(processed_images)))
            
        except Exception as e:
            # 处理失败
            self.root.after(0, lambda: self.processing_completed(False, str(e)))
    
    def processing_completed(self, success, result):
        """处理完成回调"""
        self.progress.stop()
        self.process_button.config(state="normal", text="开始处理")
        
        if success:
            self.status_label.config(
                text=f"处理完成! 共处理 {result} 页",
                fg="green"
            )
            messagebox.showinfo(
                "成功",
                f"处理完成!\n共处理 {result} 页\n输出目录: {self.output_dir}"
            )
        else:
            self.status_label.config(
                text=f"处理失败: {result}",
                fg="red"
            )
            messagebox.showerror("错误", f"处理失败:\n{result}")


def main():
    """主函数"""
    root = tk.Tk()
    app = PDFAdRemoverGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()