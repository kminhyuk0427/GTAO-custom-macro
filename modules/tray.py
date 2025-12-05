import sys
import os
import threading
import subprocess
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

class TrayIcon:
    """시스템 트레이 아이콘"""
    __slots__ = ('on_exit_callback', 'icon', '_image', '_quit_lock', '_backup_timer')
    
    def __init__(self, on_exit_callback):
        if not callable(on_exit_callback) and on_exit_callback is not None:
            raise ValueError("on_exit_callback must be callable or None")
        
        self.on_exit_callback = on_exit_callback
        self.icon = None
        self._image = None
        self._quit_lock = False
        self._backup_timer = None
    
    def _create_default_icon(self):
        """기본 아이콘 생성"""
        if self._image:
            return self._image
        
        try:
            img = Image.new('RGB', (64, 64), 'black')
            d = ImageDraw.Draw(img)
            d.ellipse([8, 8, 56, 56], fill='green', outline='white', width=3)
            d.text((20, 15), 'M', fill='white')
            self._image = img
            return img
        except Exception as e:
            print(f"기본 아이콘 생성 실패: {e}")
            # 최소 아이콘
            return Image.new('RGB', (64, 64), 'green')
    
    def load_icon_image(self):
        """아이콘 로드"""
        if self._image:
            return self._image
        
        # 실행 파일 경로 기준
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        
        # 아이콘 경로 후보
        icon_paths = [
            os.path.join(base, 'icon.ico'),
            os.path.join(os.path.dirname(base), 'icon.ico'),
        ]
        
        # 아이콘 로드 시도
        for icon_path in icon_paths:
            try:
                if os.path.exists(icon_path):
                    self._image = Image.open(icon_path).resize((64, 64), Image.Resampling.LANCZOS)
                    return self._image
            except Exception as e:
                continue
        
        # 기본 아이콘 사용
        return self._create_default_icon()
    
    def on_quit(self, icon, item):
        """종료 처리"""
        if self._quit_lock:
            return
        
        self._quit_lock = True
        
        try:
            # 1. 아이콘 중지
            if self.icon:
                try:
                    self.icon.stop()
                except:
                    pass
        except:
            pass
        
        # 2. 콜백 실행
        if self.on_exit_callback:
            try:
                self.on_exit_callback()
            except Exception as e:
                print(f"종료 콜백 오류: {e}")
        
        # 3. 백업 타이머 시작
        try:
            self._backup_timer = threading.Timer(0.5, self._force_exit)
            self._backup_timer.start()
        except:
            self._force_exit()
    
    def _force_exit(self):
        """백업 강제 종료"""
        try:
            subprocess.Popen(
                ['taskkill', '/F', '/PID', str(os.getpid())],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except:
            try:
                import ctypes
                ctypes.windll.kernel32.TerminateProcess(-1, 0)
            except:
                os._exit(0)
    
    def run(self):
        """트레이 아이콘 실행"""
        try:
            menu = Menu(
                MenuItem('KeyM', lambda: None, enabled=False), 
                MenuItem('종료', self.on_quit)
            )
            
            self.icon = Icon("KeyM", self.load_icon_image(), "KeyM", menu)
            
            threading.Thread(target=self.icon.run, daemon=True).start()
        
        except Exception as e:
            print(f"트레이 아이콘 시작 실패: {e}")
            print("트레이 아이콘 없이 계속합니다...")
    
    def cleanup(self):
        """정리"""
        if self._backup_timer:
            try:
                self._backup_timer.cancel()
            except:
                pass
        
        if self.icon:
            try:
                self.icon.stop()
            except:
                pass