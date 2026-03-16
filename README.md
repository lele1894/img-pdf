# PDF和图像处理工具集

这是一个包含两个主要工具的Python项目,用于处理PDF文件和图像的背景移除。

## 项目简介

本项目提供两个独立的工具:
1. **处理打印图片背景** - 移除图像中的黑色背景
2. **PDF广告移除工具** - 交互式移除PDF中的广告和白边

## 工具说明

### 1. 处理打印图片背景

一个功能强大的图像处理工具,主要用于移除扫描文档或打印图片中的黑色背景。

**主要功能:**
- 自动移除黑色背景,保留前景内容
- 图像旋转、翻转功能
- 智能裁剪功能
- 撤销/重做操作
- 支持多种图像格式
- 拖放文件支持

**依赖项:**
- opencv-python==4.8.1.78
- numpy==1.24.3
- Pillow==10.0.0
- tkinterdnd2==0.4.3

### 2. PDF广告移除工具

交互式PDF处理工具,允许用户选择要保留的区域,自动去除保留区域外的内容。

**主要功能:**
- 鼠标拖拽标注保留区域
- 支持"应用到所有页"和"每页各自框选"两种模式
- 可调整的保留区域编辑功能
- 白边自动去除
- 对比预览功能
- 高分辨率输出(144 DPI)

**依赖项:**
- opencv-python==4.8.1.78
- numpy==1.24.3
- Pillow==10.0.0
- pymupdf==1.23.8

## 安装方法

### 方法一: 使用虚拟环境(推荐)

#### 处理打印图片背景
```bash
python -m venv venv_image_processor
venv_image_processor\Scripts\activate
pip install -r requirements_image_processor.txt
python 处理打印图片背景.py
```

#### PDF广告移除工具
```bash
python -m venv venv_pdf_ad_remover
venv_pdf_ad_remover\Scripts\activate
pip install -r requirements_pdf_ad_remover.txt
python PDF广告移除工具.py
```

### 方法二: 直接运行
```bash
pip install opencv-python numpy Pillow pymupdf tkinterdnd2 pyinstaller
python 处理打印图片背景.py
# 或
python PDF广告移除工具.py
```

## 打包为可执行文件

### 使用优化脚本打包

#### 处理打印图片背景
```bash
# Windows
create_image_processor_env.bat  # 创建虚拟环境
pack_image_processor_optimized.bat  # 打包

# Linux/Mac
python -m venv venv_image_processor
source venv_image_processor/bin/activate
pip install -r requirements_image_processor.txt
pyinstaller pack_image_processor.spec --clean
```

#### PDF广告移除工具
```bash
# Windows
create_pdf_ad_remover_env.bat  # 创建虚拟环境
pack_pdf_ad_remover_optimized.bat  # 打包

# Linux/Mac
python -m venv venv_pdf_ad_remover
source venv_pdf_ad_remover/bin/activate
pip install -r requirements_pdf_ad_remover.txt
pyinstaller pack_pdf_ad_remover.spec --clean
```

### 打包优化说明

使用独立虚拟环境打包可以显著减小文件大小:
- **处理打印图片背景.exe**: 约59MB (比优化前减少10.6%)
- **PDF广告移除工具.exe**: 约70MB (比优化前减少15.7%)

优化原理:
- 精确控制依赖包版本
- 避免打包不必要的包
- 使用较旧但够用的包版本

## 项目结构

```
img-pdf/
├── 处理打印图片背景.py          # 图像处理工具主程序
├── PDF广告移除工具.py            # PDF处理工具主程序
├── ico.ico                       # 应用程序图标
├── requirements_image_processor.txt   # 图像处理工具依赖
├── requirements_pdf_ad_remover.txt    # PDF处理工具依赖
├── pack_image_processor.spec     # 图像处理工具打包配置
├── pack_pdf_ad_remover.spec      # PDF处理工具打包配置
├── create_image_processor_env.bat    # 创建图像处理虚拟环境
├── create_pdf_ad_remover_env.bat     # 创建PDF处理虚拟环境
├── pack_image_processor_optimized.bat  # 图像处理打包脚本
├── pack_pdf_ad_remover_optimized.bat   # PDF处理打包脚本
└── README.md                     # 项目说明文档
```

## 使用说明

### 处理打印图片背景

1. 启动程序
2. 点击"打开图像"或拖放图像文件
3. 调整"模糊程度"和"亮度调整"参数
4. 使用旋转、翻转功能调整图像
5. 可选:使用裁剪功能裁剪图像
6. 点击"保存图像"保存结果

### PDF广告移除工具

1. 启动程序
2. 点击"浏览"选择PDF文件
3. 在预览区域拖拽鼠标标注要保留的区域
4. 选择框选模式:
   - **应用到所有页**: 一页标注应用到所有页面
   - **每页各自框选**: 每页单独标注不同区域
5. 调整处理选项(白边阈值、保留白边等)
6. 点击"应用并处理PDF"
7. 查看对比预览确认结果

## 技术特点

### 性能优化
- 异步图像处理,避免界面卡顿
- 防抖处理,优化参数调整体验
- 线程池管理,提高处理效率
- 图像处理缓存,避免重复计算

### 用户体验
- 直观的GUI界面
- 实时预览和参数调整
- 完整的撤销/重做功能
- 详细的操作说明和帮助文档
- 支持拖放文件

### 输出质量
- 高分辨率处理(144 DPI)
- PNG格式保持清晰度
- 智能白边检测和去除
- 可调节的处理参数

## 依赖项说明

### 图像处理工具
- **opencv-python**: 图像处理核心库
- **numpy**: 数值计算支持
- **Pillow**: 图像格式处理
- **tkinterdnd2**: 拖放功能支持

### PDF处理工具
- **opencv-python**: 图像处理核心库
- **numpy**: 数值计算支持
- **Pillow**: 图像格式处理
- **pymupdf**: PDF文件处理

## 注意事项

1. **文件备份**: 处理前建议备份原始文件
2. **大文件处理**: 大型PDF文件处理时间较长,请耐心等待
3. **内存要求**: 处理高分辨率图像需要足够内存
4. **依赖版本**: 建议使用指定版本的依赖包以确保兼容性

## 常见问题

**Q: 打包后的EXE文件太大?**
A: 使用提供的优化脚本在独立虚拟环境中打包,可以显著减小文件大小。

**Q: 处理速度慢?**
A: 减少标注区域数量,或使用"应用到所有页"模式可以提高效率。

**Q: 图像清晰度不够?**
A: 工具已使用高分辨率处理(144 DPI),如需更高清晰度可修改代码中的zoom参数。

**Q: 支持哪些文件格式?**
A: 支持常见图像格式(JPG, PNG, BMP, TIFF, WebP)和PDF文件。

## 许可证

本项目仅供学习和个人使用。

## 贡献

欢迎提出建议和改进意见。

## 更新日志

### v2.0 (当前版本)
- 重构为两个独立工具
- 添加虚拟环境支持
- 优化打包文件大小
- 改进用户界面
- 增强处理功能

### v1.0
- 初始版本
- 基础图像处理功能
- PDF广告移除功能
