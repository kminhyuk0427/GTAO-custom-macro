import os
import sys
import subprocess
import threading

class EventHandler:
    """키보드 이벤트 핸들러"""
    __slots__ = ('core', 'toggle_key', 'blocked', 'force_quit_keys', 
                 'pressed_force_quit', '_shutdown_lock', '_block_timers')
    
    # Shift 키 매핑
    SHIFT_MAP = {
        # 숫자 키 Shift
        '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
        '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
        
        # 기호 키 Shift
        '~': '`', '_': '-', '+': '=', '{': '[', '}': ']',
        '|': '\\', ':': ';', '"': "'", '<': ',', '>': '.', '?': '/',
        
        # 대문자 -> 소문자
        'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd', 'E': 'e', 'F': 'f',
        'G': 'g', 'H': 'h', 'I': 'i', 'J': 'j', 'K': 'k', 'L': 'l',
        'M': 'm', 'N': 'n', 'O': 'o', 'P': 'p', 'Q': 'q', 'R': 'r',
        'S': 's', 'T': 't', 'U': 'u', 'V': 'v', 'W': 'w', 'X': 'x',
        'Y': 'y', 'Z': 'z',
    }
    
    # 넘버패드 키 매핑
    NUMPAD_MAP = {
        'keypad 0': 'num0', 'keypad 1': 'num1', 'keypad 2': 'num2',
        'keypad 3': 'num3', 'keypad 4': 'num4', 'keypad 5': 'num5',
        'keypad 6': 'num6', 'keypad 7': 'num7', 'keypad 8': 'num8',
        'keypad 9': 'num9', 'keypad /': 'num/', 'keypad *': 'num*',
        'keypad -': 'num-', 'keypad +': 'num+', 'keypad .': 'num.',
        'keypad enter': 'numenter',
    }
    
    def __init__(self, core, toggle_key='`', force_quit_keys=None):
        if not core:
            raise ValueError("Core instance is required")
        
        self.core = core
        self.toggle_key = toggle_key
        self.blocked = set()
        self.force_quit_keys = set(force_quit_keys or ['alt', 'shift', 'delete'])
        self.pressed_force_quit = set()
        self._shutdown_lock = False
        self._block_timers = {}
    
    def _normalize_key(self, key_name):
        """키 이름 정규화"""
        if not key_name:
            return key_name
        
        # 넘버패드 체크
        numpad = self.NUMPAD_MAP.get(key_name)
        if numpad:
            return numpad
        
        # Shift 변환 체크
        shift = self.SHIFT_MAP.get(key_name)
        if shift:
            return shift
        
        return key_name
    
    def _schedule_unblock(self, key, delay=0.05):
        """차단 해제 예약"""
        # 기존 타이머 취소
        old_timer = self._block_timers.get(key)
        if old_timer:
            old_timer.cancel()
        
        # 새 타이머 시작
        timer = threading.Timer(delay, self._unblock_key, args=(key,))
        self._block_timers[key] = timer
        timer.start()
    
    def _unblock_key(self, key):
        """키 차단 해제"""
        self.blocked.discard(key)
        self._block_timers.pop(key, None)
    
    def handle_press(self, event):
        """키 눌림 처리"""
        if self._shutdown_lock:
            return False
        
        if not event or not hasattr(event, 'name'):
            return True
        
        key = self._normalize_key(event.name)
        if not key:
            return True
        
        # 1. 강제 종료 체크
        if key in self.force_quit_keys:
            self.pressed_force_quit.add(key)
            if self.pressed_force_quit >= self.force_quit_keys:
                print("강제 종료 중...")
                self.shutdown()
                return False
            return False
        
        # 2. 토글 키
        if key == self.toggle_key:
            status = "활성화" if self.core.toggle_macro() else "비활성화"
            print(f"매크로 {status}")
            return False
        
        # 3. 매크로 비활성화 상태
        if not self.core.macro_enabled:
            return True
        
        # 4. 미등록 키
        if key not in self.core.macros:
            return True
        
        # 5. 실행 중인 매크로 차단
        if key in self.core.executing_keys:
            return True
        
        # 6. 이미 차단된 키
        if key in self.blocked:
            return False
        
        # 7. 사용자가 이미 누른 키
        if key in self.core.user_triggers:
            return False
        
        # 8. mode 2 중복 실행 방지
        info = self.core.macros.get(key)
        if info and info.get('mode') == 2:
            event_obj = self.core.mode2_events.get(key)
            if event_obj and not event_obj.is_set():
                return False
        
        # 9. 중복 눌림 방지
        if key in self.core.pressed_keys:
            return False
        
        # 10. 매크로 시작
        self.core.user_triggers.add(key)
        self.blocked.add(key)
        self.core.pressed_keys.add(key)
        
        if not self.core.start(key):
            # 시작 실패 시 상태 롤백
            self.core.user_triggers.discard(key)
            self.blocked.discard(key)
            self.core.pressed_keys.discard(key)
            return False
        
        return False
    
    def handle_release(self, event):
        """키 떼기 처리"""
        if self._shutdown_lock:
            return False
        
        if not event or not hasattr(event, 'name'):
            return True
        
        key = self._normalize_key(event.name)
        if not key:
            return True
        
        # 1. 강제 종료 키 해제
        if key in self.force_quit_keys:
            self.pressed_force_quit.discard(key)
            return False
        
        # 2. 토글 키
        if key == self.toggle_key:
            return False
        
        # 3. 매크로 비활성화 상태
        if not self.core.macro_enabled:
            return True
        
        # 4. 미등록 키
        if key not in self.core.macros:
            return True
        
        # 5. 실행 중인 매크로 차단
        if key in self.core.executing_keys:
            return True
        
        # 6. 사용자가 누른 키가 아님
        if key not in self.core.user_triggers:
            return False
        
        # 7. 상태 정리
        self.core.user_triggers.discard(key)
        self.core.pressed_keys.discard(key)
        
        info = self.core.macros.get(key)
        if not info:
            return False
        
        mode = info.get('mode', 0)
        
        if mode == 1:
            # mode 1: 즉시 중단 및 차단 해제
            self.core.stop(key)
            self.blocked.discard(key)
            
            # 기존 타이머 취소
            old_timer = self._block_timers.get(key)
            if old_timer:
                old_timer.cancel()
                self._block_timers.pop(key, None)
        
        elif mode == 2:
            # mode 2: 지연 후 차단 해제
            self._schedule_unblock(key, 0.05)
        
        return False
    
    def shutdown(self):
        """완전 종료"""
        if self._shutdown_lock:
            return
        
        self._shutdown_lock = True
        print("프로그램 종료 중...")
        
        try:
            # 1. 코어 정리
            if hasattr(self, 'core') and self.core:
                self.core.cleanup()
            
            # 2. 타이머 취소
            for timer in list(self._block_timers.values()):
                try:
                    timer.cancel()
                except:
                    pass
            self._block_timers.clear()
            
            # 3. keyboard hook 해제
            try:
                import keyboard
                keyboard.unhook_all()
                keyboard.unhook_all_hotkeys()
            except:
                pass
        
        except:
            pass
        
        finally:
            # 4. 프로세스 강제 종료
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