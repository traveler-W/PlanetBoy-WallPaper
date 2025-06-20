import os
import json
import shutil
import win32gui
import win32con
from typing import List, Dict, Union

class WallpaperManager:
    def __init__(self):
        # 创建壁纸存储目录
        self.wallpaper_dir = os.path.join(os.path.expanduser('~'), '.planetboy_wallpaper')
        if not os.path.exists(self.wallpaper_dir):
            os.makedirs(self.wallpaper_dir)
        
        # 配置文件路径
        self.config_file = os.path.join(self.wallpaper_dir, 'config.json')
        
        # 加载或创建配置
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            'wallpapers': [],
            'current_wallpaper': None,
            'settings': {
                'auto_change': False,
                'change_interval': 3600  # 默认1小时
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 确保所有必要的键都存在
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
            except Exception as e:
                print(f"Error loading config: {e}")
                return default_config
        return default_config
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def add_wallpaper(self, file_path: str) -> str:
        """添加壁纸到管理器"""
        try:
            # 确保文件存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # 获取文件名和扩展名
            filename = os.path.basename(file_path)
            
            # 创建目标路径
            target_path = os.path.join(self.wallpaper_dir, filename)
            
            # 如果文件已存在，添加数字后缀
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(target_path):
                target_path = os.path.join(self.wallpaper_dir, f"{base} ({counter}){ext}")
                counter += 1
            
            # 复制文件到壁纸目录
            shutil.copy2(file_path, target_path)
            
            # 更新配置
            if target_path not in [w['path'] for w in self.config['wallpapers']]:
                self.config['wallpapers'].append({
                    'path': target_path,
                    'name': os.path.basename(target_path),
                    'type': os.path.splitext(target_path)[1].lower()
                })
                self._save_config()
            
            return target_path
            
        except Exception as e:
            print(f"Error adding wallpaper: {e}")
            raise

    def remove_wallpaper(self, wallpaper_path: str) -> bool:
        """从管理器中删除壁纸"""
        try:
            # 查找壁纸
            wallpaper = None
            for w in self.config['wallpapers']:
                if w['path'] == wallpaper_path:
                    wallpaper = w
                    break
            
            if wallpaper:
                # 从配置中移除
                self.config['wallpapers'].remove(wallpaper)
                
                # 如果是当前壁纸，清除当前壁纸设置
                if self.config['current_wallpaper'] == wallpaper_path:
                    self.config['current_wallpaper'] = None
                
                # 删除文件
                if os.path.exists(wallpaper_path):
                    os.remove(wallpaper_path)
                
                # 保存配置
                self._save_config()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error removing wallpaper: {e}")
            return False

    def get_wallpapers(self) -> List[Dict[str, str]]:
        """获取所有壁纸列表"""
        # 清理不存在的壁纸
        self.config['wallpapers'] = [
            w for w in self.config['wallpapers']
            if os.path.exists(w['path'])
        ]
        self._save_config()
        return self.config['wallpapers']

    def get_current_wallpaper(self) -> Union[Dict[str, str], None]:
        """获取当前壁纸"""
        if self.config['current_wallpaper']:
            for wallpaper in self.config['wallpapers']:
                if wallpaper['path'] == self.config['current_wallpaper']:
                    return wallpaper
        return None

    def set_wallpaper(self, wallpaper_path: str) -> bool:
        """设置壁纸"""
        try:
            # 确保文件存在
            if not os.path.exists(wallpaper_path):
                return False
            
            # 如果有视频壁纸正在播放，需要先停止
            if hasattr(self, 'video_wallpaper'):
                self.video_wallpaper.stop()
            
            # 设置壁纸
            win32gui.SystemParametersInfo(
                win32con.SPI_SETDESKWALLPAPER,
                wallpaper_path,
                win32con.SPIF_UPDATEINIFILE | win32con.SPIF_SENDCHANGE
            )
            
            # 更新当前壁纸
            self.config['current_wallpaper'] = wallpaper_path
            self._save_config()
            
            return True
            
        except Exception as e:
            print(f"Error setting wallpaper: {e}")
            return False

    def set_video_wallpaper_handler(self, video_wallpaper):
        """设置视频壁纸处理器"""
        self.video_wallpaper = video_wallpaper 

    @staticmethod
    def is_video_file(file_path: str) -> bool:
        """判断是否为视频文件"""
        if not file_path:
            return False
        return file_path.lower().endswith('.mp4') 