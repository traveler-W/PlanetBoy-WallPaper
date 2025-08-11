import os
import win32gui
import win32con
import win32api
import ctypes
import vlc
import cv2
import time
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap

class VideoWallpaper:
    def __init__(self):
        # 初始化VLC实例
        self.instance = vlc.Instance()
        self.players = {}  # 每个显示器一个播放器
        self.current_video = None
        self.windows = {}  # 每个显示器一个窗口
        self.event_managers = {}  # 初始化事件管理器字典
        self.monitors = []  # 初始化显示器列表
        self.is_24h = True
        
        # 缩略图缓存
        self._thumbnail_cache = {}
        
        # 获取所有显示器信息
        self.update_display_info()

    def update_display_info(self):
        """更新显示器信息"""
        self.monitors.clear()

        def callback(hmonitor, _hdc, _rect, _):
            """显示器枚举回调函数"""
            try:
                info = win32api.GetMonitorInfo(hmonitor)
                is_primary = info['Flags'] & win32con.MONITORINFOF_PRIMARY != 0
                monitor_rect = info['Monitor']
                work_rect = info['Work']
                
                self.monitors.append({
                    'handle': hmonitor,
                    'rect': (
                        monitor_rect[0],  # left
                        monitor_rect[1],  # top
                        monitor_rect[2],  # right
                        monitor_rect[3]   # bottom
                    ),
                    'work_area': (
                        work_rect[0],  # left
                        work_rect[1],  # top
                        work_rect[2],  # right
                        work_rect[3]   # bottom
                    ),
                    'is_primary': is_primary
                })
                print(monitor_rect)
                print(work_rect)
            except Exception as e:
                print(f"Error getting monitor info in callback: {e}")
            return True

        try:
            # 使用EnumDisplayMonitors枚举所有显示器
            hdc = win32gui.GetDC(None)  # 获取整个屏幕的DC
            try:
                monitors = win32api.EnumDisplayMonitors(hdc, None)
                for index, monitor in enumerate(monitors):
                    self.monitors.append({
                        'handle': index,
                        'rect': (monitor[2][0], monitor[2][1], monitor[2][2], monitor[2][3]),
                        'work_area': (monitor[2][0], monitor[2][1], monitor[2][2], monitor[2][3]),
                        'is_primary': True
                    })
            finally:
                win32gui.ReleaseDC(None, hdc)

            if not self.monitors:
                raise Exception("No monitors found")
                
        except Exception as e:
            print(f"Error enumerating monitors: {e}")
            # 如果枚举失败，至少添加主显示器
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            self.monitors.append({
                'handle': win32gui.GetDesktopWindow(),
                'rect': (0, 0, screen_width, screen_height),
                'work_area': (0, 0, screen_width, screen_height),
                'is_primary': True
            })

    def _create_window(self, monitor):
        """为指定显示器创建视频播放窗口"""
        if monitor['handle'] not in self.windows:
            try:
                # 创建一个隐藏的Qt窗口
                # 根据显示器尺寸设置窗口
                monitor_left, monitor_top, monitor_right, monitor_bottom = monitor['rect']
                window_width = monitor_right - monitor_left
                window_height = monitor_bottom - monitor_top
                
                window = QWidget()
                window.setWindowFlags(
                    Qt.WindowType.FramelessWindowHint |  # 无边框
                    Qt.WindowType.Tool |                 # 工具窗口
                    Qt.WindowType.WindowStaysOnBottomHint  # 保持在底部
                )
                window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
                window.setVisible(True)
                window.setGeometry(monitor_left+1920, monitor_top, window_width, window_height)
                # print(monitor_left, monitor_top, window_width, window_height)
                
                # 获取窗口句柄
                hwnd_windows = int(window.winId())
                
                # 设置窗口样式
                style = win32gui.GetWindowLong(hwnd_windows, win32con.GWL_EXSTYLE)
                style |= win32con.WS_EX_LAYERED  # 分层窗口
                win32gui.SetWindowLong(hwnd_windows, win32con.GWL_EXSTYLE, style)
                win32gui.SetLayeredWindowAttributes(hwnd_windows, 0, 255, win32con.LWA_ALPHA)
                
                # 将窗口设置为桌面壁纸
                progman = win32gui.FindWindow("Progman", None)
                win32gui.SendMessageTimeout(
                    progman, 0x052C, 0, 0, win32con.SMTO_NORMAL,100
                )
                
                # 遍历顶级窗口，找到 WorkerW
                def enum_windows(hwnd, results):
                    class_name = win32gui.GetClassName(hwnd)
                    if class_name == "WorkerW":
                        defview = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
                        if defview:
                            results.append(hwnd)
                    return True
                
                workers = []
                win32gui.EnumWindows(enum_windows, workers)
                
                # 找到当前显示器对应的 WorkerW
                wallpaper_worker = None
                defview = None
                monitor_left, monitor_top, monitor_right, monitor_bottom = monitor['rect']
                if len(workers) == 0:
                    # 说明是新版的窗口结构(24h2)
                    defview = win32gui.FindWindowEx(progman, 0, "SHELLDLL_DefView", None)
                    
                    worker = win32gui.FindWindowEx(progman, None, "WorkerW", None)
                    if worker:
                        wallpaper_worker = worker
                else:
                    # 说明是老版的窗口结构(23h2)
                    win32gui.EnumWindows(enum_windows, workers)
                    self.is_24h = False
                    for worker in workers:
                        # 获取 WorkerW 窗口位置
                        defview = win32gui.FindWindowEx(worker, 0, "SHELLDLL_DefView", None)
                        if defview:
                            # print("找到了DefView")
                            # 获取图标窗口句柄
                            icon_window = win32gui.FindWindowEx(defview, 0, "SysListView32", None)
                            if icon_window:
                                # 将图标窗口移到前面
                                win32gui.SetWindowPos(
                                    icon_window, 
                                    win32con.HWND_TOP,
                                    0, 0, 0, 0,
                                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                                )
                            # 获取当前显示器的壁纸 WorkerW
                            wallpaper_worker = win32gui.FindWindowEx(None, worker, "WorkerW", None)
                            # print("找到了WorkerW")
                            break
                
                if wallpaper_worker and self.is_24h:
                    # 将视频窗口设置为 WorkerW 的子窗口
                    win32gui.SetParent(hwnd_windows, progman)
                    # 确保视频窗口在底部
                    win32gui.SetWindowPos(
                        hwnd_windows,
                        win32con.HWND_TOP,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE 
                    )
                    win32gui.SetWindowPos(
                        defview,
                        win32con.HWND_TOP,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE 
                    )
                    win32gui.SetWindowPos(
                        wallpaper_worker,
                        win32con.HWND_BOTTOM,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE 
                    )
                else:
                    # 将视频窗口设置为 WorkerW 的子窗口
                    win32gui.SetParent(hwnd_windows, wallpaper_worker)
                    # 确保视频窗口在底部
                    win32gui.SetWindowPos(
                        hwnd_windows,
                        win32con.HWND_BOTTOM,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE
                    )
                
                window.show()
                self.windows[monitor['handle']] = window
            except Exception as e:
                print(f"Error creating window for monitor: {e}")

    def set_wallpaper(self, video_path):
        """设置视频壁纸"""
        if not os.path.exists(video_path):
            return False

        try:
            # 停止当前播放的视频
            self.stop()
            
            # 更新显示器信息
            # self.update_display_info()
            
            # 为每个显示器创建播放器和窗口
            for monitor in self.monitors:
                try:
                    # 创建窗口
                    self._create_window(monitor)
                    
                    # 创建播放器
                    player = self.instance.media_player_new()
                    
                    # 设置播放窗口和视频缩放
                    window = self.windows.get(monitor['handle'])
                    if window:
                        player.set_hwnd(int(window.winId()))
                        # 设置视频缩放以适应窗口
                        player.video_set_scale(0.0)  # 0.0表示自动缩放以适应窗口
                        # 确保窗口在底部
                        # win32gui.SetWindowPos(
                        #     int(window.winId()),
                        #     win32con.HWND_BOTTOM,
                        #     0, 0, 0, 0,
                        #     win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE
                        # )
                    
                    # 加载视频
                    media = self.instance.media_new(video_path)
                    media.add_option('input-repeat=999999')  # 设置无限循环，这里是一个很大的数字，设置为-1无效
                    player.set_media(media)
                    
                    
                    
                    # 设置静音
                    player.audio_set_volume(0)
                    
                    # 设置事件管理器
                    event_manager = player.event_manager()
                    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, 
                                            lambda x, p=player: self._on_end_reached(x, p))
                    
                    # 保存播放器和事件管理器
                    self.players[monitor['handle']] = player
                    self.event_managers[monitor['handle']] = event_manager
                    
                    # 开始播放
                    player.play()
                except Exception as e:
                    print(f"Error setting up video for monitor: {e}")
                    continue
            
            self.current_video = video_path
            return True
        except Exception as e:
            print(f"Error setting video wallpaper: {e}")
            return False

    def stop(self):
        """停止播放视频壁纸"""
        try:
            # 停止所有播放器
            for player in self.players.values():
                if player:
                    try:
                        player.stop()
                    except:
                        pass
            
            # 清理事件管理器
            for event_manager in self.event_managers.values():
                if event_manager:
                    try:
                        event_manager.event_detach(vlc.EventType.MediaPlayerEndReached)
                    except:
                        pass
            
            # 隐藏所有窗口
            for window in self.windows.values():
                if window:
                    try:
                        window.hide()
                    except:
                        pass
            
            # 清理资源
            self.players.clear()
            self.event_managers.clear()
            self.windows.clear()
            self.current_video = None
        except Exception as e:
            print(f"Error stopping video wallpaper: {e}")

    def _on_end_reached(self, event, player):
        """视频播放结束时的回调函数，用于循环播放"""
        try:
            if player and player in self.players.values():
                # print("触发回调函数")
                # print(f"正在重置播放位置并重新播放")
                player.set_position(0)
                player.play()
                
                # 双重保险：再次设置循环选项
                if player.get_media():
                    player.get_media().add_option('input-repeat=-1')
                    print("成功设置循环选项")
                else:
                    print("警告：无法获取媒体对象")
        except Exception as e:
            print(f"Error handling video end: {e}")

    def is_playing(self):
        """检查是否正在播放视频"""
        try:
            return any(player and player.is_playing() for player in self.players.values())
        except:
            return False

    def get_current_video(self):
        """获取当前播放的视频路径"""
        return self.current_video

    def __del__(self):
        """清理资源"""
        try:
            self.stop()
            if hasattr(self, 'players'):
                for player in self.players.values():
                    if player:
                        try:
                            player.release()
                        except:
                            pass
            if hasattr(self, 'instance'):
                try:
                    self.instance.release()
                except:
                    pass
        except Exception as e:
            print(f"Error cleaning up VideoWallpaper: {e}")

    @staticmethod
    def get_video_thumbnail(video_path, size=None):
        """获取视频的第一帧作为缩略图"""
        try:
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            # 读取第一帧
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return None
            
            # 如果指定了大小，调整图片大小
            if size:
                # 计算缩放比例，保持宽高比
                h, w = frame.shape[:2]
                target_w, target_h = size
                scale = min(target_w/w, target_h/h)
                new_w, new_h = int(w*scale), int(h*scale)
                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # 转换颜色空间从BGR到RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 创建QPixmap
            height, width = frame.shape[:2]
            bytes_per_line = 3 * width
            image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            
            return pixmap
            
        except Exception as e:
            print(f"Error creating video thumbnail: {e}")
            return None
    
    def get_cached_thumbnail(self, video_path, size=None):
        """获取缓存的视频缩略图，如果没有则创建"""
        cache_key = f"{video_path}_{size[0]}x{size[1]}" if size else video_path
        if cache_key not in self._thumbnail_cache:
            thumbnail = self.get_video_thumbnail(video_path, size)
            if thumbnail:
                self._thumbnail_cache[cache_key] = thumbnail
        return self._thumbnail_cache.get(cache_key)