import time
import threading
import os

class EventHandler:
    """키보드 이벤트 핸들러 (매크로 연쇄 허용 + 최적화)"""
    __slots__ = ('core', 'toggle_key', 'blocked', 'shift_map')
    
    def __init__(self, core, toggle_key='`'):
        self.core = core
        self.toggle_key = toggle_key
        self.blocked = set()
        
        # Shift 맵 (최적화)
        self.shift_map = {
            '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', 
            '&': '7', '*': '8', '(': '9', ')': '0', '~': '`'
        }
    
    def get_base_key(self, event):
        """Shift 조합 제거"""
        return self.shift_map.get(event.name, event.name)
    
    def handle_press(self, event):
        """키 눌림 처리 (매크로 연쇄 허용)"""
        key = self.get_base_key(event)
        
        # 토글 키
        if key == self.toggle_key:
            self.core.toggle_melong()
            return False
        
        # 매크로 비활성화 시
        if not self.core.melong_enabled:
            return True
        
        # 매크로 키 아니면 통과
        if key not in self.core.melongs:
            return True
        
        # 이미 차단 중이면 무시
        if key in self.blocked:
            return False
        
        # 🔑 핵심 수정: 사용자가 직접 누른 경우만 체크
        if key in self.core.user_trigger_keys:
            return False
        
        # mode 2 중복 방지
        info = self.core.melongs[key]
        if info['mode'] == 2:
            event_obj = self.core.mode2_events.get(key)
            if event_obj and not event_obj.is_set():
                return False
        
        # 중복 누름 방지
        if key in self.core.pressed_keys:
            return False
        
        # 🔑 사용자가 직접 누른 트리거로 표시
        self.core.user_trigger_keys.add(key)
        
        # 차단 및 실행
        self.blocked.add(key)
        self.core.pressed_keys.add(key)
        self.core.start(key)
        
        return False
    
    def handle_release(self, event):
        """키 떼기 처리"""
        key = self.get_base_key(event)
        
        # 토글 키
        if key == self.toggle_key:
            return False
        
        # 매크로 비활성화 시
        if not self.core.melong_enabled:
            return True
        
        # 매크로 키 아니면 통과
        if key not in self.core.melongs:
            return True
        
        # 🔑 사용자가 직접 누른 키만 처리
        if key not in self.core.user_trigger_keys:
            return False
        
        # 사용자 트리거 기록 제거
        self.core.user_trigger_keys.discard(key)
        self.core.pressed_keys.discard(key)
        
        mode = self.core.melongs[key]['mode']
        
        if mode == 1:
            # mode 1: 즉시 중단
            self.core.stop(key)
            self.blocked.discard(key)
        elif mode == 2:
            # mode 2: 지연 후 차단 해제
            def delayed_unblock():
                time.sleep(0.05)
                self.blocked.discard(key)
            threading.Thread(target=delayed_unblock, daemon=True).start()
        
        return False
    
    def shutdown(self):
        """종료"""
        self.core.stop_signal.set()
        try:
            import keyboard
            keyboard.unhook_all()
        except:
            pass
        os._exit(0)