import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import os
import sys
import threading
import logging
from typing import Optional, Tuple, List, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import time
import traceback
from collections import deque

# 尝试导入拖放支持
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    logging.warning("tkinterdnd2 not available, drag and drop disabled")

if sys.platform == "win32":
    os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_processor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

@dataclass
class CropState:
    """裁剪状态管理"""
    is_active: bool = False
    start: Optional[Tuple[int, int]] = None
    rect: Optional[Tuple[int, int, int, int]] = None
    canvas_id: Optional[int] = None
    handle_ids: List[int] = field(default_factory=list)  # 控制点句柄ID列表
    is_resizing: bool = False  # 是否正在调整大小
    resize_handle: Optional[str] = None  # 当前拖动的控制点: 'tl', 'tm', 'tr', 'mr', 'br', 'bm', 'bl', 'ml'
    resize_start: Optional[Tuple[int, int]] = None  # 调整大小起始点
    resize_rect: Optional[Tuple[int, int, int, int]] = None  # 调整大小起始时的矩形

    # 控制点大小
    HANDLE_SIZE = 10

@dataclass
class ImageHistory:
    """图像历史记录"""
    image: np.ndarray
    operation: str

class ImageContainer:
    """图像容器类，用于管理原始图像和处理后的图像"""
    def __init__(self):
        self.original_image: Optional[np.ndarray] = None
        self.processed_image: Optional[np.ndarray] = None
        self.display_image: Optional[Image.Image] = None
        self.scale: float = 1.0
        self.history: deque[ImageHistory] = deque(maxlen=20)  # 最多保存20步历史
        self.history_index: int = -1
        self._lock = threading.Lock()  # 线程安全锁

    def save_state(self, operation: str) -> None:
        """保存当前状态到历史记录"""
        with self._lock:
            if self.original_image is None:
                return
            # 如果在历史记录中间，删除后面的记录
            if self.history_index < len(self.history) - 1:
                self.history = deque(list(self.history)[:self.history_index + 1], maxlen=20)
            # 添加新记录
            self.history.append(ImageHistory(
                image=self.original_image.copy(),
                operation=operation
            ))
            self.history_index = len(self.history) - 1
            logging.info(f"保存历史记录: {operation}, 当前索引: {self.history_index}")

    def undo(self) -> Optional[np.ndarray]:
        """撤销操作"""
        with self._lock:
            if self.history_index > 0:
                self.history_index -= 1
                self.original_image = self.history[self.history_index].image.copy()
                logging.info(f"撤销操作, 当前索引: {self.history_index}")
                return self.original_image
            return None

    def redo(self) -> Optional[np.ndarray]:
        """重做操作"""
        with self._lock:
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.original_image = self.history[self.history_index].image.copy()
                logging.info(f"重做操作, 当前索引: {self.history_index}")
                return self.original_image
            return None

    def clear(self) -> None:
        """清理资源"""
        with self._lock:
            self.original_image = None
            self.processed_image = None
            self.display_image = None
            self.history.clear()
            self.history_index = -1
            logging.info("图像容器已清理")

    @property
    def can_undo(self) -> bool:
        """是否可以撤销"""
        return self.history_index > 0

    @property
    def can_redo(self) -> bool:
        """是否可以重做"""
        return self.history_index < len(self.history) - 1

class ImageProcessor:
    """图像处理器，包含各种图像处理算法"""

    # 参数缓存，避免相同参数重复处理
    _process_cache: dict = {}

    @staticmethod
    def remove_black_background(image: np.ndarray, block_size: int, c_value: int) -> np.ndarray:
        """
        移除黑色背景，保留前景内容

        Args:
            image: 输入图像 (BGR格式)
            block_size: 自适应阈值块大小 (必须为奇数)
            c_value: 阈值调整参数

        Returns:
            处理后的图像
        """
        # 创建缓存键
        cache_key = (image.tobytes()[:100], block_size, c_value)  # 使用前100字节作为简化键

        if cache_key in ImageProcessor._process_cache:
            logging.debug("使用缓存的图像处理结果")
            return ImageProcessor._process_cache[cache_key].copy()

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, block_size, c_value)
        white_background = np.ones_like(image, dtype=np.uint8) * 255
        result = cv2.bitwise_and(image, image, mask=thresh)
        result = cv2.add(result, white_background, mask=cv2.bitwise_not(thresh))

        # 缓存结果（限制缓存大小）
        if len(ImageProcessor._process_cache) > 10:
            ImageProcessor._process_cache.clear()
        ImageProcessor._process_cache[cache_key] = result.copy()

        return result

    @staticmethod
    def clear_cache() -> None:
        """清除处理缓存"""
        ImageProcessor._process_cache.clear()
        logging.info("处理缓存已清除")


class DebounceTimer:
    """防抖定时器，避免频繁触发"""
    def __init__(self, delay: float, callback: Callable):
        self.delay = delay
        self.callback = callback
        self.timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def trigger(self, *args, **kwargs) -> None:
        """触发回调，防抖处理"""
        with self._lock:
            if self.timer:
                self.timer.cancel()
            self.timer = threading.Timer(self.delay, self.callback, args, kwargs)
            self.timer.start()

    def cancel(self) -> None:
        """取消定时器"""
        with self._lock:
            if self.timer:
                self.timer.cancel()
                self.timer = None


class ImageDisplayer:
    """图像显示管理器"""

    @staticmethod
    def update_canvas(canvas: tk.Canvas, image: np.ndarray, block_size: int,
                     c_value: int, image_container: Optional[ImageContainer] = None) -> np.ndarray:
        """
        处理并显示图像

        Args:
            canvas: Tkinter画布
            image: 原始图像
            block_size: 处理参数
            c_value: 处理参数
            image_container: 图像容器

        Returns:
            处理后的图像
        """
        try:
            processed_image = ImageProcessor.remove_black_background(image, block_size, c_value)
            processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(processed_image)

            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()

            img_width, img_height = im.size

            scale = min(canvas_width / img_width, canvas_height / img_height)

            if image_container:
                image_container.scale = scale

            new_size = (int(img_width * scale), int(img_height * scale))
            im = im.resize(new_size, Image.Resampling.LANCZOS)

            if image_container:
                image_container.display_image = im

            img_tk = ImageTk.PhotoImage(im)
            canvas.img_tk = img_tk
            canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

            return processed_image

        except Exception as e:
            logging.error(f"图像显示错误: {e}\n{traceback.format_exc()}")
            raise

    @staticmethod
    def update_async(canvas: tk.Canvas, image_container: ImageContainer,
                    block_size: tk.IntVar, c_value: tk.IntVar,
                    callback: Optional[Callable] = None,
                    executor: Optional[ThreadPoolExecutor] = None) -> None:
        """
        异步更新图像显示

        Args:
            canvas: Tkinter画布
            image_container: 图像容器
            block_size: 块大小变量
            c_value: 阈值变量
            callback: 完成回调
            executor: 线程池执行器
        """
        if image_container.original_image is None:
            return

        def process() -> None:
            try:
                current_block_size = block_size.get()
                if current_block_size % 2 == 0:
                    current_block_size += 1

                processed = ImageDisplayer.update_canvas(
                    canvas,
                    image_container.original_image,
                    current_block_size,
                    c_value.get(),
                    image_container
                )
                image_container.processed_image = processed

                if callback:
                    callback()

            except Exception as e:
                logging.error(f"异步图像处理错误: {e}\n{traceback.format_exc()}")

        if executor:
            executor.submit(process)
        else:
            thread = threading.Thread(target=process, daemon=True)
            thread.start()

class FileHandler:
    """文件操作处理器"""

    SUPPORTED_FORMATS = [
        ("图像文件", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff;*.webp"),
        ("JPEG", "*.jpg;*.jpeg"),
        ("PNG", "*.png"),
        ("BMP", "*.bmp"),
        ("TIFF", "*.tiff"),
        ("WebP", "*.webp"),
        ("所有文件", "*.*")
    ]

    @staticmethod
    def open_image(file_path: Optional[str] = None) -> Optional[Tuple[np.ndarray, str]]:
        """
        打开图像文件

        Args:
            file_path: 文件路径，如果为None则弹出文件选择对话框

        Returns:
            (图像数据, 文件名) 或 None
        """
        if not file_path:
            file_path = filedialog.askopenfilename(filetypes=FileHandler.SUPPORTED_FORMATS)

        if not file_path:
            return None

        try:
            logging.info(f"正在加载图像: {file_path}")
            pil_image = Image.open(file_path)
            # 转换为RGB模式（如果不是）
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            filename = os.path.basename(file_path)
            logging.info(f"图像加载成功: {filename} ({image.shape[1]}x{image.shape[0]})")
            return image, filename

        except Exception as e:
            logging.error(f"图像加载失败: {e}\n{traceback.format_exc()}")
            return None

    @staticmethod
    def save_image(image: np.ndarray, default_ext: str = ".jpg",
                   quality: int = 95) -> Optional[str]:
        """
        保存图像

        Args:
            image: 图像数据
            default_ext: 默认扩展名
            quality: JPEG质量 (1-100)

        Returns:
            保存的文件路径或None
        """
        file_path = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            filetypes=[
                ("JPEG", "*.jpg"),
                ("PNG", "*.png"),
                ("BMP", "*.bmp"),
                ("TIFF", "*.tiff"),
                ("WebP", "*.webp")
            ]
        )

        if not file_path:
            return None

        try:
            logging.info(f"正在保存图像: {file_path}")

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

            # 使用PIL保存，确保中文文件名支持
            pil_img = Image.fromarray(image)

            save_params = {}
            if ext in ['.jpg', '.jpeg']:
                save_params = {'quality': quality, 'optimize': True}
            elif ext == '.png':
                save_params = {'optimize': True}
            elif ext == '.webp':
                save_params = {'quality': quality}

            pil_img.save(file_path, **save_params)

            filename = os.path.basename(file_path)
            logging.info(f"图像保存成功: {filename}")
            return file_path

        except Exception as e:
            logging.error(f"图像保存失败: {e}\n{traceback.format_exc()}")
            return None


class ImageEditor:
    """图像编辑器"""

    @staticmethod
    def rotate(image_container: ImageContainer) -> bool:
        """旋转图像90度"""
        if image_container.original_image is None:
            return False

        image_container.save_state("旋转90°")
        image_container.original_image = cv2.rotate(
            image_container.original_image,
            cv2.ROTATE_90_CLOCKWISE
        )
        logging.info("图像旋转90度")
        return True

    @staticmethod
    def flip_horizontal(image_container: ImageContainer) -> bool:
        """水平翻转图像"""
        if image_container.original_image is None:
            return False

        image_container.save_state("水平翻转")
        image_container.original_image = cv2.flip(image_container.original_image, 1)
        logging.info("图像水平翻转")
        return True

    @staticmethod
    def flip_vertical(image_container: ImageContainer) -> bool:
        """垂直翻转图像"""
        if image_container.original_image is None:
            return False

        image_container.save_state("垂直翻转")
        image_container.original_image = cv2.flip(image_container.original_image, 0)
        logging.info("图像垂直翻转")
        return True


class CropManager:
    """裁剪管理器"""

    def __init__(self):
        self.state = CropState()

    def start_crop(self, image_container: ImageContainer) -> bool:
        """进入裁剪模式"""
        if image_container.original_image is None:
            return False

        self.state.is_active = True
        self.state.start = None
        self.state.rect = None
        self.state.canvas_id = None
        self.state.handle_ids = []
        self.state.is_resizing = False
        self.state.resize_handle = None
        logging.info("进入裁剪模式")
        return True

    def confirm_crop(self, canvas: tk.Canvas, image_container: ImageContainer) -> bool:
        """确认裁剪"""
        if not self.state.is_active or self.state.rect is None:
            return False

        try:
            x1, y1, x2, y2 = self.state.rect
            scale = image_container.scale

            # 转换为原始图像坐标
            orig_x1 = max(0, int(x1 / scale))
            orig_y1 = max(0, int(y1 / scale))
            orig_x2 = min(image_container.original_image.shape[1], int(x2 / scale))
            orig_y2 = min(image_container.original_image.shape[0], int(y2 / scale))

            if orig_x2 <= orig_x1 or orig_y2 <= orig_y1:
                logging.warning("无效的裁剪区域")
                return False

            # 裁剪图像
            image_container.save_state("裁剪")
            image_container.original_image = image_container.original_image[orig_y1:orig_y2, orig_x1:orig_x2]

            # 清理裁剪状态
            self._cleanup(canvas)
            logging.info(f"裁剪完成: ({orig_x1}, {orig_y1}) -> ({orig_x2}, {orig_y2})")
            return True

        except Exception as e:
            logging.error(f"裁剪失败: {e}\n{traceback.format_exc()}")
            return False

    def cancel_crop(self, canvas: tk.Canvas) -> None:
        """取消裁剪"""
        self._cleanup(canvas)
        logging.info("取消裁剪")

    def _cleanup(self, canvas: tk.Canvas) -> None:
        """清理裁剪状态"""
        self.state.is_active = False
        self.state.start = None
        self.state.rect = None
        self.state.is_resizing = False
        self.state.resize_handle = None
        self.state.resize_start = None
        self.state.resize_rect = None

        # 删除裁剪框和控制点
        if self.state.canvas_id:
            canvas.delete(self.state.canvas_id)
            self.state.canvas_id = None

        for handle_id in self.state.handle_ids:
            canvas.delete(handle_id)
        self.state.handle_ids = []

    def _get_handle_rects(self) -> dict:
        """获取8个控制点的矩形区域"""
        if not self.state.rect:
            return {}

        x1, y1, x2, y2 = self.state.rect
        hs = self.state.HANDLE_SIZE

        # 8个控制点：左上、上中、右上、右中、右下、下中、左下、左中
        handles = {
            'tl': (x1 - hs//2, y1 - hs//2, x1 + hs//2, y1 + hs//2),
            'tm': ((x1 + x2)//2 - hs//2, y1 - hs//2, (x1 + x2)//2 + hs//2, y1 + hs//2),
            'tr': (x2 - hs//2, y1 - hs//2, x2 + hs//2, y1 + hs//2),
            'mr': (x2 - hs//2, (y1 + y2)//2 - hs//2, x2 + hs//2, (y1 + y2)//2 + hs//2),
            'br': (x2 - hs//2, y2 - hs//2, x2 + hs//2, y2 + hs//2),
            'bm': ((x1 + x2)//2 - hs//2, y2 - hs//2, (x1 + x2)//2 + hs//2, y2 + hs//2),
            'bl': (x1 - hs//2, y2 - hs//2, x1 + hs//2, y2 + hs//2),
            'ml': (x1 - hs//2, (y1 + y2)//2 - hs//2, x1 + hs//2, (y1 + y2)//2 + hs//2)
        }
        return handles

    def _get_handle_at_position(self, x: int, y: int) -> Optional[str]:
        """检测鼠标是否在某个控制点上"""
        handles = self._get_handle_rects()
        for handle_name, (hx1, hy1, hx2, hy2) in handles.items():
            if hx1 <= x <= hx2 and hy1 <= y <= hy2:
                return handle_name
        return None

    def _draw_handles(self, canvas: tk.Canvas) -> None:
        """绘制8个控制点"""
        # 删除旧的控制点
        for handle_id in self.state.handle_ids:
            canvas.delete(handle_id)
        self.state.handle_ids = []

        handles = self._get_handle_rects()
        for handle_name, (hx1, hy1, hx2, hy2) in handles.items():
            # 绘制控制点
            handle_id = canvas.create_rectangle(
                hx1, hy1, hx2, hy2,
                fill='white', outline='red', width=2
            )
            self.state.handle_ids.append(handle_id)

    def on_click(self, event: tk.Event, canvas: tk.Canvas) -> None:
        """画布点击事件"""
        if not self.state.is_active:
            return

        # 如果已经有裁剪框，检测是否点击了控制点
        if self.state.rect:
            handle = self._get_handle_at_position(event.x, event.y)
            if handle:
                self.state.is_resizing = True
                self.state.resize_handle = handle
                self.state.resize_start = (event.x, event.y)
                self.state.resize_rect = self.state.rect
                logging.info(f"开始调整裁剪框: {handle}")
                return

        # 如果点击在裁剪框内部，开始拖动整个框（可选功能）
        if self.state.rect:
            x1, y1, x2, y2 = self.state.rect
            if x1 < event.x < x2 and y1 < event.y < y2:
                # 可以在这里实现拖动整个裁剪框
                pass

        # 否则开始新的选择
        self.state.start = (event.x, event.y)
        self.state.is_resizing = False

        if self.state.canvas_id:
            canvas.delete(self.state.canvas_id)
        for handle_id in self.state.handle_ids:
            canvas.delete(handle_id)
        self.state.handle_ids = []

    def on_drag(self, event: tk.Event, canvas: tk.Canvas) -> None:
        """画布拖拽事件"""
        if not self.state.is_active:
            return

        # 调整裁剪框大小
        if self.state.is_resizing and self.state.resize_handle and self.state.resize_rect:
            self._update_resize_rect(event, canvas)
            return

        # 新建裁剪框
        if self.state.start is None:
            return

        x1, y1 = self.state.start
        x2, y2 = event.x, event.y

        # 更新裁剪矩形
        self.state.rect = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

        # 绘制新的裁剪框和控制点
        self._draw_crop_box(canvas)

    def on_release(self, event: tk.Event, canvas: tk.Canvas) -> None:
        """鼠标释放事件"""
        if not self.state.is_active:
            return

        # 停止调整大小
        if self.state.is_resizing:
            self.state.is_resizing = False
            self.state.resize_handle = None
            self.state.resize_start = None
            self.state.resize_rect = None
            logging.info("完成调整裁剪框")

    def _update_resize_rect(self, event: tk.Event, canvas: tk.Canvas) -> None:
        """更新裁剪框大小"""
        if not self.state.resize_rect:
            return

        rx1, ry1, rx2, ry2 = self.state.resize_rect
        dx = event.x - self.state.resize_start[0]
        dy = event.y - self.state.resize_start[1]

        handle = self.state.resize_handle

        # 根据控制点类型调整矩形
        if handle == 'tl':  # 左上角
            self.state.rect = (rx1 + dx, ry1 + dy, rx2, ry2)
        elif handle == 'tm':  # 上中
            self.state.rect = (rx1, ry1 + dy, rx2, ry2)
        elif handle == 'tr':  # 右上角
            self.state.rect = (rx1, ry1 + dy, rx2 + dx, ry2)
        elif handle == 'mr':  # 右中
            self.state.rect = (rx1, ry1, rx2 + dx, ry2)
        elif handle == 'br':  # 右下角
            self.state.rect = (rx1, ry1, rx2 + dx, ry2 + dy)
        elif handle == 'bm':  # 下中
            self.state.rect = (rx1, ry1, rx2, ry2 + dy)
        elif handle == 'bl':  # 左下角
            self.state.rect = (rx1 + dx, ry1, rx2, ry2 + dy)
        elif handle == 'ml':  # 左中
            self.state.rect = (rx1 + dx, ry1, rx2, ry2)

        # 确保矩形有效（不翻转）
        x1, y1, x2, y2 = self.state.rect
        self.state.rect = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

        # 重绘裁剪框和控制点
        self._draw_crop_box(canvas)

    def _draw_crop_box(self, canvas: tk.Canvas) -> None:
        """绘制裁剪框和控制点"""
        # 删除旧的裁剪框和控制点
        if self.state.canvas_id:
            canvas.delete(self.state.canvas_id)
        for handle_id in self.state.handle_ids:
            canvas.delete(handle_id)
        self.state.handle_ids = []

        if not self.state.rect:
            return

        # 绘制新的裁剪框
        self.state.canvas_id = canvas.create_rectangle(
            self.state.rect[0], self.state.rect[1],
            self.state.rect[2], self.state.rect[3],
            outline='red', width=2, dash=(5, 5)
        )

        # 绘制控制点
        self._draw_handles(canvas)

    def on_mouse_move(self, event: tk.Event, canvas: tk.Canvas) -> None:
        """鼠标移动事件（更新光标）"""
        if not self.state.is_active or not self.state.rect:
            canvas.config(cursor='arrow')
            return

        # 检测是否在控制点上
        handle = self._get_handle_at_position(event.x, event.y)
        if handle:
            # 根据控制点位置设置光标（使用 Windows 兼容的光标名称）
            cursor_map = {
                'tl': 'sb_h_double_arrow',   # 左上角
                'tm': 'sb_v_double_arrow',   # 上中
                'tr': 'sb_h_double_arrow',   # 右上角
                'mr': 'sb_h_double_arrow',   # 右中
                'br': 'sb_h_double_arrow',   # 右下角
                'bm': 'sb_v_double_arrow',   # 下中
                'bl': 'sb_h_double_arrow',   # 左下角
                'ml': 'sb_h_double_arrow'    # 左中
            }
            canvas.config(cursor=cursor_map.get(handle, 'arrow'))
        else:
            # 检测是否在裁剪框内部
            x1, y1, x2, y2 = self.state.rect
            if x1 < event.x < x2 and y1 < event.y < y2:
                canvas.config(cursor='fleur')  # 移动光标
            else:
                canvas.config(cursor='arrow')

class ImageProcessorApp:
    """图像处理器主应用类"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("处理打印图片背景 v2.0")
        self.root.geometry("1280x720")

        # 设置窗口图标
        self._setup_icon()

        # 核心组件
        self.image_container = ImageContainer()
        self.crop_manager = CropManager()
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ImageProcessor")
        self.debounce_timer: Optional[DebounceTimer] = None

        # UI变量
        self.block_size = tk.IntVar(value=11)
        self.c_value = tk.IntVar(value=2)
        self.show_original = tk.BooleanVar(value=False)  # 显示原图/效果图切换
        self.zoom_level = tk.DoubleVar(value=1.0)  # 缩放级别

        # 创建UI
        self._create_ui()
        self._setup_shortcuts()
        self._setup_drag_drop()

        # 初始化防抖定时器
        self.debounce_timer = DebounceTimer(
            delay=0.1,
            callback=lambda: self._on_parameter_change()
        )

        logging.info("应用初始化完成")

    def _setup_icon(self) -> None:
        """设置窗口图标"""
        try:
            if getattr(sys, 'frozen', False):
                # 打包后的可执行文件
                icon_path = os.path.join(sys._MEIPASS, "ico.ico")
            else:
                # 开发环境
                icon_path = os.path.join(os.path.dirname(__file__), "ico.ico")

            if icon_path and os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            logging.warning(f"无法加载图标: {e}")

    def _create_ui(self) -> None:
        """创建用户界面"""
        # 样式配置
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.configure("TLabel", padding=6, background="#eee")
        style.configure("TScale", background="#eee")

        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')

        # 画布
        self.canvas = tk.Canvas(main_frame, bg='white')
        self.canvas.grid(row=0, column=0, columnspan=4, sticky='nsew')

        # 绑定画布事件
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)  # Linux scroll down

        # 参数控制区域
        self._create_parameter_controls(main_frame)

        # 按钮区域
        self._create_buttons(main_frame)

        # 裁剪按钮区域
        self._create_crop_buttons(main_frame)

        # 历史记录按钮
        self._create_history_buttons(main_frame)

        # 状态栏
        self.status_label = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=6, column=0, columnspan=4, sticky='ew', pady=5)

        # 布局配置
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

    def _create_parameter_controls(self, parent: ttk.Frame) -> None:
        """创建参数控制"""
        # 模糊程度滑块
        ttk.Label(parent, text="模糊程度:").grid(row=1, column=0, sticky='w', padx=5)
        block_size_slider = ttk.Scale(parent, from_=3, to=21, orient=tk.HORIZONTAL, variable=self.block_size)
        block_size_slider.grid(row=1, column=1, sticky='ew', padx=5)
        ttk.Spinbox(parent, from_=3, to=21, textvariable=self.block_size, width=5).grid(row=1, column=2, sticky='w', padx=5)

        # 亮度调整滑块
        ttk.Label(parent, text="亮度调整:").grid(row=2, column=0, sticky='w', padx=5)
        c_value_slider = ttk.Scale(parent, from_=0, to=10, orient=tk.HORIZONTAL, variable=self.c_value)
        c_value_slider.grid(row=2, column=1, sticky='ew', padx=5)
        ttk.Spinbox(parent, from_=0, to=10, textvariable=self.c_value, width=5).grid(row=2, column=2, sticky='w', padx=5)

        # 显示模式切换
        ttk.Checkbutton(parent, text="显示原图", variable=self.show_original,
                        command=self._toggle_display_mode).grid(row=1, column=3, padx=10)

        # 绑定滑块事件
        block_size_slider.bind("<Motion>", lambda e: self.debounce_timer.trigger())
        block_size_slider.bind("<ButtonRelease-1>", lambda e: self._on_parameter_change())
        c_value_slider.bind("<Motion>", lambda e: self.debounce_timer.trigger())
        c_value_slider.bind("<ButtonRelease-1>", lambda e: self._on_parameter_change())

        # 绑定变量变化
        self.block_size.trace_add("write", lambda *args: self.debounce_timer.trigger())
        self.c_value.trace_add("write", lambda *args: self.debounce_timer.trigger())

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """创建操作按钮"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=4, pady=10, sticky='ew')

        ttk.Button(button_frame, text="打开图像 (Ctrl+O)",
                  command=self._open_file).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="保存图像 (Ctrl+S)",
                  command=self._save_file).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="旋转90° (R)",
                  command=self._rotate_image).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="水平翻转 (H)",
                  command=self._flip_horizontal).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="垂直翻转 (V)",
                  command=self._flip_vertical).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def _create_crop_buttons(self, parent: ttk.Frame) -> None:
        """创建裁剪按钮"""
        crop_frame = ttk.Frame(parent)
        crop_frame.grid(row=4, column=0, columnspan=4, pady=5, sticky='ew')

        ttk.Button(crop_frame, text="开始裁剪 (C)",
                  command=self._start_crop).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(crop_frame, text="确认裁剪 (Enter)",
                  command=self._confirm_crop).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(crop_frame, text="取消裁剪 (Esc)",
                  command=self._cancel_crop).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def _create_history_buttons(self, parent: ttk.Frame) -> None:
        """创建历史记录按钮"""
        history_frame = ttk.Frame(parent)
        history_frame.grid(row=5, column=0, columnspan=4, pady=5, sticky='ew')

        self.undo_button = ttk.Button(history_frame, text="撤销 (Ctrl+Z)",
                                     command=self._undo, state=tk.DISABLED)
        self.undo_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.redo_button = ttk.Button(history_frame, text="重做 (Ctrl+Y)",
                                     command=self._redo, state=tk.DISABLED)
        self.redo_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        ttk.Button(history_frame, text="重置图像",
                  command=self._reset_image).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self._update_history_buttons()

    def _setup_shortcuts(self) -> None:
        """设置键盘快捷键"""
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-O>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-S>", lambda e: self._save_file())
        self.root.bind("<Control-z>", lambda e: self._undo())
        self.root.bind("<Control-Z>", lambda e: self._undo())
        self.root.bind("<Control-y>", lambda e: self._redo())
        self.root.bind("<Control-Y>", lambda e: self._redo())
        self.root.bind("<r>", lambda e: self._rotate_image())
        self.root.bind("<R>", lambda e: self._rotate_image())
        self.root.bind("<h>", lambda e: self._flip_horizontal())
        self.root.bind("<H>", lambda e: self._flip_horizontal())
        self.root.bind("<v>", lambda e: self._flip_vertical())
        self.root.bind("<V>", lambda e: self._flip_vertical())
        self.root.bind("<c>", lambda e: self._start_crop())
        self.root.bind("<C>", lambda e: self._start_crop())
        self.root.bind("<Return>", lambda e: self._confirm_crop())
        self.root.bind("<Escape>", lambda e: self._cancel_crop())

    def _setup_drag_drop(self) -> None:
        """设置拖放支持"""
        if not HAS_DND:
            return

        def on_drop(event):
            file_path = self.root.tk.splitlist(event.data)[0]
            if file_path:
                self._open_file(file_path=file_path)

        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind('<<Drop>>', on_drop)

    def _open_file(self, file_path: Optional[str] = None) -> None:
        """打开图像文件"""
        result = FileHandler.open_image(file_path)
        if result:
            image, filename = result
            self.image_container.clear()
            self.image_container.original_image = image
            self.image_container.save_state("打开图像")
            self._update_display()
            self._update_status(f"✅ 已加载: {filename} ({image.shape[1]}x{image.shape[0]})", "green")

    def _save_file(self) -> None:
        """保存图像"""
        if self.image_container.processed_image is None:
            self._update_status("⚠️ 没有可保存的图像", "orange")
            return

        file_path = FileHandler.save_image(self.image_container.processed_image)
        if file_path:
            self._update_status(f"✅ 已保存: {os.path.basename(file_path)}", "green")

    def _rotate_image(self) -> None:
        """旋转图像"""
        if ImageEditor.rotate(self.image_container):
            self._update_display()
            self._update_history_buttons()
            self._update_status("✅ 已旋转90°", "green")

    def _flip_horizontal(self) -> None:
        """水平翻转"""
        if ImageEditor.flip_horizontal(self.image_container):
            self._update_display()
            self._update_history_buttons()
            self._update_status("✅ 已水平翻转", "green")

    def _flip_vertical(self) -> None:
        """垂直翻转"""
        if ImageEditor.flip_vertical(self.image_container):
            self._update_display()
            self._update_history_buttons()
            self._update_status("✅ 已垂直翻转", "green")

    def _start_crop(self) -> None:
        """开始裁剪"""
        if self.crop_manager.start_crop(self.image_container):
            self._update_status("✂️ 裁剪模式: 拖拽选择区域 | 框选后可拖动8个控制点调整", "green")

    def _confirm_crop(self) -> None:
        """确认裁剪"""
        if self.crop_manager.confirm_crop(self.canvas, self.image_container):
            self._update_display()
            self._update_history_buttons()
            self._update_status("✅ 裁剪完成", "green")
        else:
            self._update_status("⚠️ 请先选择裁剪区域", "orange")

    def _cancel_crop(self) -> None:
        """取消裁剪"""
        self.crop_manager.cancel_crop(self.canvas)
        self._update_status("ℹ️ 已取消裁剪", "blue")

    def _undo(self) -> None:
        """撤销操作"""
        if self.image_container.undo():
            self._update_display()
            self._update_history_buttons()
            self._update_status("↩️ 已撤销", "blue")

    def _redo(self) -> None:
        """重做操作"""
        if self.image_container.redo():
            self._update_display()
            self._update_history_buttons()
            self._update_status("↪️ 已重做", "blue")

    def _reset_image(self) -> None:
        """重置图像"""
        if self.image_container.history:
            self.image_container.original_image = self.image_container.history[0].image.copy()
            self.image_container.save_state("重置")
            self._update_display()
            self._update_status("🔄 已重置", "blue")

    def _update_display(self) -> None:
        """更新图像显示"""
        if self.image_container.original_image is None:
            return

        if self.show_original.get():
            # 显示原图
            self._display_original()
        else:
            # 显示处理后的图像
            ImageDisplayer.update_async(
                self.canvas,
                self.image_container,
                self.block_size,
                self.c_value,
                callback=lambda: self._update_history_buttons(),
                executor=self.executor
            )

    def _display_original(self) -> None:
        """显示原始图像"""
        try:
            image = cv2.cvtColor(self.image_container.original_image, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(image)

            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            img_width, img_height = im.size
            scale = min(canvas_width / img_width, canvas_height / img_height)

            new_size = (int(img_width * scale), int(img_height * scale))
            im = im.resize(new_size, Image.Resampling.LANCZOS)

            img_tk = ImageTk.PhotoImage(im)
            self.canvas.img_tk = img_tk
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

        except Exception as e:
            logging.error(f"显示原图错误: {e}")

    def _on_parameter_change(self) -> None:
        """参数变化回调"""
        if self.image_container.original_image is None or self.show_original.get():
            return

        ImageDisplayer.update_async(
            self.canvas,
            self.image_container,
            self.block_size,
            self.c_value,
            executor=self.executor
        )

    def _toggle_display_mode(self) -> None:
        """切换显示模式"""
        self._update_display()
        mode = "原图" if self.show_original.get() else "效果图"
        self._update_status(f"👁️ 显示模式: {mode}", "blue")

    def _on_canvas_click(self, event: tk.Event) -> None:
        """画布点击事件"""
        self.crop_manager.on_click(event, self.canvas)

    def _on_canvas_drag(self, event: tk.Event) -> None:
        """画布拖拽事件"""
        self.crop_manager.on_drag(event, self.canvas)

    def _on_canvas_release(self, event: tk.Event) -> None:
        """画布鼠标释放事件"""
        self.crop_manager.on_release(event, self.canvas)

    def _on_canvas_motion(self, event: tk.Event) -> None:
        """画布鼠标移动事件"""
        self.crop_manager.on_mouse_move(event, self.canvas)

    def _on_mouse_wheel(self, event: tk.Event) -> None:
        """鼠标滚轮事件（缩放）"""
        # 简单的缩放实现
        if self.image_container.original_image is None:
            return

        # Windows: event.delta, Linux: event.num (4=up, 5=down)
        if event.delta:
            delta = event.delta
        else:
            delta = 1 if event.num == 4 else -1

        # 限制缩放范围
        current = self.zoom_level.get()
        new_zoom = max(0.1, min(3.0, current + delta * 0.1))
        self.zoom_level.set(new_zoom)

    def _update_status(self, message: str, color: str) -> None:
        """更新状态栏"""
        self.status_label.config(text=message, foreground=color)
        logging.info(message)

    def _update_history_buttons(self) -> None:
        """更新历史记录按钮状态"""
        self.undo_button.config(state=tk.NORMAL if self.image_container.can_undo else tk.DISABLED)
        self.redo_button.config(state=tk.NORMAL if self.image_container.can_redo else tk.DISABLED)

    def cleanup(self) -> None:
        """清理资源"""
        if self.debounce_timer:
            self.debounce_timer.cancel()

        if self.executor:
            self.executor.shutdown(wait=False)

        self.image_container.clear()
        ImageProcessor.clear_cache()
        logging.info("应用资源已清理")


def create_ui():
    """创建用户界面（兼容旧接口）"""
    root = tk.Tk() if not HAS_DND else TkinterDnD.Tk()
    app = ImageProcessorApp(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    create_ui()
