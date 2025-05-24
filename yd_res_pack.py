
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ESP32资源打包工具 - SPIFFS资源生成器图形界面

本应用程序为ESP32嵌入式系统提供图形化界面，用于生成和打包
使用SPIFFS（SPI Flash文件系统）的图像资源。支持多种图像格式
和针对嵌入式显示应用优化的压缩方法。

主要功能:
    - 支持多种输入格式：JPEG、PNG
    - 支持多种输出格式：SJPG、SPNG、QOI、SQOI、RAW（LVGL兼容）
    - 可配置图像分片以优化内存使用
    - LVGL集成支持（v8.x和v9.x版本）
    - 实时处理反馈
    - 配置文件管理
    - 自动化资源打包与内存映射

支持的图像格式:
    输入格式:  .jpg, .png
    输出格式: .sjpg（分片JPEG）, .spng（分片PNG）, .qoi（QOI格式）,
             .sqoi（分片QOI）, .bin（LVGL原始格式）

依赖库:
    - PyQt5: GUI框架
    - Pillow (PIL): 图像处理
    - numpy: 数值运算
    - qoi-conv: QOI格式支持
    - packaging: 版本管理

使用方法:
    直接运行此脚本启动图形界面:
    $ python yd_res_pack.py

    或使用提供的批处理文件进行自动环境配置:
    $ run.bat


技术支持: T01284
版本: 1.0.0
日期: 2024-12-19
许可证: 内部使用

注意事项:
    此程序为内部测试使用，如遇到任何问题请联系T01284。

系统要求:
    - Python 3.8 或更高版本
    - PyQt5 5.15+
    - Pillow 8.0+
    - numpy 1.19+
    - qoi-conv 1.0+
    - packaging 20.0+

文件结构:
    yd_res_pack.py          # 主GUI应用程序
    spiffs_assets_gen.py    # 资源处理脚本
    yd_res_pack.bat         # 环境配置脚本
    temp_config.json        # 临时配置文件（自动生成）

配置说明:
    应用程序生成的JSON配置文件结构如下:
    {
        "assets_path": "图片目录路径",
        "image_file": "输出文件路径.bin",
        "main_path": "头文件目录路径",
        "support_format": ".jpg,.png",
        "support_spng": true,
        "support_sjpg": true,
        "lvgl_ver": "9.0.0",
        ...
    }

使用示例:
    基本用法:
    1. 选择包含PNG/JPG文件的图片目录
    2. 选择生成二进制文件的输出目录
    3. 根据需要配置格式设置
    4. 点击"生成资源文件"开始处理

    高级用法:
    - 为嵌入式显示配置LVGL特定设置
    - 为内存受限设备调整分片高度
    - 使用QOI格式获得更好的压缩比

技术特点:
    - 图像分片处理：支持大图像分块处理，减少内存占用
    - 多格式支持：兼容多种压缩格式，适应不同应用场景
    - LVGL集成：完全兼容LVGL图形库的格式要求
    - 内存映射：生成高效的内存映射表，提升访问速度
    - 配置管理：支持配置保存和加载，便于批量处理

应用场景:
    - ESP32嵌入式系统界面开发
    - 物联网设备显示资源管理
    - 嵌入式GUI应用程序开发
    - LVGL图形库项目资源打包

保留所有权利。仅限内部使用。
"""

__version__ = "1.0.0"
__author__ = "T01284"
__status__ = "内部测试版"
__date__ = "2025-5-23"

import sys
import os
import json
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QPushButton, QFileDialog, QGroupBox, QCheckBox,
                             QSpinBox, QComboBox, QTextEdit, QProgressBar,
                             QMessageBox, QFrame, QSplitter, QTabWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor


class GenerateThread(QThread):
    """生成线程类"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, config_path, script_path):
        super().__init__()
        self.config_path = config_path
        self.script_path = script_path

    def run(self):
        try:
            # 检查脚本是否存在
            if not os.path.exists(self.script_path):
                self.finished.emit(False, f"找不到脚本文件: {self.script_path}")
                return

            # 执行脚本
            cmd = [sys.executable, self.script_path, '--config', self.config_path]
            self.progress.emit(f"执行命令: {' '.join(cmd)}")

            # 设置环境变量强制使用UTF-8编码
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore',  # 忽略编码错误
                universal_newlines=True,
                env=env
            )

            # 实时输出
            while True:
                try:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.progress.emit(output.strip())
                except UnicodeDecodeError:
                    # 如果遇到编码错误，跳过这一行
                    continue

            # 获取返回码
            rc = process.poll()
            try:
                stderr = process.stderr.read()
            except UnicodeDecodeError:
                stderr = "输出包含无法解码的字符"

            if rc == 0:
                self.finished.emit(True, "生成完成!")
            else:
                error_msg = stderr if stderr else f"脚本执行失败，返回码: {rc}"
                self.finished.emit(False, error_msg)

        except Exception as e:
            self.finished.emit(False, f"执行出错: {str(e)}")


class SPIFFSAssetsGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_default_config()

    def init_ui(self):
        self.setWindowTitle("SPIFFS Assets Generator - 图片资源生成器  此程序为内部测试使用,如遇到任何问题请联系T01284")
        self.setGeometry(100, 100, 1000, 700)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
        """)

        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        central_widget_layout = QVBoxLayout()
        central_widget_layout.addWidget(splitter)
        central_widget.setLayout(central_widget_layout)

        # 左侧配置面板
        config_widget = QWidget()
        config_layout = QVBoxLayout()
        config_widget.setLayout(config_layout)

        # 右侧输出面板
        output_widget = QWidget()
        output_layout = QVBoxLayout()
        output_widget.setLayout(output_layout)

        splitter.addWidget(config_widget)
        splitter.addWidget(output_widget)
        splitter.setSizes([600, 400])

        # 配置选项卡
        tab_widget = QTabWidget()
        config_layout.addWidget(tab_widget)

        # 基本设置选项卡
        basic_tab = QWidget()
        tab_widget.addTab(basic_tab, "基本设置")
        self.setup_basic_tab(basic_tab)

        # 格式设置选项卡
        format_tab = QWidget()
        tab_widget.addTab(format_tab, "格式设置")
        self.setup_format_tab(format_tab)

        # 高级设置选项卡
        advanced_tab = QWidget()
        tab_widget.addTab(advanced_tab, "高级设置")
        self.setup_advanced_tab(advanced_tab)

        # 控制按钮
        control_layout = QHBoxLayout()
        self.generate_btn = QPushButton("生成资源文件")
        self.generate_btn.clicked.connect(self.generate_assets)
        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.clicked.connect(self.save_config)
        self.load_config_btn = QPushButton("加载配置")
        self.load_config_btn.clicked.connect(self.load_config)

        control_layout.addWidget(self.save_config_btn)
        control_layout.addWidget(self.load_config_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.generate_btn)

        config_layout.addLayout(control_layout)

        # 输出面板
        output_layout.addWidget(QLabel("输出日志:"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        output_layout.addWidget(self.output_text)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        output_layout.addWidget(self.progress_bar)



    def setup_basic_tab(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 路径设置组
        path_group = QGroupBox("路径设置")
        path_layout = QGridLayout()
        path_group.setLayout(path_layout)

        # 图片目录
        path_layout.addWidget(QLabel("图片目录:"), 0, 0)
        self.assets_path_edit = QLineEdit()
        path_layout.addWidget(self.assets_path_edit, 0, 1)
        assets_browse_btn = QPushButton("浏览")
        assets_browse_btn.clicked.connect(self.browse_assets_path)
        path_layout.addWidget(assets_browse_btn, 0, 2)

        # 输出目录
        path_layout.addWidget(QLabel("输出目录:"), 1, 0)
        self.output_path_edit = QLineEdit()
        path_layout.addWidget(self.output_path_edit, 1, 1)
        output_browse_btn = QPushButton("浏览")
        output_browse_btn.clicked.connect(self.browse_output_path)
        path_layout.addWidget(output_browse_btn, 1, 2)

        # 头文件目录
        path_layout.addWidget(QLabel("头文件目录:"), 2, 0)
        self.main_path_edit = QLineEdit()
        path_layout.addWidget(self.main_path_edit, 2, 1)
        main_browse_btn = QPushButton("浏览")
        main_browse_btn.clicked.connect(self.browse_main_path)
        path_layout.addWidget(main_browse_btn, 2, 2)

        # 脚本路径
        path_layout.addWidget(QLabel("脚本路径:"), 3, 0)
        self.script_path_edit = QLineEdit()
        self.script_path_edit.setText("./spiffs_assets_gen.py")
        path_layout.addWidget(self.script_path_edit, 3, 1)
        script_browse_btn = QPushButton("浏览")
        script_browse_btn.clicked.connect(self.browse_script_path)
        path_layout.addWidget(script_browse_btn, 3, 2)

        layout.addWidget(path_group)

        # 基本参数组
        basic_group = QGroupBox("基本参数")
        basic_layout = QGridLayout()
        basic_group.setLayout(basic_layout)

        # 文件名长度
        basic_layout.addWidget(QLabel("文件名长度:"), 0, 0)
        self.name_length_spin = QSpinBox()
        self.name_length_spin.setRange(8, 128)
        self.name_length_spin.setValue(32)
        basic_layout.addWidget(self.name_length_spin, 0, 1)

        # 分片高度
        basic_layout.addWidget(QLabel("分片高度:"), 1, 0)
        self.split_height_spin = QSpinBox()
        self.split_height_spin.setRange(1, 1024)
        self.split_height_spin.setValue(16)
        basic_layout.addWidget(self.split_height_spin, 1, 1)

        # 分区大小
        basic_layout.addWidget(QLabel("分区大小:"), 2, 0)
        self.assets_size_edit = QLineEdit()
        self.assets_size_edit.setText("0x100000")
        basic_layout.addWidget(self.assets_size_edit, 2, 1)

        layout.addWidget(basic_group)
        layout.addStretch()

    def setup_format_tab(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # 支持格式组
        format_group = QGroupBox("支持的输入格式")
        format_layout = QVBoxLayout()
        format_group.setLayout(format_layout)

        self.support_jpg_cb = QCheckBox("JPEG (.jpg)")
        self.support_jpg_cb.setChecked(True)
        self.support_png_cb = QCheckBox("PNG (.png)")
        self.support_png_cb.setChecked(True)

        format_layout.addWidget(self.support_jpg_cb)
        format_layout.addWidget(self.support_png_cb)

        layout.addWidget(format_group)

        # 输出格式组
        output_group = QGroupBox("输出格式")
        output_layout = QVBoxLayout()
        output_group.setLayout(output_layout)

        self.support_sjpg_cb = QCheckBox("SJPG (分块JPEG)")
        self.support_sjpg_cb.setChecked(True)
        self.support_spng_cb = QCheckBox("SPNG (分块PNG)")
        self.support_spng_cb.setChecked(True)
        self.support_qoi_cb = QCheckBox("QOI (快速无损)")
        self.support_sqoi_cb = QCheckBox("SQOI (分块QOI)")
        self.support_raw_cb = QCheckBox("RAW (LVGL原始格式)")

        output_layout.addWidget(self.support_sjpg_cb)
        output_layout.addWidget(self.support_spng_cb)
        output_layout.addWidget(self.support_qoi_cb)
        output_layout.addWidget(self.support_sqoi_cb)
        output_layout.addWidget(self.support_raw_cb)

        layout.addWidget(output_group)
        layout.addStretch()

    def setup_advanced_tab(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # LVGL设置组
        lvgl_group = QGroupBox("LVGL设置")
        lvgl_layout = QGridLayout()
        lvgl_group.setLayout(lvgl_layout)

        # LVGL版本
        lvgl_layout.addWidget(QLabel("LVGL版本:"), 0, 0)
        self.lvgl_ver_combo = QComboBox()
        self.lvgl_ver_combo.addItems(["8.3.0", "9.0.0", "9.1.0", "9.2.0"])
        self.lvgl_ver_combo.setCurrentText("9.0.0")
        lvgl_layout.addWidget(self.lvgl_ver_combo, 0, 1)

        # 色彩格式
        lvgl_layout.addWidget(QLabel("色彩格式:"), 1, 0)
        self.support_raw_cf_combo = QComboBox()
        self.support_raw_cf_combo.addItems([
            "TRUE_COLOR", "TRUE_COLOR_ALPHA", "INDEXED_1BIT",
            "INDEXED_2BIT", "INDEXED_4BIT", "INDEXED_8BIT"
        ])
        lvgl_layout.addWidget(self.support_raw_cf_combo, 1, 1)

        # 输出格式
        lvgl_layout.addWidget(QLabel("输出格式:"), 2, 0)
        self.support_raw_ff_combo = QComboBox()
        self.support_raw_ff_combo.addItems(["C_ARRAY", "BIN"])
        self.support_raw_ff_combo.setCurrentText("BIN")
        lvgl_layout.addWidget(self.support_raw_ff_combo, 2, 1)

        # 抖动处理
        self.support_raw_dither_cb = QCheckBox("启用抖动处理")
        lvgl_layout.addWidget(self.support_raw_dither_cb, 3, 0, 1, 2)

        # BGR模式
        self.support_raw_bgr_cb = QCheckBox("启用BGR模式")
        lvgl_layout.addWidget(self.support_raw_bgr_cb, 4, 0, 1, 2)

        layout.addWidget(lvgl_group)
        layout.addStretch()

    def browse_assets_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择图片目录")
        if path:
            self.assets_path_edit.setText(path)

    def browse_output_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_path_edit.setText(path)

    def browse_main_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择头文件目录")
        if path:
            self.main_path_edit.setText(path)

    def browse_script_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择脚本文件", "", "Python Files (*.py)")
        if path:
            self.script_path_edit.setText(path)

    def get_support_formats(self):
        formats = []
        if self.support_jpg_cb.isChecked():
            formats.append(".jpg")
        if self.support_png_cb.isChecked():
            formats.append(".png")
        return ",".join(formats)

    def generate_config(self):
        """生成配置字典"""
        output_path = self.output_path_edit.text()
        if not output_path:
            raise ValueError("请选择输出目录")

        config = {
            "assets_path": self.assets_path_edit.text(),
            "image_file": os.path.join(output_path, "assets.bin"),
            "main_path": self.main_path_edit.text(),
            "name_length": self.name_length_spin.value(),
            "split_height": self.split_height_spin.value(),
            "support_format": self.get_support_formats(),
            "support_spng": self.support_spng_cb.isChecked(),
            "support_sjpg": self.support_sjpg_cb.isChecked(),
            "support_qoi": self.support_qoi_cb.isChecked(),
            "support_sqoi": self.support_sqoi_cb.isChecked(),
            "support_raw": self.support_raw_cb.isChecked(),
            "assets_size": self.assets_size_edit.text(),
            "lvgl_ver": self.lvgl_ver_combo.currentText(),
            "support_raw_cf": self.support_raw_cf_combo.currentText(),
            "support_raw_ff": self.support_raw_ff_combo.currentText(),
            "support_raw_dither": self.support_raw_dither_cb.isChecked(),
            "support_raw_bgr": self.support_raw_bgr_cb.isChecked()
        }
        return config

    def save_config(self):
        """保存配置到文件"""
        try:
            config = self.generate_config()
            file_path, _ = QFileDialog.getSaveFileName(self, "保存配置文件", "", "JSON Files (*.json)")
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                self.output_text.append(f"配置已保存到: {file_path}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存配置失败: {str(e)}")

    def load_config(self):
        """从文件加载配置"""
        file_path, _ = QFileDialog.getOpenFileName(self, "加载配置文件", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.load_config_from_dict(config)
                self.output_text.append(f"配置已加载: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载配置失败: {str(e)}")

    def load_config_from_dict(self, config):
        """从字典加载配置"""
        self.assets_path_edit.setText(config.get("assets_path", ""))

        # 从image_file中提取目录
        image_file = config.get("image_file", "")
        if image_file:
            self.output_path_edit.setText(os.path.dirname(image_file))

        self.main_path_edit.setText(config.get("main_path", ""))
        self.name_length_spin.setValue(config.get("name_length", 32))
        self.split_height_spin.setValue(config.get("split_height", 16))
        self.assets_size_edit.setText(config.get("assets_size", "0x100000"))

        # 支持格式
        formats = config.get("support_format", "").split(",")
        self.support_jpg_cb.setChecked(".jpg" in formats)
        self.support_png_cb.setChecked(".png" in formats)

        # 输出格式
        self.support_spng_cb.setChecked(config.get("support_spng", False))
        self.support_sjpg_cb.setChecked(config.get("support_sjpg", False))
        self.support_qoi_cb.setChecked(config.get("support_qoi", False))
        self.support_sqoi_cb.setChecked(config.get("support_sqoi", False))
        self.support_raw_cb.setChecked(config.get("support_raw", False))

        # LVGL设置
        self.lvgl_ver_combo.setCurrentText(config.get("lvgl_ver", "9.0.0"))
        self.support_raw_cf_combo.setCurrentText(config.get("support_raw_cf", "TRUE_COLOR"))
        self.support_raw_ff_combo.setCurrentText(config.get("support_raw_ff", "BIN"))
        self.support_raw_dither_cb.setChecked(config.get("support_raw_dither", False))
        self.support_raw_bgr_cb.setChecked(config.get("support_raw_bgr", False))

    def load_default_config(self):
        """加载默认配置"""
        default_config = {
            "assets_path": "",
            "image_file": "",
            "main_path": "",
            "name_length": 32,
            "split_height": 16,
            "support_format": ".jpg,.png",
            "support_spng": True,
            "support_sjpg": True,
            "support_qoi": False,
            "support_sqoi": False,
            "support_raw": False,
            "assets_size": "0x100000",
            "lvgl_ver": "9.0.0",
            "support_raw_cf": "TRUE_COLOR",
            "support_raw_ff": "BIN",
            "support_raw_dither": False,
            "support_raw_bgr": False
        }
        self.load_config_from_dict(default_config)

    def generate_assets(self):
        """生成资源文件"""
        try:
            # 验证输入
            if not self.assets_path_edit.text():
                QMessageBox.warning(self, "错误", "请选择图片目录")
                return

            if not self.output_path_edit.text():
                QMessageBox.warning(self, "错误", "请选择输出目录")
                return

            if not os.path.exists(self.script_path_edit.text()):
                QMessageBox.warning(self, "错误", "找不到脚本文件")
                return

            # 生成配置
            config = self.generate_config()

            # 创建输出目录
            os.makedirs(self.output_path_edit.text(), exist_ok=True)
            if self.main_path_edit.text():
                os.makedirs(self.main_path_edit.text(), exist_ok=True)


            # 获取代码所在目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # 在代码目录创建临时配置文件
            config_path = os.path.join(script_dir, "temp_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            # 清空输出
            self.output_text.clear()
            self.output_text.append("开始生成资源文件...")

            # 禁用生成按钮
            self.generate_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 无限进度条

            # 启动生成线程
            self.generate_thread = GenerateThread(config_path, self.script_path_edit.text())
            self.generate_thread.progress.connect(self.on_progress)
            self.generate_thread.finished.connect(self.on_finished)
            self.generate_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成失败: {str(e)}")

    def on_progress(self, message):
        """更新进度"""
        self.output_text.append(message)
        self.output_text.ensureCursorVisible()

    def on_finished(self, success, message):
        """生成完成"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.output_text.append(f"✅ {message}")
            QMessageBox.information(self, "成功", message)
        else:
            self.output_text.append(f"❌ {message}")
            QMessageBox.critical(self, "错误", message)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SPIFFS Assets Generator")

    # 设置应用图标 (如果有的话)
    # app.setWindowIcon(QIcon("icon.png"))

    window = SPIFFSAssetsGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()