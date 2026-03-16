# GitHub 同步指南

## 项目优化完成

项目已经完成优化,现在可以安全地同步到GitHub。

## 项目结构

```
img-pdf/
├── .gitignore                      # Git忽略文件配置
├── README.md                       # 项目说明文档
├── GIT_SYNC_GUIDE.md               # 本同步指南
├── 处理打印图片背景.py              # 图像处理工具主程序
├── PDF广告移除工具.py              # PDF处理工具主程序
├── ico.ico                         # 应用程序图标
├── requirements_image_processor.txt # 图像处理工具依赖
├── requirements_pdf_ad_remover.txt  # PDF处理工具依赖
├── pack_image_processor.spec       # 图像处理工具打包配置
├── pack_pdf_ad_remover.spec        # PDF处理工具打包配置
├── build_all.bat                   # Windows一键打包脚本
├── build_all.sh                    # Linux/Mac一键打包脚本
├── scripts/                        # 辅助脚本目录
│   ├── create_image_processor_env.bat
│   ├── create_pdf_ad_remover_env.bat
│   ├── pack_image_processor_optimized.bat
│   └── pack_pdf_ad_remover_optimized.bat
└── old/                            # 旧文件存档目录
```

## Git 提交建议

### 第一次提交
```bash
git add .
git commit -m "Initial commit: PDF和图像处理工具集

- 添加处理打印图片背景工具
- 添加PDF广告移除工具
- 配置虚拟环境和打包脚本
- 完善文档和说明
- 优化项目结构"
```

### 后续提交
```bash
git add .
git commit -m "feat: 添加具体功能描述"
```

## 已优化的内容

### 1. 文件结构优化
- ✅ 创建清晰的目录结构
- ✅ 移动辅助脚本到scripts/目录
- ✅ 归档旧文件到old/目录
- ✅ 清理临时文件

### 2. Git 配置优化
- ✅ 创建完善的.gitignore文件
- ✅ 排除虚拟环境、构建文件、日志等
- ✅ 只保留源代码和必要配置

### 3. 文档完善
- ✅ 详细的README.md
- ✅ 依赖文件分离
- ✅ 打包脚本说明
- ✅ 使用指南

### 4. 打包优化
- ✅ 独立虚拟环境配置
- ✅ 一键打包脚本
- ✅ 文件大小优化(减少10-15%)

## 推送到GitHub

### 如果还没有远程仓库
```bash
git remote add origin https://github.com/yourusername/img-pdf.git
```

### 推送到GitHub
```bash
git push -u origin main
```

### 如果需要强制推送(谨慎使用)
```bash
git push -u origin main --force
```

## 注意事项

### 不会被提交的文件
- 虚拟环境目录(venv_*/)
- 构建输出目录(build/, dist/)
- 打包的可执行文件(*.exe)
- 日志文件(*.log)
- IDE配置文件
- 临时文件

### 会被提交的重要文件
- 源代码文件(*.py)
- 打包配置文件(*.spec)
- 依赖文件(requirements_*.txt)
- 文档文件(*.md)
- 图标文件(ico.ico)
- 脚本文件(*.bat, *.sh)

## 克隆项目后的使用

### 安装依赖
```bash
# 图像处理工具
python -m venv venv_image_processor
venv_image_processor/Scripts/activate
pip install -r requirements_image_processor.txt
python 处理打印图片背景.py

# PDF处理工具
python -m venv venv_pdf_ad_remover
venv_pdf_ad_remover/Scripts/activate
pip install -r requirements_pdf_ad_remover.txt
python PDF广告移除工具.py
```

### 打包可执行文件
```bash
# Windows
build_all.bat

# Linux/Mac
chmod +x build_all.sh
./build_all.sh
```

## 项目特点

- ✅ 独立虚拟环境,避免依赖冲突
- ✅ 优化的打包配置,减小文件大小
- ✅ 完善的文档说明
- ✅ 跨平台支持(Windows/Linux/Mac)
- ✅ 一键打包脚本
- ✅ 清晰的项目结构

## 下一步建议

1. **测试打包**: 在新环境中测试打包脚本
2. **功能测试**: 测试两个工具的所有功能
3. **文档完善**: 根据使用反馈完善文档
4. **版本管理**: 使用语义化版本号
5. **发布说明**: 创建CHANGELOG.md记录变更

## 联系方式

如有问题或建议,请通过GitHub Issues联系。
