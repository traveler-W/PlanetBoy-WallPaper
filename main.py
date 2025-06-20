import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget,
                           QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                           QFileDialog, QListWidget, QMessageBox, QListWidgetItem,
                           QFrame, QScrollArea, QSlider, QCheckBox)
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl, QSettings
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPalette, QPainter
import win32gui
import win32con
import win32api
from PIL import Image
from wallpaper_manager import WallpaperManager
from video_wallpaper import VideoWallpaper

# 创建图标目录
ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')
if not os.path.exists(ICONS_DIR):
    os.makedirs(ICONS_DIR)

# 默认图标路径
DEFAULT_VIDEO_ICON = os.path.join(ICONS_DIR, 'video.png')
DEFAULT_GIF_ICON = os.path.join(ICONS_DIR, 'gif.png')

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('PlanetBoy', 'Wallpaper')
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 248, 240, 0.3);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(191, 186, 180, 0.6);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)
        
        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # 自启动设置区域
        autostart_container = QWidget()
        autostart_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 248, 240, 0.7);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        autostart_layout = QHBoxLayout(autostart_container)
        
        autostart_label = QLabel("开机自启动")
        autostart_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.autostart_checkbox = QCheckBox()
        self.autostart_checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 40px;
                height: 20px;
                border-radius: 10px;
                background: rgba(191, 186, 180, 0.6);
            }
            QCheckBox::indicator:checked {
                background: rgba(255, 228, 196, 0.9);
            }
        """)
        self.autostart_checkbox.setChecked(self.settings.value('autostart', False, type=bool))
        self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
        
        autostart_layout.addWidget(autostart_label)
        autostart_layout.addWidget(self.autostart_checkbox)
        autostart_layout.addStretch()
        
        # 透明度设置区域
        opacity_container = QWidget()
        opacity_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 248, 240, 0.7);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        opacity_layout = QVBoxLayout(opacity_container)
        
        opacity_title = QLabel("界面透明度")
        opacity_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        opacity_layout.addWidget(opacity_title)
        
        # 添加透明度值显示
        self.opacity_value_label = QLabel("70%")
        self.opacity_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.opacity_value_label.setStyleSheet("font-size: 16px; color: #664433;")
        opacity_layout.addWidget(self.opacity_value_label)
        
        # 添加滑块
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(20)  # 最小透明度20%
        self.opacity_slider.setMaximum(100)  # 最大透明度100%
        self.opacity_slider.setValue(self.settings.value('opacity', 70, type=int))
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: rgba(191, 186, 180, 0.6);
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
                background: rgba(255, 228, 196, 0.9);
            }
            QSlider::sub-page:horizontal {
                background: rgba(255, 228, 196, 0.9);
                border-radius: 4px;
            }
        """)
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        opacity_layout.addWidget(self.opacity_slider)
        
        # 更新透明度值显示
        self.update_opacity_label(self.opacity_slider.value())
        
        # 背景图设置区域
        bg_container = QWidget()
        bg_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 248, 240, 0.7);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        bg_layout = QVBoxLayout(bg_container)
        
        bg_title = QLabel("标签页背景设置")
        bg_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        bg_layout.addWidget(bg_title)
        
        # 背景图预览和选择按钮
        self.bg_preview = QLabel("未设置背景图")
        self.bg_preview.setStyleSheet("""
            QLabel {
                background: rgba(255, 248, 240, 0.5);
                border: 2px dashed rgba(191, 186, 180, 0.6);
                border-radius: 10px;
                padding: 20px;
                min-height: 100px;
            }
        """)
        self.bg_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_layout.addWidget(self.bg_preview)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        select_bg_btn = QPushButton("选择背景图")
        select_bg_btn.clicked.connect(self.select_background)
        
        clear_bg_btn = QPushButton("不设置背景")
        clear_bg_btn.clicked.connect(self.clear_background)
        clear_bg_btn.setStyleSheet("""
            QPushButton {
                background: rgba(191, 186, 180, 0.6);
            }
            QPushButton:hover {
                background: rgba(191, 186, 180, 0.8);
            }
        """)
        
        btn_layout.addWidget(select_bg_btn)
        btn_layout.addWidget(clear_bg_btn)
        bg_layout.addLayout(btn_layout)
        
        # 添加所有设置区域到内容布局
        content_layout.addWidget(autostart_container)
        content_layout.addWidget(opacity_container)
        content_layout.addWidget(bg_container)
        content_layout.addStretch()
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        
        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll)
        
        # 加载已保存的背景图
        self.load_background()

    def toggle_autostart(self, state):
        """切换开机自启动状态"""
        self.settings.setValue('autostart', bool(state))
        # 这里需要实现实际的开机自启动设置
        startup_path = os.path.join(
            os.getenv('APPDATA'),
            'Microsoft\\Windows\\Start Menu\\Programs\\Startup',
            'PlanetBoyWallpaper.lnk'
        )
        if state:
            # 创建快捷方式
            try:
                import winshell
                from win32com.client import Dispatch
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(startup_path)
                shortcut.Targetpath = sys.executable
                shortcut.WorkingDirectory = os.path.dirname(sys.executable)
                shortcut.save()
            except Exception as e:
                QMessageBox.warning(self, "警告", f"设置开机自启动失败: {str(e)}")
        else:
            # 删除快捷方式
            try:
                if os.path.exists(startup_path):
                    os.remove(startup_path)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"取消开机自启动失败: {str(e)}")

    def select_background(self):
        """选择背景图"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择背景图",
            "",
            "图片文件 (*.jpg *.jpeg *.png)"
        )
        
        if file_path:
            self.settings.setValue('background_image', file_path)
            self.load_background()
            # 获取主窗口并更新背景
            main_window = self.window()
            if isinstance(main_window, WallpaperApp):
                main_window.update_tab_backgrounds()

    def load_background(self):
        """加载背景图预览"""
        bg_path = self.settings.value('background_image', '')
        if bg_path and os.path.exists(bg_path):
            pixmap = QPixmap(bg_path)
            scaled_pixmap = pixmap.scaled(
                300, 200,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.bg_preview.setPixmap(scaled_pixmap)
        else:
            self.bg_preview.setText("未设置背景图")

    def update_opacity(self, value):
        """更新透明度设置"""
        self.settings.setValue('opacity', value)
        self.update_opacity_label(value)
        # 通知主窗口更新透明度
        main_window = self.window()
        if isinstance(main_window, WallpaperApp):
            main_window.update_tab_backgrounds()

    def update_opacity_label(self, value):
        """更新透明度值显示"""
        self.opacity_value_label.setText(f"{value}%")

    def clear_background(self):
        """清除背景图设置"""
        self.settings.remove('background_image')
        self.bg_preview.setText("未设置背景图")
        # 通知主窗口更新背景
        main_window = self.window()
        if isinstance(main_window, WallpaperApp):
            main_window.update_tab_backgrounds()

class WallpaperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 设置无边框窗口
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # 设置窗口背景透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("PlanetBoy壁纸")
        self.setMinimumSize(800, 600)
        self.is_maximized = False
        self.drag_position = None
        
        # 初始化管理器
        self.wallpaper_manager = WallpaperManager()
        self.original_geometry = None
        self.video_wallpaper = VideoWallpaper()
        
        # 连接壁纸管理器和视频壁纸处理器
        self.wallpaper_manager.set_video_wallpaper_handler(self.video_wallpaper)
        
        # 创建主窗口部件和布局
        main_widget = QWidget()
        main_widget.setObjectName("centralWidget")
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建自定义标题栏
        title_bar = QWidget()
        title_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 248, 240, 0.9);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        title_layout.setSpacing(5)

        # 窗口标题
        title_icon = QLabel()
        title_icon.setPixmap(QPixmap(os.path.join(ICONS_DIR, '1.png')).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio))
        title_layout.addWidget(title_icon)
        
        title_label = QLabel("PlanetBoy壁纸")
        title_label.setStyleSheet("font-weight: bold; color: #333;")
        title_layout.addWidget(title_label)

        # 占位符，将按钮推到右侧
        title_layout.addStretch()

        # 最小化按钮
        self.min_btn = QPushButton("−")
        self.min_btn.setStyleSheet(""
            "QPushButton { background: none; border: none; width: 18px; height: 15px; font-size: 16px; color: #555; border-radius: 4px; }"
            "QPushButton:hover { background-color: rgba(191, 186, 180, 0.6); }"
        )
        self.min_btn.clicked.connect(self.showMinimized)

        # 最大化/还原按钮
        self.max_btn = QPushButton("□")
        self.max_btn.setStyleSheet(""
            "QPushButton { background: none; border: none; width: 18px; height: 15px; font-size: 16px; color: #555; border-radius: 4px; }"
            "QPushButton:hover { background-color: rgba(191, 186, 180, 0.6); }"
        )
        self.max_btn.clicked.connect(self.toggle_maximize)

        # 关闭按钮
        self.close_btn = QPushButton("✕")
        self.close_btn.setStyleSheet(""
            "QPushButton { background: none; border: none; width: 18px; height: 15px; font-size: 16px; color: #555; border-radius: 4px; }"
            "QPushButton:hover { background-color: #ff4d4d; color: white; }"
        )
        self.close_btn.clicked.connect(self.close)

        # 添加按钮到标题栏
        title_layout.addWidget(self.min_btn)
        title_layout.addWidget(self.max_btn)
        title_layout.addWidget(self.close_btn)

        # 添加标题栏到主布局
        main_layout.addWidget(title_bar)

        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addWidget(content_widget)
        
        # 创建标签页容器
        self.tab_container = QWidget()
        self.tab_container.setObjectName("tabContainer")
        self.tab_container.setStyleSheet("""
            #tabContainer {
                background: rgba(255, 248, 240, 0.7);
                border-radius: 15px;
                border: 1px solid rgba(255, 228, 196, 0.8);
            }
        """)
        
        # 创建标签页
        self.tabs = QTabWidget()
        # 设置标签栏的边距
        self.tabs.setContentsMargins(5, 3, 0, 0)
        self.tabs.tabBar().setContentsMargins(5, 3, 0, 0)
        # 设置标签居中
        self.tabs.tabBar().setExpanding(True)  # 让标签填充整个可用空间
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar {
                alignment: center;
            }
            QTabBar::tab {
                background: rgba(255, 248, 240, 0.7);
                color: #664433;
                padding: 10px 20px;
                margin: 2px;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                min-width: 100px;  /* 设置最小宽度使标签更均匀 */
                max-width: 200px;  /* 设置最大宽度防止标签过宽 */
            }
            QTabBar::tab:selected {
                background: rgba(255, 228, 196, 0.9);
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: rgba(255, 228, 196, 0.7);
            }
        """)
        
        # 创建各个标签页
        self.preview_tab = WallpaperPreviewTab(self.wallpaper_manager, self.video_wallpaper)
        self.manage_tab = WallpaperManageTab(self.wallpaper_manager, self.video_wallpaper)
        self.recommend_tab = self.create_recommend_tab()
        self.settings_tab = SettingsTab()
        self.about_tab = self.create_about_tab()
        
        # 连接壁纸管理和预览页面的信号
        self.manage_tab.wallpaper_changed.connect(self.preview_tab.set_current_file)
        self.manage_tab.wallpaper_changed.connect(self.preview_tab.update_preview)
        
        # 添加标签页
        self.tabs.addTab(self.preview_tab, "壁纸设置")
        self.tabs.addTab(self.manage_tab, "壁纸管理")
        self.tabs.addTab(self.recommend_tab, "壁纸推荐")
        self.tabs.addTab(self.settings_tab, "设置")
        self.tabs.addTab(self.about_tab, "关于")
        
        # 设置标签页容器布局
        tab_container_layout = QVBoxLayout(self.tab_container)
        tab_container_layout.setContentsMargins(0, 0, 0, 0)
        tab_container_layout.addWidget(self.tabs)
        
        # 将标签页容器添加到主布局
        content_layout.addWidget(self.tab_container)
        
        # 加载标签页背景
        self.update_tab_backgrounds()
        
        # 设置样式表
        self.setStyleSheet("""
            QMainWindow {
                background: transparent;
            }
            #centralWidget {
                background: rgba(255, 248, 240, 0.8);
                border-radius: 15px;
                margin: 0px;
            }
            QWidget {
                color: #664433;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QTabBar::tab {
                background: rgba(255, 248, 240, 0.7);
                color: #664433;
                padding: 10px 20px;
                margin: 2px;
                border: none;
                border-radius: 10px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: rgba(255, 228, 196, 0.9);
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: rgba(255, 228, 196, 0.7);
            }
            QPushButton {
                background: rgba(255, 228, 196, 0.8);
                color: #664433;
                border: none;
                padding: 12px 25px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 218, 176, 0.9);
            }
            QPushButton:pressed {
                background: rgba(255, 208, 166, 1);
            }
            QScrollBar:vertical {
                background: rgba(255, 248, 240, 0.3);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(191, 186, 180, 0.6);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)

    def toggle_maximize(self):
        if self.is_maximized:
            # 还原窗口
            self.setWindowState(Qt.WindowState.WindowNoState)
            self.setGeometry(self.original_geometry)
            self.max_btn.setText("□")
            self.is_maximized = False
        else:
            # 最大化窗口
            self.original_geometry = self.geometry()
            self.setWindowState(Qt.WindowState.WindowMaximized)
            self.max_btn.setText("◱")
            self.is_maximized = True

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < 35:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None and not self.is_maximized:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def update_tab_backgrounds(self):
        """更新所有标签页的背景"""
        settings = QSettings('PlanetBoy', 'Wallpaper')
        bg_path = settings.value('background_image', '')
        opacity = settings.value('opacity', 70, type=int)
        opacity_value = opacity / 100.0  # 转换为0-1之间的值
        
        # 更新主窗口样式
        self.centralWidget().setStyleSheet(f"""
            #centralWidget {{
                background: rgba(255, 248, 240, {opacity_value * 1});
                border-radius: 15px;
                margin: 0px;
            }}
        """)
        
        # 创建基本样式
        container_style = f"""
            #tabContainer {{
                background: rgba(255, 248, 240, {opacity_value * 0.7});
                border-radius: 15px;
                border: 1px solid rgba(255, 228, 196, {opacity_value * 0.8});
            }}
        """
        
        # 如果有背景图且文件存在，添加背景图样式
        if bg_path and os.path.exists(bg_path):
            container_style += f"""
                #tabContainer {{
                    background-image: url({bg_path});
                    background-position: center;
                    background-repeat: no-repeat;
                }}
            """
        
        # 更新标签栏样式
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar {{
                alignment: center;
            }}
            QTabBar::tab {{
                background: rgba(255, 248, 240, {opacity_value * 0.7});
                color: #664433;
                padding: 10px 20px;
                margin: 2px;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                min-width: 100px;
                max-width: 200px;
            }}
            QTabBar::tab:selected {{
                background: rgba(255, 228, 196, {opacity_value * 0.9});
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background: rgba(255, 228, 196, {opacity_value * 0.7});
            }}
        """)
        
        # 为每个标签页创建独立的样式
        tab_style = f"""
            QWidget {{
                background: transparent;
            }}
            QPushButton {{
                background: rgba(255, 228, 196, {opacity_value * 0.8});
            }}
            QLabel {{
                background: transparent;
            }}
            QListWidget {{
                background: rgba(255, 248, 240, {opacity_value * 0.7});
                border: 1px solid rgba(255, 228, 196, {opacity_value * 0.6});
                border-radius: 10px;
            }}
            QScrollArea {{
                background: transparent;
                border: 1px solid rgba(255, 228, 196, {opacity_value * 0.6});
                border-radius: 10px;
            }}
            QWidget#centralWidget {{
                background: transparent;
            }}
            QCheckBox::indicator {{
                background: rgba(191, 186, 180, {opacity_value * 0.6});
            }}
            QCheckBox::indicator:checked {{
                background: rgba(255, 228, 196, {opacity_value * 0.9});
            }}
            QSlider::groove:horizontal {{
                background: rgba(191, 186, 180, {opacity_value * 0.6});
            }}
            QSlider::handle:horizontal {{
                background: rgba(255, 228, 196, {opacity_value * 0.9});
            }}
            QSlider::sub-page:horizontal {{
                background: rgba(255, 228, 196, {opacity_value * 0.9});
            }}
        """
        
        # 应用样式
        self.tab_container.setStyleSheet(container_style)
        self.preview_tab.setStyleSheet(tab_style)
        self.manage_tab.setStyleSheet(tab_style)
        self.recommend_tab.setStyleSheet(tab_style)
        self.settings_tab.setStyleSheet(tab_style)
        self.about_tab.setStyleSheet(tab_style)

    def create_recommend_tab(self):
        """创建推荐标签页"""
        recommend_tab = QWidget()
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        recommend_layout = QVBoxLayout(scroll_content)
        recommend_layout.setContentsMargins(30, 30, 30, 30)
        scroll.setWidget(scroll_content)
         
        # 设置滚动区域样式
        scroll.setStyleSheet("""
            QScrollArea { 
                background: rgba(255, 248, 240, 0.3);
            }
            QScrollBar:vertical {
                background: rgba(255, 248, 240, 0.3);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(191, 186, 180, 0.6);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)
        scroll_content.setStyleSheet("QWidget { background: transparent; }")
        
        # 创建主布局
        recommend_tab.setLayout(QVBoxLayout())
        recommend_tab.layout().addWidget(scroll)
        recommend_tab.layout().setContentsMargins(0, 0, 0, 0)
        
        # 推荐网站数据
        websites = [
            {"url": "https://haowallpaper.com", "desc": "很高质量壁纸分享平台，上面的壁纸都很精美，最主要的是都免费，就很香。", "rating": 5},
            {"url": "https://wallhere.com/zh/", "desc": "免费高清图片资源,上面的图片一般般，但是也有亮眼的壁纸。", "rating": 4},
            {"url": "https://wallhaven.cc/", "desc": "是很牛逼的壁纸网站，上面的壁纸也有很说服力。", "rating": 3},
            {"url": "https://pixabay.com", "desc": "免版权图片和视频。", "rating": 2},
            {"url": "https://simpledesktops.com/", "desc": "略微抽象的壁纸，不是很推荐。", "rating": 2},
            {"url": "https://konachan.net/post", "desc": "很不错的动漫壁纸网站。", "rating": 3},
            {"url": "https://www.wallpaperhub.app/", "desc": "还是很牛逼的网站的，有电点东西。", "rating": 4}
        ]
        
        # 创建推荐按钮
        for site in websites:
            btn = QPushButton()
            btn.setFixedHeight(80)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 248, 240, 0.7);
                    border-radius: 10px;
                    padding: 10px;
                    text-align: left;
                    border: 1px solid rgba(0,0,0,0.1);
                }
                QPushButton:hover {
                    background: rgba(191, 186, 180, 0.6);
                    border: 1px solid rgba(0,0,0,0.2);
                }
                QPushButton:pressed {
                    background: rgba(255, 248, 240, 1.0);
                    border: 1px solid rgba(100,0,0,0.3);
                    padding-left: 12px;
                    padding-top: 12px;
                }
            """)
            
            # 按钮内容布局
            btn_layout = QVBoxLayout()
            url_label = QLabel(f"网址: {site['url']}")
            desc_label = QLabel(f"描述: {site['desc']}")
            
            # 添加星级评价
            rating_layout = QHBoxLayout()
            rating_label = QLabel("推荐指数:")
            rating_stars = QLabel("★" * site['rating'] + "☆" * (5 - site['rating']))
            rating_stars.setStyleSheet("color: red; font-size: 16px;")
            
            rating_layout.addWidget(rating_label)
            rating_layout.addWidget(rating_stars)
            
            btn_layout.addWidget(url_label)
            btn_layout.addWidget(desc_label)
            btn_layout.addLayout(rating_layout)
            btn.setLayout(btn_layout)
            
            # 设置点击事件
            btn.clicked.connect(lambda _, url=site['url']: QDesktopServices.openUrl(QUrl(url)))
            recommend_layout.addWidget(btn)
        
        return recommend_tab

    def create_about_tab(self):
        """创建关于标签页"""
        about_tab = QWidget()
        main_layout = QVBoxLayout(about_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 248, 240, 0.3);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(191, 186, 180, 0.6);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)

        # 创建内容容器
        content_widget = QWidget()
        about_layout = QVBoxLayout(content_widget)
        about_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.setContentsMargins(50, 50, 50, 50)  # 增加外边距
        about_layout.setSpacing(30)  # 增加间距

        # 创建一个容器来包含所有内容
        content_container = QWidget()
        content_container.setFixedWidth(400)  # 固定宽度
        content_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 248, 240, 0.85);
                border-radius: 20px;
                border: 1px solid rgba(255, 228, 196, 0.9);
            }
        """)
        container_layout = QVBoxLayout(content_container)
        container_layout.setContentsMargins(30, 40, 30, 40)  # 增加内边距
        container_layout.setSpacing(25)  # 增加组件间距

        # 添加logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(os.path.join(ICONS_DIR, '1.png'))
        scaled_pixmap = logo_pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, 
                                         Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(logo_label)

        # 添加标题
        title_label = QLabel("PlanetBoy壁纸")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #664433;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title_label)

        # 添加版本信息
        version_label = QLabel("Version 1.0")
        version_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #996655;
            }
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(version_label)

        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("""
            QFrame {
                border: none;
                background-color: rgba(255, 228, 196, 0.8);
                min-height: 1px;
                max-height: 1px;
            }
        """)
        container_layout.addWidget(line)

        # 添加作者信息
        author_title = QLabel("开发者")
        author_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #664433;
            }
        """)
        author_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(author_title)

        author_name = QLabel("planetboy")
        author_name.setStyleSheet("""
            QLabel {
                color: #996655;
                font-size: 16px;
            }
        """)
        author_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(author_name)

        # 添加GitHub链接按钮
        github_btn = QPushButton("访问 GitHub")
        github_btn.setFixedWidth(200)  # 固定按钮宽度
        github_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 228, 196, 0.8);
                border: none;
                border-radius: 15px;
                padding: 12px;
                font-size: 15px;
                color: #664433;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 218, 176, 0.9);
            }
            QPushButton:pressed {
                background: rgba(255, 208, 166, 1);
                padding-left: 14px;
                padding-top: 14px;
            }
        """)
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/traveler-W/PlanetBoy-WallPaper")
            )
        )
        container_layout.addWidget(github_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 添加版权信息
        copyright_label = QLabel("© 2024 PlanetBoy. All rights reserved.")
        copyright_label.setStyleSheet("""
            QLabel {
                color: #996655;
                font-size: 12px;
            }
        """)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(copyright_label)

        # 将内容容器添加到布局
        about_layout.addWidget(content_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        
        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll)
        
        return about_tab

class WallpaperPreviewTab(QWidget):
    def __init__(self, wallpaper_manager, video_wallpaper):
        super().__init__()
        self.wallpaper_manager = wallpaper_manager
        self.video_wallpaper = video_wallpaper
        self.current_file = None
        self.preview_cache = {}  # 添加预览缓存
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 预览区域
        self.preview_area = QLabel("预览画面")
        self.preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_area.setMinimumSize(400, 400)  # 设置最小尺寸
        self.preview_area.setStyleSheet("""
            QLabel {
                background: rgba(255, 248, 240, 0.7);
                border: 2px solid rgba(255, 228, 196, 0.8);
                border-radius: 15px;
                font-size: 16px;
                padding: 20px;
            }
        """)
        layout.addWidget(self.preview_area)
        
        # 选择壁纸按钮
        select_btn = QPushButton("选择壁纸")
        select_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                min-width: 150px;
                margin-top: 20px;
            }
        """)
        select_btn.clicked.connect(self.select_wallpaper)
        layout.addWidget(select_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def get_cached_preview(self, file_path, target_size):
        """获取缓存的预览图"""
        cache_key = f"{file_path}_{target_size[0]}_{target_size[1]}"
        
        if cache_key in self.preview_cache:
            return self.preview_cache[cache_key]
            
        try:
            if self.wallpaper_manager.is_video_file(file_path):
                return None
                
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                return None
                
            # 保持宽高比缩放
            scaled_pixmap = pixmap.scaled(
                target_size[0], 
                target_size[1],
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 缓存预览图
            self.preview_cache[cache_key] = scaled_pixmap
            return scaled_pixmap
        except Exception as e:
            print(f"Error generating preview: {e}")
            return None

    def clear_cache(self):
        """清除预览缓存"""
        self.preview_cache.clear()

    def select_wallpaper(self):
        """选择壁纸"""
        file_dialog = QFileDialog()
        file_dialog.setStyleSheet("""
            QFileDialog {
                background: rgba(255, 248, 240, 0.95);
            }
            QFileDialog QPushButton {
                min-width: 100px;
            }
        """)
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "选择壁纸",
            "",
            "图片/视频文件 (*.jpg *.jpeg *.png *.gif *.mp4)"
        )
        
        if file_path:
            self.current_file = file_path
            if file_path.lower().endswith('.mp4'):
                self.video_wallpaper.set_wallpaper(file_path)
            else:
                self.wallpaper_manager.set_wallpaper(file_path)
            self.update_preview()

    def update_preview(self):
        """更新预览"""
        if not self.current_file:
            self.preview_area.setText("未选择壁纸")
            return
            
        try:
            preview_size = self.preview_area.size()
            # 计算实际预览尺寸（减去padding）
            target_size = (preview_size.width() - 40, preview_size.height() - 40)
            
            # 获取缓存的预览图
            pixmap = self.get_cached_preview(self.current_file, target_size)
            
            if pixmap:
                self.preview_area.setPixmap(pixmap)
            else:
                if self.wallpaper_manager.is_video_file(self.current_file):
                    self.preview_area.setText(f"当前视频壁纸:\n{os.path.basename(self.current_file)}")
                else:
                    self.preview_area.setText("无法加载预览")
        except Exception as e:
            print(f"Error updating preview: {e}")
            self.preview_area.setText("无法加载预览")

    def resizeEvent(self, event):
        """处理窗口大小改变事件"""
        super().resizeEvent(event)
        # 当窗口大小改变时，清除缓存并更新预览
        self.clear_cache()
        self.update_preview()  # 更新预览以适应新的尺寸

    def set_current_file(self, file_path):
        """设置当前文件并更新预览"""
        self.current_file = file_path
        self.update_preview()

class WallpaperManageTab(QWidget):
    wallpaper_changed = pyqtSignal(str)  # 添加信号

    def __init__(self, wallpaper_manager, video_wallpaper):
        super().__init__()
        self.wallpaper_manager = wallpaper_manager
        self.video_wallpaper = video_wallpaper
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建默认图标
        self.create_default_icons()
        
        # 壁纸列表
        self.wallpaper_list = QListWidget()
        self.wallpaper_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.wallpaper_list.setIconSize(QSize(200, 120))
        self.wallpaper_list.setSpacing(20)
        self.wallpaper_list.setMovement(QListWidget.Movement.Static)
        self.wallpaper_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.wallpaper_list.setStyleSheet("""
            QListWidget {
                background: rgba(255, 248, 240, 0.7);
                padding: 20px;
                border-radius: 15px;
            }
            QListWidget::item {
                background: rgba(255, 248, 240, 0.8);
                color: #664433;
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
                min-width: 220px;
                min-height: 180px;
            }
            QListWidget::item:selected {
                background: rgba(255, 228, 196, 0.9);
                border: 2px solid rgba(255, 218, 176, 1);
            }
            QListWidget::item:hover {
                background: rgba(255, 238, 216, 0.9);
                border: 2px solid rgba(255, 228, 196, 1);
            }
        """)
        self.wallpaper_list.itemDoubleClicked.connect(self.apply_wallpaper)
        layout.addWidget(self.wallpaper_list)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        
        add_btn = QPushButton("添加壁纸")
        delete_btn = QPushButton("删除壁纸")
        
        add_btn.clicked.connect(self.add_wallpaper)
        delete_btn.clicked.connect(self.delete_wallpaper)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)
        
        # 更新列表
        self.update_wallpaper_list()

    def create_default_icons(self):
        """创建默认图标"""
        # 创建视频图标
        if not os.path.exists(DEFAULT_VIDEO_ICON):
            video_icon = QPixmap(200, 120)
            video_icon.fill(QColor(255, 228, 196))
            painter = QPainter(video_icon)
            painter.drawText(video_icon.rect(), Qt.AlignmentFlag.AlignCenter, "视频")
            painter.end()
            video_icon.save(DEFAULT_VIDEO_ICON)

        # 创建GIF图标
        if not os.path.exists(DEFAULT_GIF_ICON):
            gif_icon = QPixmap(200, 120)
            gif_icon.fill(QColor(255, 228, 196))
            painter = QPainter(gif_icon)
            painter.drawText(gif_icon.rect(), Qt.AlignmentFlag.AlignCenter, "GIF")
            painter.end()
            gif_icon.save(DEFAULT_GIF_ICON)

    def update_wallpaper_list(self):
        """更新壁纸列表"""
        self.wallpaper_list.clear()
        wallpapers = self.wallpaper_manager.get_wallpapers()
        
        for wallpaper in wallpapers:
            item = QListWidgetItem()
            wallpaper_path = wallpaper['path'] if isinstance(wallpaper, dict) else wallpaper
            name = os.path.basename(wallpaper_path)
            
            # 创建预览图
            if wallpaper_path.lower().endswith('.mp4'):
                # 对于视频文件，获取第一帧作为预览
                pixmap = self.video_wallpaper.get_cached_thumbnail(wallpaper_path, (250, 120))
                if pixmap:
                    item.setIcon(QIcon(pixmap))
                else:
                    # 如果无法获取视频缩略图，使用默认图标
                    item.setIcon(QIcon(DEFAULT_VIDEO_ICON))
                item.setText(f"{name}\n[视频]")
            elif wallpaper_path.lower().endswith('.gif'):
                # 对于GIF，使用特殊图标
                if os.path.exists(DEFAULT_GIF_ICON):
                    item.setIcon(QIcon(DEFAULT_GIF_ICON))
                item.setText(f"{name}\n[GIF]")
            else:
                # 对于图片，创建缩略图
                try:
                    pixmap = QPixmap(wallpaper_path)
                    scaled_pixmap = pixmap.scaled(250, 120, Qt.AspectRatioMode.KeepAspectRatio, 
                                                Qt.TransformationMode.SmoothTransformation)
                    item.setIcon(QIcon(scaled_pixmap))
                    item.setText(name)
                except Exception as e:
                    print(f"Error creating thumbnail for {wallpaper_path}: {e}")
                    item.setText(name)
            
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
            item.setData(Qt.ItemDataRole.UserRole, wallpaper_path)
            self.wallpaper_list.addItem(item)

    def add_wallpaper(self):
        """添加新壁纸"""
        file_dialog = QFileDialog()
        file_dialog.setStyleSheet("""
            QFileDialog {
                background: rgba(255, 248, 240, 0.95);
            }
            QFileDialog QPushButton {
                min-width: 100px;
            }
        """)
        files, _ = file_dialog.getOpenFileNames(
            self,
            "选择壁纸",
            "",
            "图片/视频文件 (*.jpg *.jpeg *.png *.gif *.mp4)"
        )
        
        if files:
            for file in files:
                self.wallpaper_manager.add_wallpaper(file)
            self.update_wallpaper_list()

    def delete_wallpaper(self):
        """删除选中的壁纸"""
        current_item = self.wallpaper_list.currentItem()
        if current_item:
            wallpaper_path = current_item.data(Qt.ItemDataRole.UserRole)
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除壁纸 {os.path.basename(wallpaper_path)} 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.wallpaper_manager.remove_wallpaper(wallpaper_path)
                self.update_wallpaper_list()

    def apply_wallpaper(self, item):
        """应用选中的壁纸"""
        wallpaper_path = item.data(Qt.ItemDataRole.UserRole)
        if wallpaper_path.lower().endswith('.mp4'):
            self.video_wallpaper.set_wallpaper(wallpaper_path)
        else:
            self.wallpaper_manager.set_wallpaper(wallpaper_path)
        # 发送信号
        self.wallpaper_changed.emit(wallpaper_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = WallpaperApp()
    window.show()
    sys.exit(app.exec())