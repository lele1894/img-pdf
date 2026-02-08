import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import os
import sys
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading

if sys.platform == "win32":
    os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

class ImageContainer:
    """图像容器类,用于管理原始图像和处理后的图像"""
    def __init__(self):
        self.original_image = None
        self.processed_image = None
        self.display_image = None  # 当前显示的图像
        self.scale = 1.0  # 显示缩放比例

def remove_black_background(image, block_size, c_value):
    """移除黑色背景,保留前景内容"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, block_size, c_value)
    white_background = np.ones_like(image, dtype=np.uint8) * 255
    result = cv2.bitwise_and(image, image, mask=thresh)
    result = cv2.add(result, white_background, mask=cv2.bitwise_not(thresh))
    return result

def update_image(canvas, image, block_size, c_value, image_container=None):
    """处理并显示图像"""
    processed_image = remove_black_background(image, block_size, c_value)
    processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(processed_image)

    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    img_width, img_height = im.size

    scale = min(canvas_width / img_width, canvas_height / img_height)

    # 保存缩放比例
    if image_container:
        image_container.scale = scale

    new_size = (int(img_width * scale), int(img_height * scale))
    im = im.resize(new_size, Image.Resampling.LANCZOS)

    # 保存显示图像
    if image_container:
        image_container.display_image = im

    img_tk = ImageTk.PhotoImage(im)
    canvas.img_tk = img_tk
    canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
    return processed_image

def update_image_async(canvas, image_container, block_size, c_value, callback=None):
    """异步处理图像,避免阻塞UI"""
    if image_container.original_image is None:
        return

    def process():
        try:
            current_block_size = block_size.get()
            if current_block_size % 2 == 0:
                current_block_size += 1
            processed = update_image(canvas, image_container.original_image, current_block_size, c_value.get(), image_container)
            image_container.processed_image = processed
            if callback:
                callback()
        except Exception as e:
            print(f"图像处理错误: {e}")

    thread = threading.Thread(target=process, daemon=True)
    thread.start()

def open_file(canvas, block_size, c_value, image_container, status_label, file_path=None):
    """打开图像文件"""
    if not file_path:
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("图像文件", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff"),
                ("JPEG", "*.jpg;*.jpeg"),
                ("PNG", "*.png"),
                ("BMP", "*.bmp"),
                ("所有文件", "*.*")
            ]
        )
    if file_path:
        try:
            status_label.config(text="📂 正在加载图像...", foreground="blue")
            pil_image = Image.open(file_path)
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            image_container.original_image = image
            update_image_async(canvas, image_container, block_size, c_value)
            status_label.config(text=f"✅ 已加载: {os.path.basename(file_path)} ({image.shape[1]}x{image.shape[0]})", foreground="green")
        except Exception as e:
            status_label.config(text=f"❌ 加载失败: {e}", foreground="red")

def save_file(image_container, status_label):
    """保存处理后的图像"""
    if image_container.processed_image is None:
        status_label.config(text="⚠️ 没有可保存的图像", foreground="orange")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".jpg",
        filetypes=[
            ("JPEG", "*.jpg"),
            ("PNG", "*.png"),
            ("BMP", "*.bmp"),
            ("TIFF", "*.tiff")
        ]
    )
    if file_path:
        try:
            status_label.config(text="💾 正在保存图像...", foreground="blue")

            # 确保路径是unicode字符串
            if isinstance(file_path, bytes):
                file_path = file_path.decode('utf-8')

            # 规范化路径
            file_path = os.path.normpath(file_path)

            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            ext = os.path.splitext(file_path)[1].lower()

            # 统一使用PIL保存,确保中文文件名支持
            pil_img = Image.fromarray(image_container.processed_image)

            if ext == '.jpg' or ext == '.jpeg':
                pil_img.save(file_path, 'JPEG', quality=95)
            elif ext == '.png':
                pil_img.save(file_path, 'PNG', optimize=True)
            elif ext == '.bmp':
                pil_img.save(file_path, 'BMP')
            elif ext == '.tiff':
                pil_img.save(file_path, 'TIFF')

            status_label.config(text=f"✅ 已保存: {os.path.basename(file_path)}", foreground="green")
        except Exception as e:
            status_label.config(text=f"❌ 保存失败: {e}", foreground="red")

def rotate_image(image_container, canvas, block_size, c_value):
    """旋转图像90度"""
    if image_container.original_image is not None:
        image_container.original_image = cv2.rotate(image_container.original_image, cv2.ROTATE_90_CLOCKWISE)
        update_image_async(canvas, image_container, block_size, c_value)

def flip_horizontal(image_container, canvas, block_size, c_value):
    """水平翻转图像"""
    if image_container.original_image is not None:
        image_container.original_image = cv2.flip(image_container.original_image, 1)
        update_image_async(canvas, image_container, block_size, c_value)

def flip_vertical(image_container, canvas, block_size, c_value):
    """垂直翻转图像"""
    if image_container.original_image is not None:
        image_container.original_image = cv2.flip(image_container.original_image, 0)
        update_image_async(canvas, image_container, block_size, c_value)

# 裁剪相关变量
crop_mode = False
crop_start = None
crop_rect = None
crop_canvas_id = None

def start_crop_mode(canvas, image_container, block_size, c_value, status_label):
    """进入裁剪模式"""
    global crop_mode, crop_start, crop_rect, crop_canvas_id

    if image_container.original_image is None:
        status_label.config(text="⚠️ 请先打开图像", foreground="red")
        return

    crop_mode = True
    crop_start = None
    crop_rect = None
    crop_canvas_id = None
    status_label.config(text="✂️ 裁剪模式: 请在图像上拖拽选择区域", foreground="green")

def confirm_crop(canvas, image_container, block_size, c_value, status_label):
    """确认裁剪"""
    global crop_mode, crop_start, crop_rect, crop_canvas_id

    if not crop_mode:
        return

    if crop_rect is None:
        status_label.config(text="⚠️ 请先选择裁剪区域", foreground="orange")
        return

    try:
        # 计算实际图像坐标
        x1, y1, x2, y2 = crop_rect
        scale = image_container.scale

        # 转换为原始图像坐标
        orig_x1 = int(x1 / scale)
        orig_y1 = int(y1 / scale)
        orig_x2 = int(x2 / scale)
        orig_y2 = int(y2 / scale)

        # 确保坐标有效
        orig_x1 = max(0, orig_x1)
        orig_y1 = max(0, orig_y1)
        orig_x2 = min(image_container.original_image.shape[1], orig_x2)
        orig_y2 = min(image_container.original_image.shape[0], orig_y2)

        if orig_x2 <= orig_x1 or orig_y2 <= orig_y1:
            status_label.config(text="❌ 无效的裁剪区域", foreground="red")
            return

        # 裁剪图像
        image_container.original_image = image_container.original_image[orig_y1:orig_y2, orig_x1:orig_x2]

        # 退出裁剪模式
        crop_mode = False
        if crop_canvas_id:
            canvas.delete(crop_canvas_id)
        crop_canvas_id = None
        crop_rect = None

        # 更新图像
        update_image_async(canvas, image_container, block_size, c_value)
        status_label.config(text="✅ 裁剪完成", foreground="green")

    except Exception as e:
        status_label.config(text=f"❌ 裁剪失败: {e}", foreground="red")

def cancel_crop(canvas, status_label):
    """取消裁剪"""
    global crop_mode, crop_start, crop_rect, crop_canvas_id

    crop_mode = False
    crop_start = None
    crop_rect = None

    if crop_canvas_id:
        canvas.delete(crop_canvas_id)
        crop_canvas_id = None

    status_label.config(text="ℹ️ 已取消裁剪", foreground="blue")

def on_canvas_click(event, canvas):
    """画布点击事件"""
    global crop_start, crop_canvas_id

    if not crop_mode:
        return

    crop_start = (event.x, event.y)

    # 删除旧的裁剪框
    if crop_canvas_id:
        canvas.delete(crop_canvas_id)

def on_canvas_drag(event, canvas):
    """画布拖拽事件"""
    global crop_start, crop_rect, crop_canvas_id

    if not crop_mode or crop_start is None:
        return

    x1, y1 = crop_start
    x2, y2 = event.x, event.y

    # 更新裁剪矩形
    crop_rect = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    # 删除旧的裁剪框
    if crop_canvas_id:
        canvas.delete(crop_canvas_id)

    # 绘制新的裁剪框
    crop_canvas_id = canvas.create_rectangle(
        crop_rect[0], crop_rect[1], crop_rect[2], crop_rect[3],
        outline='red', width=2, dash=(5, 5)
    )

def create_ui():
    """创建用户界面"""
    root = TkinterDnD.Tk()
    root.title("处理打印图片背景")
    root.geometry("1280x720")

    # 设置窗口图标
    try:
        # 尝试从多个路径加载图标
        icon_path = None

        # 1. 尝试从PyInstaller打包后的临时目录加载
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "ico.ico")
        # 2. 尝试从脚本所在目录加载
        else:
            icon_path = os.path.join(os.path.dirname(__file__), "ico.ico")

        if icon_path and os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception as e:
        print(f"无法加载图标: {e}")

    block_size = tk.IntVar(value=11)
    c_value = tk.IntVar(value=2)
    image_container = ImageContainer()

    style = ttk.Style()
    style.configure("TButton", padding=6, relief="flat", background="#ccc")
    style.configure("TLabel", padding=6, background="#eee")
    style.configure("TScale", background="#eee")

    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(row=0, column=0, sticky='nsew')

    canvas = tk.Canvas(main_frame, bg='white')
    canvas.grid(row=0, column=0, columnspan=4, sticky='nsew')

    # 绑定画布事件用于裁剪
    canvas.bind("<Button-1>", lambda e: on_canvas_click(e, canvas))
    canvas.bind("<B1-Motion>", lambda e: on_canvas_drag(e, canvas))

    # 模糊程度滑块和标签
    ttk.Label(main_frame, text="模糊程度:").grid(row=1, column=0, sticky='w', padx=5)
    block_size_slider = ttk.Scale(main_frame, from_=3, to=21, orient=tk.HORIZONTAL, variable=block_size)
    block_size_slider.grid(row=1, column=1, sticky='ew', padx=5)
    block_size_spinbox = ttk.Spinbox(main_frame, from_=3, to=21, textvariable=block_size, width=5)
    block_size_spinbox.grid(row=1, column=2, sticky='w', padx=5)

    # 亮度调整滑块和标签
    ttk.Label(main_frame, text="亮度调整:").grid(row=2, column=0, sticky='w', padx=5)
    c_value_slider = ttk.Scale(main_frame, from_=0, to=10, orient=tk.HORIZONTAL, variable=c_value)
    c_value_slider.grid(row=2, column=1, sticky='ew', padx=5)
    c_value_spinbox = ttk.Spinbox(main_frame, from_=0, to=10, textvariable=c_value, width=5)
    c_value_spinbox.grid(row=2, column=2, sticky='w', padx=5)

    # 按钮区域
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=3, column=0, columnspan=4, pady=10, sticky='ew')

    open_button = ttk.Button(button_frame, text="打开图像",
                            command=lambda: open_file(canvas, block_size, c_value, image_container, status_label))
    open_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    save_button = ttk.Button(button_frame, text="保存图像",
                            command=lambda: save_file(image_container, status_label))
    save_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    rotate_button = ttk.Button(button_frame, text="旋转90°",
                              command=lambda: rotate_image(image_container, canvas, block_size, c_value))
    rotate_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    flip_h_button = ttk.Button(button_frame, text="水平翻转",
                              command=lambda: flip_horizontal(image_container, canvas, block_size, c_value))
    flip_h_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    flip_v_button = ttk.Button(button_frame, text="垂直翻转",
                              command=lambda: flip_vertical(image_container, canvas, block_size, c_value))
    flip_v_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    # 裁剪按钮区域
    crop_button_frame = ttk.Frame(main_frame)
    crop_button_frame.grid(row=4, column=0, columnspan=4, pady=5, sticky='ew')

    # 状态栏 - 在按钮之前定义
    status_label = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
    status_label.grid(row=5, column=0, columnspan=4, sticky='ew', pady=5)

    # 现在可以定义按钮了,因为status_label已经存在
    start_crop_button = ttk.Button(crop_button_frame, text="开始裁剪",
                                   command=lambda: start_crop_mode(canvas, image_container, block_size, c_value, status_label))
    start_crop_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    confirm_crop_button = ttk.Button(crop_button_frame, text="确认裁剪",
                                     command=lambda: confirm_crop(canvas, image_container, block_size, c_value, status_label))
    confirm_crop_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    cancel_crop_button = ttk.Button(crop_button_frame, text="取消裁剪",
                                    command=lambda: cancel_crop(canvas, status_label))
    cancel_crop_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    # 拖放事件处理
    def on_drop(event):
        file_path = root.tk.splitlist(event.data)[0]
        if file_path:
            open_file(canvas, block_size, c_value, image_container, status_label, file_path=file_path)

    canvas.drop_target_register(DND_FILES)
    canvas.dnd_bind('<<Drop>>', on_drop)

    # 窗口和框架的布局配置
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)

    # 滑块变化处理
    def on_slider_change(event=None):
        if image_container.original_image is not None:
            update_image_async(canvas, image_container, block_size, c_value)

    # Spinbox变化处理
    def on_spinbox_change():
        if image_container.original_image is not None:
            update_image_async(canvas, image_container, block_size, c_value)

    # 滑块事件绑定
    block_size_slider.bind("<Motion>", on_slider_change)
    c_value_slider.bind("<Motion>", on_slider_change)
    block_size_slider.bind("<ButtonRelease-1>", on_slider_change)
    c_value_slider.bind("<ButtonRelease-1>", on_slider_change)

    # Spinbox事件绑定 - 使用trace监听变量变化
    def on_block_size_change(*args):
        on_spinbox_change()

    def on_c_value_change(*args):
        on_spinbox_change()

    block_size.trace_add("write", on_block_size_change)
    c_value.trace_add("write", on_c_value_change)

    # 键盘事件处理
    def on_key_press(event, slider, var):
        if event.keysym in ['Left', 'Down']:
            var.set(max(var.get() - 1, slider.cget('from')))
        elif event.keysym in ['Right', 'Up']:
            var.set(min(var.get() + 1, slider.cget('to')))
        on_slider_change(event)

    block_size_slider.bind("<KeyPress>", lambda event: on_key_press(event, block_size_slider, block_size))
    c_value_slider.bind("<KeyPress>", lambda event: on_key_press(event, c_value_slider, c_value))

    block_size_slider.bind("<Button-1>", lambda event: block_size_slider.focus_set())
    c_value_slider.bind("<Button-1>", lambda event: c_value_slider.focus_set())

    block_size_slider.focus_set()

    root.mainloop()

if __name__ == "__main__":
    create_ui()
