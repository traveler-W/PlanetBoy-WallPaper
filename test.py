import win32gui
import win32con
import win32api
import vlc
import time
def find_shelldll_defview():
    """查找SHELLDLL_DefView窗口"""

    # SHELLDLL_DefView
    # 如果直接查找失败，尝试通过WorkerW窗口查
    progman = win32gui.FindWindow("Progman", None)
    if progman:
        print(f"找到Progman窗口: {progman}")
        # 发送0x052C消息激活桌面窗口
        win32gui.SendMessage(progman, 0x052C, 0, 0)
        
        def enum_windows(hwnd, results):
            # 获取窗口类名
            class_name = win32gui.GetClassName(hwnd)
            if class_name == "WorkerW":
                print(f"找到WorkerW窗口: {hwnd}")
                defview = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
                if defview:
                    print(f"在WorkerW {hwnd} 中找到了DefView")
                results.append(hwnd)
            return True
                
        workers = []
        win32gui.EnumWindows(enum_windows, workers)
        print(f"总共找到 {len(workers)} 个WorkerW窗口")
        
        for worker in workers:
            defview = win32gui.FindWindowEx(worker, 0, "SHELLDLL_DefView", None)
            if defview:
                print(f"确认：在WorkerW {worker} 中找到了DefView")
                return worker
    
    print("未能找到包含SHELLDLL_DefView的WorkerW窗口")
    return None
def find_hdc():
    hdc = win32gui.GetDC(None)  # 获取整个屏幕的DC
    monitors = win32api.EnumDisplayMonitors(hdc, None)
    for monitor in monitors:
        print(monitor[2][0],monitor[2][1])
    pass

def _on_end_reached(event, player):
        """视频播放结束时的回调函数，用于循环播放"""
        print("走了回调")
        try:
            if player and player in self.players.values():
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
def loop_test2():
    player = vlc.Instance()

    media_list = player.media_list_new()

    media_player = player.media_list_player_new()

    media = player.media_new("C:\\Users\\xinhuo-u04\\Pictures\\vedio\\nn.mp4")

    media_list.add_media(media)
    media_player.set_media_list(media_list)
    media.add_option('--input-repeat=-1','--no-video-title-show','--fullscreen','--mouse-hide-timeout=0')  # 设置无限循环
    event_manager = media_player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, 
                                            lambda x, p=media_player: _on_end_reached(x, p))
    

    player.vlm_set_loop("death_note", True)

    media_player.play()

    time.sleep(20)
if __name__ == "__main__":
    find_shelldll_defview()
    # find_hdc()
    # loop_test2()