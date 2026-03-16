"""
PDF广告移除工具 - 交互式标注版本(保留区域模式 + 对比预览)
允许用户选择要保留的区域,自动去除保留区域外的白边
支持源文件和处理后文件的对比预览,左右同步滚动
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import threading
import os
import sys
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
        
        self.left_zoom_var = tk.DoubleVar(value=0.2)
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

        self.right_zoom_var = tk.DoubleVar(value=0.2)
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

        # 绘制边框线(仅在预览时显示,不影响实际文件)
        border_color = "#e74c3c" if canvas == self.right_canvas else "#3498db"
        canvas.create_rectangle(
            x, y, x + new_width, y + new_height,
            outline=border_color,
            width=3
        )

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
        
        # 设置窗口图标
        try:
            if getattr(sys, 'frozen', False):
                # 打包后的可执行文件
                icon_path = os.path.join(sys._MEIPASS, "ico.ico")
            else:
                # 开发环境
                icon_path = os.path.join(os.path.dirname(__file__), "ico.ico")
            
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"无法加载图标: {e}")
        
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
        self.first_page_image = None  # 当前显示的图片

        # 边框调整相关
        self.selected_region_index = None  # 当前选中的区域索引
        self.resize_edge = None  # 当前拖拽的边: 'top', 'bottom', 'left', 'right'
        self.resize_start_pos = None  # 调整开始时的鼠标位置
        self.resize_original_rect = None  # 调整开始时的矩形
        self.handle_size = 8  # 调整手柄的大小

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
        self.canvas.bind("<Motion>", self.on_mouse_move)  # 鼠标移动事件(用于改变光标)
        
        # 右侧功能区域(50%)
        right_frame = tk.Frame(self.root, bg="#ecf0f1")
        right_frame.pack(side="right", fill="both", expand=True)
        
        # 功能区域标题
        func_title = tk.Label(
            right_frame,
            text="⚙️ 功能控制面板",
            font=("Arial", 14, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        func_title.pack(pady=5)

        # 文件选择区域
        file_frame = tk.LabelFrame(right_frame, text="📁 文件选择", font=("Arial", 10, "bold"), bg="#ecf0f1")
        file_frame.pack(fill="x", padx=10, pady=5)

        # PDF文件选择
        pdf_label = tk.Label(file_frame, text="PDF文件:", font=("Arial", 9), bg="#ecf0f1")
        pdf_label.pack(anchor="w", padx=8, pady=(5, 3))

        pdf_entry_frame = tk.Frame(file_frame, bg="#ecf0f1")
        pdf_entry_frame.pack(fill="x", padx=8, pady=3)
        
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
        region_frame = tk.LabelFrame(right_frame, text="📋 已选择的保留区域", font=("Arial", 10, "bold"), bg="#ecf0f1")
        region_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 区域列表
        region_list_frame = tk.Frame(region_frame, bg="#ecf0f1")
        region_list_frame.pack(fill="both", expand=True, padx=8, pady=5)

        scrollbar = tk.Scrollbar(region_list_frame)
        scrollbar.pack(side="right", fill="y")

        self.region_listbox = tk.Listbox(
            region_list_frame,
            yscrollcommand=scrollbar.set,
            height=6,
            font=("Arial", 9),
            selectbackground="#3498db"
        )
        self.region_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.region_listbox.yview)

        # 绑定列表框选择事件
        self.region_listbox.bind("<<ListboxSelect>>", self.on_region_select)

        # 按钮框架
        button_frame = tk.Frame(region_frame, bg="#ecf0f1")
        button_frame.pack(fill="x", padx=8, pady=3)
        
        delete_button = tk.Button(
            button_frame,
            text="🗑️ 删除选中",
            command=self.delete_selected_region,
            width=12,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9, "bold")
        )
        delete_button.pack(side="left", padx=2)

        clear_button = tk.Button(
            button_frame,
            text="🧹 清空全部",
            command=self.clear_all_regions,
            width=12,
            bg="#f39c12",
            fg="white",
            font=("Arial", 9, "bold")
        )
        clear_button.pack(side="left", padx=2)

        # 区域信息
        info_frame = tk.Frame(region_frame, bg="#ecf0f1")
        info_frame.pack(fill="x", padx=8, pady=3)
        
        self.info_label = tk.Label(
            info_frame,
            text="保留区域数量: 0",
            font=("Arial", 9, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        self.info_label.pack(anchor="w")

        # 处理选项
        options_frame = tk.LabelFrame(right_frame, text="⚙️ 处理选项", font=("Arial", 10, "bold"), bg="#ecf0f1")
        options_frame.pack(fill="x", padx=10, pady=5)

        # 框选模式选项
        mode_frame = tk.Frame(options_frame, bg="#ecf0f1")
        mode_frame.pack(fill="x", padx=8, pady=3)
        
        mode_label = tk.Label(
            mode_frame,
            text="框选模式:",
            font=("Arial", 9, "bold"),
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
        all_pages_radio.pack(anchor="w", padx=8)

        per_page_radio = tk.Radiobutton(
            mode_frame,
            text="每页各自框选",
            variable=self.region_mode_var,
            value="per_page",
            font=("Arial", 9),
            bg="#ecf0f1",
            command=self.on_mode_change
        )
        per_page_radio.pack(anchor="w", padx=8)

        # 去除白边选项
        self.remove_margin_var = tk.BooleanVar(value=True)
        remove_margin_check = tk.Checkbutton(
            options_frame,
            text="去除保留区域外的白边",
            variable=self.remove_margin_var,
            font=("Arial", 9),
            bg="#ecf0f1"
        )
        remove_margin_check.pack(anchor="w", padx=8, pady=2)

        # 对比预览选项
        self.show_compare_var = tk.BooleanVar(value=True)
        compare_check = tk.Checkbutton(
            options_frame,
            text="处理后显示对比预览",
            variable=self.show_compare_var,
            font=("Arial", 9),
            bg="#ecf0f1"
        )
        compare_check.pack(anchor="w", padx=8, pady=2)

        # 处理按钮
        process_frame = tk.Frame(right_frame, bg="#ecf0f1")
        process_frame.pack(fill="x", padx=10, pady=8)
        
        self.process_button = tk.Button(
            process_frame,
            text="✅ 应用并处理PDF",
            command=self.start_processing,
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            width=20,
            height=2,
            relief="raised"
        )
        self.process_button.pack()

        # 进度条
        self.progress = ttk.Progressbar(
            right_frame,
            mode="indeterminate",
            length=300
        )
        self.progress.pack(pady=5)

        # 状态标签
        self.status_label = tk.Label(
            right_frame,
            text="👋 欢迎!请选择PDF文件开始处理",
            font=("Arial", 10),
            bg="#ecf0f1",
            fg="#7f8c8d"
        )
        self.status_label.pack(pady=5)

        # 详细说明按钮
        help_frame = tk.Frame(right_frame, bg="#ecf0f1")
        help_frame.pack(fill="x", padx=10, pady=5)

        detail_help_button = tk.Button(
            help_frame,
            text="📖 查看详细说明",
            command=self.show_detailed_help,
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            width=18
        )
        detail_help_button.pack(pady=3)

    def show_detailed_help(self):
        """显示详细说明弹窗"""
        help_window = tk.Toplevel(self.root)
        help_window.title("详细使用说明")
        help_window.geometry("800x600")
        help_window.configure(bg="#ecf0f1")

        # 创建滚动文本框
        text_frame = tk.Frame(help_window, bg="#ecf0f1")
        text_frame.pack(fill="both", expand=True, padx=20, pady=20)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(
            text_frame,
            wrap="word",
            yscrollcommand=scrollbar.set,
            font=("微软雅黑", 10),
            bg="#ffffff",
            fg="#2c3e50",
            padx=10,
            pady=10
        )
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        # 详细说明内容
        help_content = """
═══════════════════════════════════════════════════════════════
                   PDF广告移除工具 - 详细使用说明
═══════════════════════════════════════════════════════════════

【软件简介】
本工具是一款交互式PDF广告/白边移除工具,支持鼠标拖拽标注
保留区域,自动去除保留区域外的内容,适用于扫描文档、学术
论文、电子书等需要去除广告、水印或多余白边的场景。

═══════════════════════════════════════════════════════════════

【基础操作流程】

1️⃣ 选择PDF文件
   • 点击"浏览..."按钮,选择需要处理的PDF文件
   • 选择后自动加载并显示第一页

2️⃣ 标注保留区域
   • 在左侧预览区域的图片上,按住鼠标左键拖拽
   • 拖拽出一个矩形框,标注要保留的内容区域
   • 可以标注多个保留区域

3️⃣ 调整标注区域
   • 点击已标注的区域可以选中它(边框变红色)
   • 拖拽区域边框或角落可以调整大小
   • 点击空白区域或点击其他区域可切换选中

4️⃣ 选择框选模式
   ✓ 应用到所有页:在一页标注的区域应用到所有页面
   ✓ 每页各自框选:每页单独标注不同区域

5️⃣ 处理PDF
   • 点击"✅ 应用并处理PDF"按钮
   • 等待处理完成
   • 自动弹出对比预览窗口

═══════════════════════════════════════════════════════════════

【高级功能】

🔹 区域调整
   • 选中区域后,四个角显示红色手柄
   • 拖拽手柄可同时调整宽高
   • 拖拽边框可单独调整一边
   • 支持八个方向调整(四角+四边)

🔹 区域管理
   • 在右侧列表中可查看所有标注区域
   • 点击列表项可选中对应区域
   • "🗑️ 删除选中":删除当前选中的区域
   • "🧹 清空全部":清空所有标注区域

🔹 页面导航
   • 使用"◀ 上一页"和"下一页 ▶"按钮翻页
   • 顶部显示当前页码(如:第 1 / 5 页)

🔹 对比预览
   • 左侧:源文件(蓝色边框)
   • 右侧:处理后文件(红色边框)
   • 支持独立缩放控制
   • 鼠标滚轮或点击按钮翻页
   • 边框仅为视觉辅助,不影响输出文件

═══════════════════════════════════════════════════════════════

【处理选项】

☑ 去除保留区域外的白边
   • 勾选后,保留区域外的白色区域会被自动裁剪
   • 提高处理后的PDF可读性

☑ 处理后显示对比预览
   • 勾选后,处理完成后自动弹出对比预览窗口
   • 左右对比查看原始文件和处理后文件

═══════════════════════════════════════════════════════════════

【注意事项】

⚠ 文件要求
   • 支持所有标准PDF文件
   • 大文件处理时间较长,请耐心等待
   • 建议先备份原文件

⚠ 标注建议
   • 标注区域建议包含完整的文字内容
   • 区域最小尺寸建议不小于20×20像素
   • 多个区域之间可以重叠

⚠ 输出文件
   • 输出文件名自动添加"_cleaned"后缀
   • 保存在原文件同目录下
   • 清晰度已优化(2倍缩放处理)

⚠ 使用技巧
   • 使用"应用到所有页"模式可大幅提高效率
   • 对于每页内容差异大的PDF,使用"每页各自框选"
   • 处理完成后仔细检查对比预览,确保无误

═══════════════════════════════════════════════════════════════

【常见问题】

Q: 处理后的PDF为什么比原文件大?
A: 因为使用了高分辨率处理(144 DPI),确保清晰度。

Q: 能否撤销已标注的区域?
A: 可以,点击"🗑️ 删除选中"或"🧹 清空全部"按钮。

Q: 处理速度太慢怎么办?
A: 减少标注区域数量,或使用"应用到所有页"模式。

Q: 能否批量处理多个PDF?
A: 目前不支持批量处理,请逐个文件处理。

Q: 边框会出现在最终PDF中吗?
A: 不会,边框仅在预览时显示,不会保存到输出文件。

═══════════════════════════════════════════════════════════════

【技术支持】

• 版本: v1.0
• 开发语言: Python + Tkinter
• 依赖库: PyMuPDF, OpenCV, Pillow

如有问题或建议,请联系开发者。
═══════════════════════════════════════════════════════════════
        """

        # 添加文本内容
        text_widget.insert(tk.END, help_content)
        text_widget.config(state="disabled")  # 设为只读

        # 关闭按钮
        close_button = tk.Button(
            help_window,
            text="关闭",
            command=help_window.destroy,
            font=("微软雅黑", 11, "bold"),
            bg="#e74c3c",
            fg="white",
            width=10,
            height=1
        )
        close_button.pack(pady=10)

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

        # 翻页时取消选中
        self.selected_region_index = None

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
            # 点击空白区域,取消选中
            self.selected_region_index = None
            self.canvas.delete("all")
            self.display_image()
            return

        # 检查是否在选中区域的调整手柄上
        if self.selected_region_index is not None:
            if self.current_page in self.keep_regions:
                region = self.keep_regions[self.current_page][self.selected_region_index]
                edge = self.get_resize_edge(event.x, event.y, region)
                if edge:
                    # 开始调整边框
                    self.resize_edge = edge
                    self.resize_start_pos = (event.x, event.y)
                    self.resize_original_rect = region.copy()
                    return

        # 检查是否在某个区域内
        region_idx = self.get_region_at_position(event.x, event.y)
        if region_idx is not None:
            # 选中该区域
            self.selected_region_index = region_idx
            # 更新列表框选中项
            self.region_listbox.selection_clear(0, tk.END)
            self.region_listbox.selection_set(region_idx)
            # 重新绘制
            self.canvas.delete("all")
            self.display_image()
            return

        # 点击空白区域,开始拖拽创建新区域
        self.selected_region_index = None
        self.drag_start = (event.x, event.y)
    
    def on_mouse_drag(self, event):
        """鼠标拖动事件"""
        # 如果正在调整边框
        if self.resize_edge and self.selected_region_index is not None:
            self.handle_resize_drag(event)
            return

        # 如果正在创建新区域
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

    def handle_resize_drag(self, event):
        """处理边框调整拖动"""
        if self.resize_original_rect is None:
            return

        # 计算鼠标移动的偏移量
        dx = event.x - self.resize_start_pos[0]
        dy = event.y - self.resize_start_pos[1]

        # 转换为原始坐标的偏移量
        orig_dx = dx / self.scale
        orig_dy = dy / self.scale

        # 根据调整的边更新矩形
        new_x1 = self.resize_original_rect['x1']
        new_y1 = self.resize_original_rect['y1']
        new_x2 = self.resize_original_rect['x2']
        new_y2 = self.resize_original_rect['y2']

        edge = self.resize_edge

        if edge == 'left' or edge == 'top_left' or edge == 'bottom_left':
            new_x1 = max(0, min(new_x1 + orig_dx, new_x2 - 10))
        if edge == 'right' or edge == 'top_right' or edge == 'bottom_right':
            new_x2 = max(new_x1 + 10, min(new_x2 + orig_dx, self.first_page_image.size[0]))
        if edge == 'top' or edge == 'top_left' or edge == 'top_right':
            new_y1 = max(0, min(new_y1 + orig_dy, new_y2 - 10))
        if edge == 'bottom' or edge == 'bottom_left' or edge == 'bottom_right':
            new_y2 = max(new_y1 + 10, min(new_y2 + orig_dy, self.first_page_image.size[1]))

        # 更新选中区域的坐标
        self.keep_regions[self.current_page][self.selected_region_index] = {
            'x1': int(new_x1),
            'y1': int(new_y1),
            'x2': int(new_x2),
            'y2': int(new_y2)
        }

        # 重新绘制
        self.canvas.delete("all")
        self.display_image()
    
    def on_mouse_release(self, event):
        """鼠标释放事件"""
        # 如果完成了边框调整
        if self.resize_edge:
            self.resize_edge = None
            self.resize_start_pos = None
            self.resize_original_rect = None
            self.update_region_listbox()
            return

        # 如果完成了新区域创建
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

            # 选中刚创建的区域
            if mode != "all":
                self.selected_region_index = len(self.keep_regions[self.current_page]) - 1
            else:
                self.selected_region_index = len(self.keep_regions.get(0, [])) - 1

            # 更新列表显示
            self.update_region_listbox()

            # 重新绘制所有区域(包括新创建的)
            self.canvas.delete("all")
            self.display_image()

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

                # 判断是否为选中区域,使用不同颜色
                is_selected = (i == self.selected_region_index)
                outline_color = "#e74c3c" if is_selected else "#27ae60"
                line_width = 3 if is_selected else 2

                # 绘制矩形边框
                self.canvas.create_rectangle(
                    display_x1, display_y1, display_x2, display_y2,
                    outline=outline_color,
                    width=line_width
                )

                # 如果是选中区域,绘制调整手柄
                if is_selected:
                    self.draw_resize_handles(display_x1, display_y1, display_x2, display_y2)

                # 添加区域编号标签
                center_x = (display_x1 + display_x2) // 2
                center_y = (display_y1 + display_y2) // 2
                self.canvas.create_text(
                    center_x, center_y,
                    text=str(i + 1),
                    fill=outline_color,
                    font=("Arial", 16, "bold")
                )

    def on_region_select(self, event):
        """区域列表选择事件"""
        selection = self.region_listbox.curselection()
        if selection:
            self.selected_region_index = selection[0]
            self.canvas.delete("all")
            self.display_image()

    def draw_resize_handles(self, x1, y1, x2, y2):
        """绘制调整手柄"""
        h = self.handle_size // 2
        handle_color = "#e74c3c"

        # 四个角的手柄
        handles = [
            (x1 - h, y1 - h, x1 + h, y1 + h),  # 左上
            (x2 - h, y1 - h, x2 + h, y1 + h),  # 右上
            (x2 - h, y2 - h, x2 + h, y2 + h),  # 右下
            (x1 - h, y2 - h, x1 + h, y2 + h),  # 左下
        ]

        for hx1, hy1, hx2, hy2 in handles:
            self.canvas.create_rectangle(
                hx1, hy1, hx2, hy2,
                fill=handle_color,
                outline="white",
                width=2
            )

    def get_resize_edge(self, x, y, region):
        """检测鼠标是否在某个边或角上"""
        h = self.handle_size  # 检测范围
        margin = h  # 边缘检测范围

        x1 = region['x1'] * self.scale + self.image_x1
        y1 = region['y1'] * self.scale + self.image_y1
        x2 = region['x2'] * self.scale + self.image_x1
        y2 = region['y2'] * self.scale + self.image_y1

        # 检测四个角
        if abs(x - x1) <= margin and abs(y - y1) <= margin:
            return 'top_left'
        if abs(x - x2) <= margin and abs(y - y1) <= margin:
            return 'top_right'
        if abs(x - x2) <= margin and abs(y - y2) <= margin:
            return 'bottom_right'
        if abs(x - x1) <= margin and abs(y - y2) <= margin:
            return 'bottom_left'

        # 检测四条边
        if abs(x - x1) <= margin and y1 <= y <= y2:
            return 'left'
        if abs(x - x2) <= margin and y1 <= y <= y2:
            return 'right'
        if abs(y - y1) <= margin and x1 <= x <= x2:
            return 'top'
        if abs(y - y2) <= margin and x1 <= x <= x2:
            return 'bottom'

        return None

    def get_region_at_position(self, x, y):
        """获取指定位置的区域索引"""
        if self.current_page not in self.keep_regions:
            return None

        for i, region in enumerate(self.keep_regions[self.current_page]):
            x1 = region['x1'] * self.scale + self.image_x1
            y1 = region['y1'] * self.scale + self.image_y1
            x2 = region['x2'] * self.scale + self.image_x1
            y2 = region['y2'] * self.scale + self.image_y1

            if x1 <= x <= x2 and y1 <= y <= y2:
                return i

        return None

    def update_cursor(self, event):
        """根据鼠标位置更新光标"""
        if self.first_page_image is None:
            return

        # 检查是否在选中区域的调整手柄上
        if self.selected_region_index is not None:
            if self.current_page in self.keep_regions:
                region = self.keep_regions[self.current_page][self.selected_region_index]
                edge = self.get_resize_edge(event.x, event.y, region)
                if edge:
                    cursor_map = {
                        'top_left': 'size_nw_se',
                        'top_right': 'size_ne_sw',
                        'bottom_right': 'size_nw_se',
                        'bottom_left': 'size_ne_sw',
                        'left': 'sb_h_double_arrow',
                        'right': 'sb_h_double_arrow',
                        'top': 'sb_v_double_arrow',
                        'bottom': 'sb_v_double_arrow'
                    }
                    self.canvas.config(cursor=cursor_map.get(edge, 'arrow'))
                    return

        # 检查是否在某个区域内
        region_idx = self.get_region_at_position(event.x, event.y)
        if region_idx is not None:
            self.canvas.config(cursor='fleur')
            return

        # 默认光标
        self.canvas.config(cursor='arrow')

    def on_mouse_move(self, event):
        """鼠标移动事件"""
        self.update_cursor(event)

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

        # 取消选中状态
        self.selected_region_index = None

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
            self.selected_region_index = None  # 取消选中状态
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

            # 使用高分辨率转换页面为图片(2倍缩放 = ~144 DPI),确保清晰度
            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
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

            # 将区域坐标转换为高分辨率坐标
            scaled_regions = []
            for region in current_regions:
                scaled_region = {
                    'x1': region['x1'] * zoom,
                    'y1': region['y1'] * zoom,
                    'x2': region['x2'] * zoom,
                    'y2': region['y2'] * zoom
                }
                scaled_regions.append(scaled_region)

            image = self.process_keep_regions(image, scaled_regions)
            
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
        
        # 保存输出PDF,使用高质量压缩模式
        output_pdf.save(output_pdf_path, deflate=True, clean=True)
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