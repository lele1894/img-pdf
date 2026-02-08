"""
PDF广告移除工具 - 交互式标注版本(保留区域模式 + 对比预览)
允许用户选择要保留的区域,自动去除保留区域外的白边
支持源文件和处理后文件的对比预览,左右同步滚动
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import threading
import os
import cv2
import numpy as np
from PIL import Image, ImageTk


class ComparePreviewGUI:
    """对比预览界面"""
    
    def __init__(self, root, original_pdf_path, cleaned_pdf_path):
        self.root = root
        self.root.title("PDF对比预览 - 源文件 vs 处理后文件")
        self.root.geometry("1600x900")
        
        self.original_pdf_path = original_pdf_path
        self.cleaned_pdf_path = cleaned_pdf_path
        
        # 数据存储
        self.original_images = []
        self.cleaned_images = []
        self.current_page = 0
        self.total_pages = 0
        
        # 创建界面
        self.create_widgets()
        
        # 加载PDF
        self.load_pdfs()
    
    def create_widgets(self):
        """创建GUI组件"""
        # 顶部控制栏
        control_frame = tk.Frame(self.root, bg="#34495e", height=60)
        control_frame.pack(side="top", fill="x")
        
        # 标题
        title_label = tk.Label(
            control_frame,
            text="📊 PDF对比预览",
            font=("Arial", 18, "bold"),
            bg="#34495e",
            fg="white"
        )
        title_label.pack(side="left", padx=20, pady=10)
        
        # 页面控制
        page_frame = tk.Frame(control_frame, bg="#34495e")
        page_frame.pack(side="right", padx=20, pady=10)
        
        self.page_label = tk.Label(
            page_frame,
            text="第 1 / 1 页",
            font=("Arial", 12),
            bg="#34495e",
            fg="white"
        )
        self.page_label.pack(side="left", padx=10)
        
        prev_button = tk.Button(
            page_frame,
            text="◀ 上一页",
            command=self.prev_page,
            width=10,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold")
        )
        prev_button.pack(side="left", padx=5)
        
        next_button = tk.Button(
            page_frame,
            text="下一页 ▶",
            command=self.next_page,
            width=10,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold")
        )
        next_button.pack(side="left", padx=5)
        
        # 主内容区域 - 左右对比
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)
        
        # 左侧 - 源文件
        left_frame = tk.Frame(main_frame, bg="#2c3e50")
        left_frame.pack(side="left", fill="both", expand=True)
        
        left_title = tk.Label(
            left_frame,
            text="📄 源文件",
            font=("Arial", 14, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        left_title.pack(pady=10)
        
        # 左侧缩放控制
        left_zoom_frame = tk.Frame(left_frame, bg="#2c3e50")
        left_zoom_frame.pack(pady=5)
        
        left_zoom_label = tk.Label(
            left_zoom_frame,
            text="缩放:",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="white"
        )
        left_zoom_label.pack(side="left", padx=5)
        
        self.left_zoom_var = tk.DoubleVar(value=0.5)
        left_zoom_scale = tk.Scale(
            left_zoom_frame,
            from_=0.1,
            to=2.0,
            resolution=0.1,
            orient="horizontal",
            variable=self.left_zoom_var,
            command=lambda v: self.on_left_zoom_change(v),
            length=200,
            bg="#2c3e50",
            fg="white"
        )
        left_zoom_scale.pack(side="left", padx=5)
        
        left_canvas_frame = tk.Frame(left_frame, bg="white", relief="sunken", borderwidth=3)
        left_canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.left_canvas = tk.Canvas(left_canvas_frame, bg="white")
        self.left_canvas.pack(fill="both", expand=True)
        
        # 绑定滚动事件
        self.left_canvas.bind("<MouseWheel>", self.on_left_scroll)
        self.left_canvas.bind("<Button-4>", self.on_left_scroll)
        self.left_canvas.bind("<Button-5>", self.on_left_scroll)
        
        # 右侧 - 处理后文件
        right_frame = tk.Frame(main_frame, bg="#27ae60")
        right_frame.pack(side="right", fill="both", expand=True)
        
        right_title = tk.Label(
            right_frame,
            text="✅ 处理后文件",
            font=("Arial", 14, "bold"),
            bg="#27ae60",
            fg="white"
        )
        right_title.pack(pady=10)
        
        # 右侧缩放控制
        right_zoom_frame = tk.Frame(right_frame, bg="#27ae60")
        right_zoom_frame.pack(pady=5)
        
        right_zoom_label = tk.Label(
            right_zoom_frame,
            text="缩放:",
            font=("Arial", 10),
            bg="#27ae60",
            fg="white"
        )
        right_zoom_label.pack(side="left", padx=5)
        
        self.right_zoom_var = tk.DoubleVar(value=0.5)
        right_zoom_scale = tk.Scale(
            right_zoom_frame,
            from_=0.1,
            to=2.0,
            resolution=0.1,
            orient="horizontal",
            variable=self.right_zoom_var,
            command=lambda v: self.on_right_zoom_change(v),
            length=200,
            bg="#27ae60",
            fg="white"
        )
        right_zoom_scale.pack(side="left", padx=5)
        
        right_canvas_frame = tk.Frame(right_frame, bg="white", relief="sunken", borderwidth=3)
        right_canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.right_canvas = tk.Canvas(right_canvas_frame, bg="white")
        self.right_canvas.pack(fill="both", expand=True)
        
        # 绑定滚动事件
        self.right_canvas.bind("<MouseWheel>", self.on_right_scroll)
        self.right_canvas.bind("<Button-4>", self.on_right_scroll)
        self.right_canvas.bind("<Button-5>", self.on_right_scroll)
        
        # 底部信息栏
        info_frame = tk.Frame(self.root, bg="#ecf0f1", height=40)
        info_frame.pack(side="bottom", fill="x")
        
        info_text = f"源文件: {os.path.basename(self.original_pdf_path)}  |  处理后文件: {os.path.basename(self.cleaned_pdf_path)}"
        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=("Arial", 10),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        info_label.pack(pady=10)
    
    def load_pdfs(self):
        """加载PDF文件"""
        try:
            import fitz
            import io
            
            # 加载源文件
            self.root.config(cursor="watch")
            self.root.update()
            
            print(f"正在加载源文件: {self.original_pdf_path}")
            print(f"正在加载处理后文件: {self.cleaned_pdf_path}")
            
            original_doc = fitz.open(self.original_pdf_path)
            cleaned_doc = fitz.open(self.cleaned_pdf_path)
            
            print(f"源文件页数: {len(original_doc)}")
            print(f"处理后文件页数: {len(cleaned_doc)}")
            
            self.total_pages = min(len(original_doc), len(cleaned_doc))
            print(f"总页数: {self.total_pages}")
            
            if self.total_pages == 0:
                raise Exception("PDF文件为空")
            
            # 转换所有页面为图片
            zoom = 2
            
            for i in range(self.total_pages):
                print(f"正在转换第 {i+1}/{self.total_pages} 页...")
                
                # 源文件页面
                orig_page = original_doc[i]
                orig_mat = fitz.Matrix(zoom, zoom)
                orig_pix = orig_page.get_pixmap(matrix=orig_mat)
                orig_img_data = orig_pix.tobytes("png")
                orig_image = Image.open(io.BytesIO(orig_img_data))
                self.original_images.append(orig_image)
                print(f"  源文件第{i+1}页加载成功, 尺寸: {orig_image.size}")
                
                # 处理后文件页面
                clean_page = cleaned_doc[i]
                clean_mat = fitz.Matrix(zoom, zoom)
                clean_pix = clean_page.get_pixmap(matrix=clean_mat)
                clean_img_data = clean_pix.tobytes("png")
                clean_image = Image.open(io.BytesIO(clean_img_data))
                self.cleaned_images.append(clean_image)
                print(f"  处理后第{i+1}页加载成功, 尺寸: {clean_image.size}")
            
            original_doc.close()
            cleaned_doc.close()
            
            self.root.config(cursor="")
            
            print("所有页面加载完成,开始显示...")
            
            # 显示第一页
            self.root.after(100, lambda: self.display_page(0))
            
        except Exception as e:
            self.root.config(cursor="")
            print(f"加载PDF失败: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"加载PDF失败:\n{str(e)}")
            self.root.destroy()
    
    def display_page(self, page_num):
        """显示指定页"""
        print(f"display_page 被调用, 页码: {page_num}")
        
        if page_num < 0 or page_num >= self.total_pages:
            print(f"页码超出范围: {page_num} / {self.total_pages}")
            return
        
        self.current_page = page_num
        
        # 更新页面标签
        self.page_label.config(text=f"第 {page_num + 1} / {self.total_pages} 页")
        
        # 获取各自独立的缩放比例
        left_zoom_factor = self.left_zoom_var.get()
        right_zoom_factor = self.right_zoom_var.get()
        
        print(f"准备显示第 {page_num + 1} 页")
        print(f"源文件缩放比例: {left_zoom_factor}")
        print(f"处理后文件缩放比例: {right_zoom_factor}")
        print(f"源文件图片数量: {len(self.original_images)}")
        print(f"处理后图片数量: {len(self.cleaned_images)}")
        
        # 显示源文件
        self.display_image_on_canvas(
            self.left_canvas,
            self.original_images[page_num],
            left_zoom_factor
        )
        
        # 显示处理后文件
        self.display_image_on_canvas(
            self.right_canvas,
            self.cleaned_images[page_num],
            right_zoom_factor
        )
        
        print(f"第 {page_num + 1} 页显示完成")
    
    def display_image_on_canvas(self, canvas, image, zoom_factor):
        """在画布上显示图片"""
        print(f"display_image_on_canvas 被调用, 画布: {canvas}, 图片尺寸: {image.size}")
        
        canvas.delete("all")
        
        # 计算缩放后的尺寸
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        print(f"画布尺寸: {canvas_width} x {canvas_height}")
        
        if canvas_width <= 1 or canvas_height <= 1:
            print("画布尺寸无效,等待更新...")
            canvas.update()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            print(f"更新后画布尺寸: {canvas_width} x {canvas_height}")
        
        img_width, img_height = image.size
        
        # 应用缩放
        new_width = int(img_width * zoom_factor)
        new_height = int(img_height * zoom_factor)
        
        print(f"缩放后图片尺寸: {new_width} x {new_height}")
        
        # 缩放图片
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # 为每个画布创建独立的PhotoImage对象
        photo = ImageTk.PhotoImage(resized_image)
        
        # 将PhotoImage对象保存到画布的属性中,防止被垃圾回收
        canvas.photo = photo
        
        # 计算居中位置
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        
        print(f"图片位置: ({x}, {y})")
        
        # 显示图片
        canvas.create_image(x, y, image=photo, anchor="nw")
        
        # 保存图片信息用于滚动
        canvas.image_info = {
            'x': x,
            'y': y,
            'width': new_width,
            'height': new_height,
            'original_image': image
        }
        
        print("图片显示完成")
    
    def on_left_scroll(self, event):
        """左侧画布滚动事件"""
        self.on_scroll(event, 'left')
    
    def on_right_scroll(self, event):
        """右侧画布滚动事件"""
        self.on_scroll(event, 'right')
    
    def on_scroll(self, event, side):
        """滚动事件处理 - 同步滚动"""
        # 确定滚动方向
        if event.num == 5 or event.delta < 0:
            direction = 1  # 向下滚动
        else:
            direction = -1  # 向上滚动
        
        # 切换页面
        new_page = self.current_page + direction
        if 0 <= new_page < self.total_pages:
            self.display_page(new_page)
    
    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.display_page(self.current_page - 1)
    
    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages - 1:
            self.display_page(self.current_page + 1)
    
    def on_left_zoom_change(self, value):
        """左侧缩放改变"""
        print(f"左侧缩放改变为: {value}")
        # 只重新显示左侧画布
        zoom_factor = float(value)
        if 0 <= self.current_page < self.total_pages:
            self.display_image_on_canvas(
                self.left_canvas,
                self.original_images[self.current_page],
                zoom_factor
            )
    
    def on_right_zoom_change(self, value):
        """右侧缩放改变"""
        print(f"右侧缩放改变为: {value}")
        # 只重新显示右侧画布
        zoom_factor = float(value)
        if 0 <= self.current_page < self.total_pages:
            self.display_image_on_canvas(
                self.right_canvas,
                self.cleaned_images[self.current_page],
                zoom_factor
            )


class InteractiveAdRemoverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF广告移除工具 - 保留区域模式")
        self.root.geometry("1400x800")
        
        # 数据存储
        self.pdf_file_path = None
        self.output_pdf_path = None
        self.all_pages_images = []  # 存储所有页面的图片
        self.all_pages_cv2 = []     # 存储所有页面的OpenCV格式图片
        self.current_page = 0       # 当前显示的页码
        self.total_pages = 0        # 总页数
        self.keep_regions = {}      # 存储每页的保留区域 {页码: [(x1, y1, x2, y2), ...]}
        self.drag_start = None
        self.current_rect = None
        self.rect_id = None
        self.scale = 1.0
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        """创建GUI组件 - 左右结构"""
        # 左侧预览区域(50%)
        left_frame = tk.Frame(self.root, bg="#2c3e50")
        left_frame.pack(side="left", fill="both", expand=True)
        
        # 预览区域标题
        preview_title = tk.Label(
            left_frame,
            text="📄 PDF预览区域",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        preview_title.pack(pady=10)
        
        # 页面控制栏
        page_control_frame = tk.Frame(left_frame, bg="#2c3e50")
        page_control_frame.pack(pady=5)
        
        self.page_label = tk.Label(
            page_control_frame,
            text="第 1 / 1 页",
            font=("Arial", 12),
            bg="#2c3e50",
            fg="white"
        )
        self.page_label.pack(side="left", padx=10)
        
        prev_button = tk.Button(
            page_control_frame,
            text="◀ 上一页",
            command=self.prev_page,
            width=10,
            bg="#3498db",
            fg="white",
            font=("Arial", 9, "bold")
        )
        prev_button.pack(side="left", padx=3)
        
        next_button = tk.Button(
            page_control_frame,
            text="下一页 ▶",
            command=self.next_page,
            width=10,
            bg="#3498db",
            fg="white",
            font=("Arial", 9, "bold")
        )
        next_button.pack(side="left", padx=3)
        
        # 预览说明
        preview_desc = tk.Label(
            left_frame,
            text="在图片上拖动鼠标选择要保留的区域",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="#bdc3c7"
        )
        preview_desc.pack(pady=5)
        
        # 图片画布
        canvas_frame = tk.Frame(left_frame, bg="white", relief="sunken", borderwidth=3)
        canvas_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white")
        self.canvas.pack(fill="both", expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        
        # 右侧功能区域(50%)
        right_frame = tk.Frame(self.root, bg="#ecf0f1")
        right_frame.pack(side="right", fill="both", expand=True)
        
        # 功能区域标题
        func_title = tk.Label(
            right_frame,
            text="⚙️ 功能控制面板",
            font=("Arial", 16, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        func_title.pack(pady=15)
        
        # 文件选择区域
        file_frame = tk.LabelFrame(right_frame, text="📁 文件选择", font=("Arial", 11, "bold"), bg="#ecf0f1")
        file_frame.pack(fill="x", padx=15, pady=10)
        
        # PDF文件选择
        pdf_label = tk.Label(file_frame, text="PDF文件:", font=("Arial", 10), bg="#ecf0f1")
        pdf_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        pdf_entry_frame = tk.Frame(file_frame, bg="#ecf0f1")
        pdf_entry_frame.pack(fill="x", padx=10, pady=5)
        
        self.pdf_entry = tk.Entry(pdf_entry_frame, width=50, font=("Arial", 10))
        self.pdf_entry.pack(side="left", fill="x", expand=True)
        
        browse_button = tk.Button(
            pdf_entry_frame,
            text="浏览...",
            command=self.select_pdf_file,
            width=10,
            bg="#3498db",
            fg="white",
            font=("Arial", 9, "bold")
        )
        browse_button.pack(side="left", padx=5)
        
        # 保留区域列表
        region_frame = tk.LabelFrame(right_frame, text="📋 已选择的保留区域", font=("Arial", 11, "bold"), bg="#ecf0f1")
        region_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # 区域列表
        region_list_frame = tk.Frame(region_frame, bg="#ecf0f1")
        region_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(region_list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.region_listbox = tk.Listbox(
            region_list_frame,
            yscrollcommand=scrollbar.set,
            height=8,
            font=("Arial", 9),
            selectbackground="#3498db"
        )
        self.region_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.region_listbox.yview)
        
        # 按钮框架
        button_frame = tk.Frame(region_frame, bg="#ecf0f1")
        button_frame.pack(fill="x", padx=10, pady=5)
        
        delete_button = tk.Button(
            button_frame,
            text="🗑️ 删除选中",
            command=self.delete_selected_region,
            width=15,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9, "bold")
        )
        delete_button.pack(side="left", padx=3)
        
        clear_button = tk.Button(
            button_frame,
            text="🧹 清空全部",
            command=self.clear_all_regions,
            width=15,
            bg="#f39c12",
            fg="white",
            font=("Arial", 9, "bold")
        )
        clear_button.pack(side="left", padx=3)
        
        # 区域信息
        info_frame = tk.Frame(region_frame, bg="#ecf0f1")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        self.info_label = tk.Label(
            info_frame,
            text="保留区域数量: 0",
            font=("Arial", 10, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        self.info_label.pack(anchor="w")
        
        # 处理选项
        options_frame = tk.LabelFrame(right_frame, text="⚙️ 处理选项", font=("Arial", 11, "bold"), bg="#ecf0f1")
        options_frame.pack(fill="x", padx=15, pady=10)
        
        # 框选模式选项
        mode_frame = tk.Frame(options_frame, bg="#ecf0f1")
        mode_frame.pack(fill="x", padx=10, pady=5)
        
        mode_label = tk.Label(
            mode_frame,
            text="框选模式:",
            font=("Arial", 10, "bold"),
            bg="#ecf0f1"
        )
        mode_label.pack(anchor="w")
        
        self.region_mode_var = tk.StringVar(value="all")
        
        all_pages_radio = tk.Radiobutton(
            mode_frame,
            text="应用到所有页",
            variable=self.region_mode_var,
            value="all",
            font=("Arial", 9),
            bg="#ecf0f1",
            command=self.on_mode_change
        )
        all_pages_radio.pack(anchor="w", padx=10)
        
        per_page_radio = tk.Radiobutton(
            mode_frame,
            text="每页各自框选",
            variable=self.region_mode_var,
            value="per_page",
            font=("Arial", 9),
            bg="#ecf0f1",
            command=self.on_mode_change
        )
        per_page_radio.pack(anchor="w", padx=10)
        
        # 去除白边选项
        self.remove_margin_var = tk.BooleanVar(value=True)
        remove_margin_check = tk.Checkbutton(
            options_frame,
            text="去除保留区域外的白边",
            variable=self.remove_margin_var,
            font=("Arial", 10),
            bg="#ecf0f1"
        )
        remove_margin_check.pack(anchor="w", padx=10, pady=5)
        
        # 对比预览选项
        self.show_compare_var = tk.BooleanVar(value=True)
        compare_check = tk.Checkbutton(
            options_frame,
            text="处理后显示对比预览",
            variable=self.show_compare_var,
            font=("Arial", 10),
            bg="#ecf0f1"
        )
        compare_check.pack(anchor="w", padx=10, pady=5)
        
        # 处理按钮
        process_frame = tk.Frame(right_frame, bg="#ecf0f1")
        process_frame.pack(fill="x", padx=15, pady=15)
        
        self.process_button = tk.Button(
            process_frame,
            text="✅ 应用并处理PDF",
            command=self.start_processing,
            font=("Arial", 14, "bold"),
            bg="#27ae60",
            fg="white",
            width=25,
            height=2,
            relief="raised"
        )
        self.process_button.pack()
        
        # 进度条
        self.progress = ttk.Progressbar(
            right_frame,
            mode="indeterminate",
            length=400
        )
        self.progress.pack(pady=10)
        
        # 状态标签
        self.status_label = tk.Label(
            right_frame,
            text="👋 欢迎!请选择PDF文件开始处理",
            font=("Arial", 11),
            bg="#ecf0f1",
            fg="#7f8c8d"
        )
        self.status_label.pack(pady=10)
        
        # 操作说明
        help_frame = tk.LabelFrame(right_frame, text="💡 操作说明", font=("Arial", 11, "bold"), bg="#ecf0f1")
        help_frame.pack(fill="x", padx=15, pady=10)
        
        help_text = """
1. 点击"浏览"选择PDF文件
2. 点击"加载预览"查看第一页
3. 在图片上拖动鼠标选择要保留的区域
4. 可选择多个保留区域
5. 点击"应用并处理PDF"完成处理
6. 处理完成后可查看对比预览
        """
        help_label = tk.Label(
            help_frame,
            text=help_text,
            font=("Arial", 9),
            bg="#ecf0f1",
            fg="#34495e",
            justify="left"
        )
        help_label.pack(anchor="w", padx=10, pady=5)
    
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
            self.status_label.config(text=f"✅ 已选择: {os.path.basename(file_path)}, 正在加载...", fg="#f39c12")
            
            # 自动加载PDF
            self.load_first_page()
    
    def load_first_page(self):
        """加载PDF的所有页面"""
        if not self.pdf_file_path or not os.path.exists(self.pdf_file_path):
            messagebox.showerror("错误", "请先选择有效的PDF文件!")
            return
        
        try:
            import fitz
            import io
            
            self.status_label.config(text="⏳ 正在加载所有页面...", fg="#f39c12")
            self.root.update()
            
            # 清空之前的数据
            self.all_pages_images = []
            self.all_pages_cv2 = []
            self.keep_regions = {}
            self.current_page = 0
            self.region_mode_var.set("all")  # 重置为应用到所有页模式
            
            # 打开PDF文件
            pdf_document = fitz.open(self.pdf_file_path)
            
            self.total_pages = len(pdf_document)
            
            if self.total_pages == 0:
                messagebox.showerror("错误", "PDF文件为空!")
                return
            
            # 加载所有页面 - 使用原始尺寸
            for i in range(self.total_pages):
                self.status_label.config(text=f"⏳ 正在加载第 {i+1}/{self.total_pages} 页...", fg="#f39c12")
                self.root.update()
                
                # 获取页面
                page = pdf_document[i]
                
                # 获取原始页面尺寸
                page_rect = page.rect
                self.original_page_width = int(page_rect.width)
                self.original_page_height = int(page_rect.height)
                
                # 将页面转换为图片 - 使用原始尺寸(1倍缩放)
                mat = fitz.Matrix(1, 1)
                pix = page.get_pixmap(matrix=mat)
                
                # 转换为OpenCV格式
                img_data = pix.tobytes("png")
                cv2_image = cv2.imdecode(
                    np.frombuffer(img_data, np.uint8),
                    cv2.IMREAD_COLOR
                )
                self.all_pages_cv2.append(cv2_image)
                
                # 转换为PIL Image用于显示
                pil_image = Image.fromarray(
                    cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
                )
                self.all_pages_images.append(pil_image)
                
                print(f"第{i+1}页加载完成: 原始尺寸={self.original_page_width}x{self.original_page_height}, 图片尺寸={pil_image.size}")
            
            pdf_document.close()
            
            # 显示第一页
            self.display_current_page()
            
            self.status_label.config(text=f"✅ 所有 {self.total_pages} 页加载完成!请在图片上标注要保留的区域", fg="#27ae60")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载PDF失败:\n{str(e)}")
            self.status_label.config(text="❌ 加载失败", fg="#e74c3c")
    
    def on_mode_change(self):
        """框选模式改变时的处理"""
        mode = self.region_mode_var.get()
        
        # 更新区域列表显示
        self.update_region_listbox()
        
        # 重新显示当前页面
        self.canvas.delete("all")
        self.display_image()
        
        # 显示模式切换提示
        if mode == "all":
            self.status_label.config(text="已切换到'应用到所有页'模式", fg="#3498db")
        else:
            self.status_label.config(text="已切换到'每页各自框选'模式", fg="#3498db")
    
    def on_canvas_resize(self, event):
        """画布大小改变时重新显示图片"""
        if len(self.all_pages_images) > 0:
            self.display_current_page()
    
    def display_current_page(self):
        """显示当前页面"""
        if self.current_page >= len(self.all_pages_images):
            return
        
        # 更新页面标签
        self.page_label.config(text=f"第 {self.current_page + 1} / {self.total_pages} 页")
        
        # 获取当前页面的图片
        self.first_page_image = self.all_pages_images[self.current_page]
        
        # 更新区域列表显示
        self.update_region_listbox()
        
        # 显示图片
        self.display_image()
    
    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_current_page()
    
    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_current_page()
    
    def display_image(self):
        """显示图片"""
        if self.first_page_image is None:
            return
        
        # 计算合适的显示尺寸
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        img_width, img_height = self.first_page_image.size
        
        # 计算缩放比例,留出一些边距
        margin = 20
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin
        
        scale = min(available_width / img_width, available_height / img_height, 1.0)
        self.scale = scale
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # 缩放图片
        display_image = self.first_page_image.resize((new_width, new_height), Image.LANCZOS)
        
        # 显示图片
        self.photo = ImageTk.PhotoImage(display_image)
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.photo,
            anchor="center"
        )
        
        # 计算图片在画布上的位置
        self.image_x1 = (canvas_width - new_width) // 2
        self.image_y1 = (canvas_height - new_height) // 2
        self.image_x2 = self.image_x1 + new_width
        self.image_y2 = self.image_y1 + new_height
        
        # 绘制图片边框
        self.canvas.create_rectangle(
            self.image_x1 - 2, self.image_y1 - 2,
            self.image_x2 + 2, self.image_y2 + 2,
            outline="#3498db", width=2
        )
        
        # 重绘所有已选择的区域
        self.redraw_regions()
    
    def on_mouse_press(self, event):
        """鼠标按下事件"""
        if self.first_page_image is None:
            return
        
        # 检查是否在图片区域内
        if not (self.image_x1 <= event.x <= self.image_x2 and 
                self.image_y1 <= event.y <= self.image_y2):
            return
        
        self.drag_start = (event.x, event.y)
    
    def on_mouse_drag(self, event):
        """鼠标拖动事件"""
        if self.drag_start is None:
            return
        
        # 删除之前的临时矩形
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        # 绘制新的临时矩形
        x1 = min(self.drag_start[0], event.x)
        y1 = min(self.drag_start[1], event.y)
        x2 = max(self.drag_start[0], event.x)
        y2 = max(self.drag_start[1], event.y)
        
        # 限制在图片区域内
        x1 = max(self.image_x1, x1)
        y1 = max(self.image_y1, y1)
        x2 = min(self.image_x2, x2)
        y2 = min(self.image_y2, y2)
        
        self.rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="#27ae60",
            width=3,
            dash=(5, 5)
        )
        
        self.current_rect = (x1, y1, x2, y2)
    
    def on_mouse_release(self, event):
        """鼠标释放事件"""
        if self.drag_start is None or self.current_rect is None:
            return
        
        # 转换为图片坐标(相对于图片左上角)
        x1 = int((self.current_rect[0] - self.image_x1) / self.scale)
        y1 = int((self.current_rect[1] - self.image_y1) / self.scale)
        x2 = int((self.current_rect[2] - self.image_x1) / self.scale)
        y2 = int((self.current_rect[3] - self.image_y1) / self.scale)
        
        # 确保坐标正确
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        # 检查区域是否有效
        if x2 - x1 > 20 and y2 - y1 > 20:
            # 使用原始尺寸,不需要坐标转换
            region = {
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2
            }
            
            print(f"标注区域: ({x1}, {y1}) -> ({x2}, {y2})")
            print(f"图片尺寸: {self.first_page_image.size}")
            
            # 根据框选模式处理
            mode = self.region_mode_var.get()
            
            if mode == "all":
                # 应用到所有页
                for page_num in range(self.total_pages):
                    if page_num not in self.keep_regions:
                        self.keep_regions[page_num] = []
                    self.keep_regions[page_num].append(region.copy())
            else:
                # 每页各自框选
                if self.current_page not in self.keep_regions:
                    self.keep_regions[self.current_page] = []
                self.keep_regions[self.current_page].append(region)
            
            # 更新列表显示
            self.update_region_listbox()
            
            # 绘制永久矩形
            display_x1 = self.image_x1 + x1 * self.scale
            display_y1 = self.image_y1 + y1 * self.scale
            display_x2 = self.image_x1 + x2 * self.scale
            display_y2 = self.image_y1 + y2 * self.scale
            
            self.canvas.create_rectangle(
                display_x1, display_y1, display_x2, display_y2,
                outline="#27ae60",
                width=2
            )
            
            # 添加区域编号标签
            current_regions = self.keep_regions.get(self.current_page, [])
            self.canvas.create_text(
                (display_x1 + display_x2) // 2,
                (display_y1 + display_y2) // 2,
                text=str(len(current_regions)),
                fill="#27ae60",
                font=("Arial", 16, "bold")
            )
        
        # 清除临时矩形
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        
        self.drag_start = None
        self.current_rect = None
    
    def update_region_listbox(self):
        """更新区域列表"""
        self.region_listbox.delete(0, tk.END)
        
        mode = self.region_mode_var.get()
        
        if mode == "all":
            # 应用到所有页模式 - 显示总区域信息
            total_regions = sum(len(regions) for regions in self.keep_regions.values())
            
            if total_regions > 0:
                # 显示第一页的区域作为参考
                if 0 in self.keep_regions:
                    for i, region in enumerate(self.keep_regions[0]):
                        width = region['x2'] - region['x1']
                        height = region['y2'] - region['y1']
                        text = f"区域{i+1}: 位置({region['x1']}, {region['y1']}) 大小{width}×{height} [应用到所有{self.total_pages}页]"
                        self.region_listbox.insert(tk.END, text)
                
                self.info_label.config(text=f"保留区域数量: {len(self.keep_regions.get(0, []))} (应用到所有{self.total_pages}页)")
            else:
                self.info_label.config(text=f"保留区域数量: 0 (应用到所有{self.total_pages}页)")
        else:
            # 每页各自框选模式 - 显示当前页的区域
            if self.current_page in self.keep_regions:
                for i, region in enumerate(self.keep_regions[self.current_page]):
                    width = region['x2'] - region['x1']
                    height = region['y2'] - region['y1']
                    text = f"第{self.current_page+1}页 区域{i+1}: 位置({region['x1']}, {region['y1']}) 大小{width}×{height}"
                    self.region_listbox.insert(tk.END, text)
            
            # 计算总区域数
            total_regions = sum(len(regions) for regions in self.keep_regions.values())
            self.info_label.config(text=f"保留区域数量: {total_regions} (当前页: {len(self.keep_regions.get(self.current_page, []))})")
    
    def redraw_regions(self):
        """重绘当前页的所有已选择的区域"""
        if self.current_page in self.keep_regions:
            for i, region in enumerate(self.keep_regions[self.current_page]):
                # 现在使用原始尺寸,直接使用坐标
                display_x1 = self.image_x1 + region['x1'] * self.scale
                display_y1 = self.image_y1 + region['y1'] * self.scale
                display_x2 = self.image_x1 + region['x2'] * self.scale
                display_y2 = self.image_y1 + region['y2'] * self.scale
                
                self.canvas.create_rectangle(
                    display_x1, display_y1, display_x2, display_y2,
                    outline="#27ae60",
                    width=2
                )
                
                # 添加区域编号标签
                center_x = (display_x1 + display_x2) // 2
                center_y = (display_y1 + display_y2) // 2
                self.canvas.create_text(
                    center_x, center_y,
                    text=str(i + 1),
                    fill="#27ae60",
                    font=("Arial", 16, "bold")
                )
    
    def delete_selected_region(self):
        """删除选中的区域"""
        selection = self.region_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的区域!")
            return
        
        mode = self.region_mode_var.get()
        index = selection[0]
        
        if mode == "all":
            # 应用到所有页模式 - 删除所有页对应的区域
            for page_num in range(self.total_pages):
                if page_num in self.keep_regions and index < len(self.keep_regions[page_num]):
                    del self.keep_regions[page_num][index]
                    # 如果该页没有区域了,删除该页的键
                    if not self.keep_regions[page_num]:
                        del self.keep_regions[page_num]
        else:
            # 每页各自框选模式 - 只删除当前页的区域
            if self.current_page not in self.keep_regions:
                return
            
            del self.keep_regions[self.current_page][index]
            # 如果该页没有区域了,删除该页的键
            if not self.keep_regions[self.current_page]:
                del self.keep_regions[self.current_page]
        
        # 更新显示
        self.update_region_listbox()
        self.canvas.delete("all")
        self.display_image()
    
    def clear_all_regions(self):
        """清空所有区域"""
        total_regions = sum(len(regions) for regions in self.keep_regions.values())
        if total_regions == 0:
            return
        
        mode = self.region_mode_var.get()
        
        if mode == "all":
            confirm_text = f"确定要清空所有 {len(self.keep_regions.get(0, []))} 个保留区域吗?\n(这将从所有 {self.total_pages} 页中删除)"
        else:
            confirm_text = f"确定要清空所有 {total_regions} 个保留区域吗?"
        
        if messagebox.askyesno("确认", confirm_text):
            self.keep_regions = {}
            self.update_region_listbox()
            self.canvas.delete("all")
            self.display_image()
    
    def start_processing(self):
        """开始处理PDF"""
        # 验证输入
        if not self.pdf_file_path or not os.path.exists(self.pdf_file_path):
            messagebox.showerror("错误", "请选择有效的PDF文件!")
            return
        
        if not self.keep_regions:
            messagebox.showwarning("警告", "请先在图片上标注要保留的区域!")
            return
        
        # 禁用按钮,防止重复点击
        self.process_button.config(state="disabled", text="处理中...")
        self.progress.start()
        self.status_label.config(text="⏳ 正在处理PDF...", fg="#f39c12")
        
        # 在新线程中处理,避免阻塞GUI
        thread = threading.Thread(target=self.process_pdf)
        thread.start()
    
    def process_pdf(self):
        """处理PDF文件"""
        try:
            # 创建保留区域处理器
            remover = KeepRegionRemover(
                self.keep_regions,
                self.remove_margin_var.get()
            )
            
            # 处理PDF
            output_pdf = remover.process_pdf(self.pdf_file_path)
            self.output_pdf_path = output_pdf
            
            # 处理完成
            self.root.after(0, lambda: self.processing_completed(True, output_pdf))
            
        except Exception as e:
            # 处理失败
            self.root.after(0, lambda: self.processing_completed(False, str(e)))
    
    def processing_completed(self, success, result):
        """处理完成回调"""
        self.progress.stop()
        self.process_button.config(state="normal", text="✅ 应用并处理PDF")
        
        if success:
            self.status_label.config(
                text=f"🎉 处理完成! 输出文件: {os.path.basename(result)}",
                fg="#27ae60"
            )
            
            # 直接显示对比预览,不弹窗询问
            if self.show_compare_var.get():
                self.show_compare_preview()
            else:
                messagebox.showinfo(
                    "成功",
                    f"处理完成!\n输出文件: {result}"
                )
        else:
            self.status_label.config(
                text=f"❌ 处理失败: {result}",
                fg="#e74c3c"
            )
            messagebox.showerror("错误", f"处理失败:\n{result}")
    
    def show_compare_preview(self):
        """显示对比预览窗口"""
        if self.pdf_file_path and self.output_pdf_path:
            compare_window = tk.Toplevel(self.root)
            compare_gui = ComparePreviewGUI(
                compare_window,
                self.pdf_file_path,
                self.output_pdf_path
            )


class KeepRegionRemover:
    """保留区域处理器"""
    
    def __init__(self, keep_regions, remove_margins=True):
        """
        初始化保留区域处理器
        
        Args:
            keep_regions: 要保留的区域字典 {页码: [{'x1':, 'y1':, 'x2':, 'y2':}, ...]}
            remove_margins: 是否去除保留区域外的白边
        """
        self.keep_regions = keep_regions
        self.remove_margins = remove_margins
    
    def process_pdf(self, pdf_path, output_pdf_path=None):
        """
        处理PDF文件,保留指定区域并去除白边
        
        Args:
            pdf_path: 输入PDF文件路径
            output_pdf_path: 输出PDF文件路径
            
        Returns:
            处理后的PDF文件路径
        """
        try:
            import fitz
            import io
        except ImportError:
            raise Exception("请先安装pymupdf: pip install pymupdf")
        
        # 设置输出PDF路径
        if output_pdf_path is None:
            base_name = os.path.splitext(pdf_path)[0]
            output_pdf_path = f"{base_name}_cleaned.pdf"
        
        # 打开PDF文件
        pdf_document = fitz.open(pdf_path)
        
        # 创建新的PDF文档
        output_pdf = fitz.open()
        
        for i, page in enumerate(pdf_document):
            # 获取页面的原始尺寸
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height
            
            print(f"\n处理第 {i+1} 页:")
            print(f"  原始PDF尺寸: {page_width:.0f}x{page_height:.0f}")
            
            # 使用原始分辨率转换页面为图片
            mat = fitz.Matrix(1, 1)  # 使用1倍缩放,保持原始分辨率
            pix = page.get_pixmap(matrix=mat)
            
            print(f"  Pixmap尺寸: {pix.width}x{pix.height}")
            
            # 转换为OpenCV格式
            img_data = pix.tobytes("png")
            image = cv2.imdecode(
                np.frombuffer(img_data, np.uint8),
                cv2.IMREAD_COLOR
            )
            
            print(f"  OpenCV图像尺寸: {image.shape[1]}x{image.shape[0]}")
            
            # 处理保留区域(使用当前页的区域)
            current_regions = self.keep_regions.get(i, [])
            print(f"  保留区域数量: {len(current_regions)}")
            for j, region in enumerate(current_regions):
                print(f"    区域{j+1}: ({region['x1']}, {region['y1']}) -> ({region['x2']}, {region['y2']})")
            
            image = self.process_keep_regions(image, current_regions)
            
            print(f"  处理后图像尺寸: {image.shape[1]}x{image.shape[0]}")
            
            # 如果需要去除白边
            if self.remove_margins:
                image = self.remove_white_margins(image)
                print(f"  去除白边后尺寸: {image.shape[1]}x{image.shape[0]}")
            
            # 转换为PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # 转换为字节流,使用PNG格式保持原始清晰度
            img_bytes = io.BytesIO()
            pil_image.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            
            # 创建新页面,使用处理后的图片尺寸
            new_page = output_pdf.new_page(
                width=pil_image.width,
                height=pil_image.height
            )
            new_page.insert_image(
                new_page.rect,
                stream=img_bytes.getvalue()
            )
            
            print(f"  最终输出尺寸: {pil_image.width}x{pil_image.height}")
        
        # 保存输出PDF,启用压缩
        output_pdf.save(output_pdf_path, deflate=True)
        output_pdf.close()
        pdf_document.close()
        
        return output_pdf_path
    
    def process_keep_regions(self, image, regions):
        """
        处理保留区域,将保留区域外的内容用白色覆盖
        
        Args:
            image: OpenCV图像对象
            regions: 当前页的保留区域列表 [{'x1':, 'y1':, 'x2':, 'y2':}, ...]
            
        Returns:
            处理后的图像
        """
        # 如果没有保留区域,返回原图
        if not regions:
            return image
        
        # 创建白色覆盖层
        white_color = (255, 255, 255)
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        
        # 为每个保留区域创建掩码
        for region in regions:
            x1 = region['x1']
            y1 = region['y1']
            x2 = region['x2']
            y2 = region['y2']
            
            # 确保坐标在图像范围内
            height, width = image.shape[:2]
            x1 = max(0, min(x1, width))
            y1 = max(0, min(y1, height))
            x2 = max(0, min(x2, width))
            y2 = max(0, min(y2, height))
            
            # 在掩码上标记保留区域
            mask[y1:y2, x1:x2] = 255
        
        # 创建白色图像
        white_image = np.full(image.shape, white_color, dtype=np.uint8)
        
        # 使用掩码合并图像
        result = np.where(mask[:, :, np.newaxis] == 255, image, white_image)
        
        return result
    
    def remove_white_margins(self, image):
        """
        去除图片四周的白边
        
        Args:
            image: OpenCV图像对象
            
        Returns:
            去除白边后的图像
        """
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 使用阈值检测白色区域
        _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
        
        # 查找非白色区域的边界
        coords = cv2.findNonZero(cv2.bitwise_not(binary))
        
        if coords is None:
            # 如果整个图片都是白色,返回原图
            return image
        
        # 获取边界坐标
        x, y, w, h = cv2.boundingRect(coords)
        
        # 裁剪图片
        result = image[y:y+h, x:x+w]
        
        return result


def main():
    """主函数"""
    root = tk.Tk()
    app = InteractiveAdRemoverGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()