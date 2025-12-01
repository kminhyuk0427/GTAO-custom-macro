import keyboard
import time
import threading

class melongCore:
    """메롱 핵심 실행 엔진"""
    
    def __init__(self):
        self.is_running = False
        self.current_melong = None
        self.stop_signal = threading.Event()
        self.pressed_keys = set()
        self.mode2_events = {}
        self.melong_enabled = True
        self.melongs = {}
        self.timings = {'press': 0.01, 'release': 0.01, 'sequence': 0.001}
    
    def configure(self, melongs, timings):
        """메롱 설정 적용"""
        self.melongs = melongs
        self.timings = timings
        
        for key, info in melongs.items():
            if info['mode'] == 2:
                self.mode2_events[key] = threading.Event()
                self.mode2_events[key].set()
    
    def toggle_melong(self):
        """메롱 ON/OFF 토글"""
        self.melong_enabled = not self.melong_enabled
        if not self.melong_enabled and self.is_running:
            self.stop_signal.set()
        return self.melong_enabled
    
    def execute_key(self, key, delay=None, hold=None):
        """단일 키 입력"""
        keyboard.press(key)
        time.sleep(hold if hold else self.timings['press'])
        keyboard.release(key)
        time.sleep(delay if delay else self.timings['release'])
    
    def run_once(self, trigger, keys, delays, holds):
        """모드 2: 1회 실행"""
        if trigger in self.mode2_events:
            self.mode2_events[trigger].clear()
        
        try:
            for i, key in enumerate(keys):
                if not self.melong_enabled:
                    break
                self.execute_key(
                    key,
                    delays[i] if delays else None,
                    holds[i] if holds else None
                )
        finally:
            if trigger in self.mode2_events:
                self.mode2_events[trigger].set()
    
    def run_repeat(self, trigger, keys, delays, holds):
        """모드 1: 연속 반복"""
        try:
            while not self.stop_signal.is_set() and self.melong_enabled and trigger in self.pressed_keys:
                for i, key in enumerate(keys):
                    if trigger not in self.pressed_keys:
                        return
                    self.execute_key(
                        key,
                        delays[i] if delays else None,
                        holds[i] if holds else None
                    )
                time.sleep(self.timings['sequence'])
        finally:
            self.is_running = False
            self.current_melong = None
    
    def start(self, trigger):
        """메롱 시작"""
        if not self.melong_enabled or trigger not in self.melongs:
            return False
        
        info = self.melongs[trigger]
        mode = info['mode']
        
        if mode == 0:
            return False
        
        keys = info['keys']
        delays = info.get('delays')
        holds = info.get('holds')
        
        if mode == 2:
            if trigger in self.mode2_events and not self.mode2_events[trigger].is_set():
                return False
            threading.Thread(target=self.run_once, args=(trigger, keys, delays, holds), daemon=True).start()
            return True
        
        if self.is_running:
            return False
        
        self.is_running = True
        self.current_melong = trigger
        self.stop_signal.clear()
        
        threading.Thread(target=self.run_repeat, args=(trigger, keys, delays, holds), daemon=True).start()
        return True
    
    def stop(self, trigger):
        """메롱 중단"""
        if self.current_melong == trigger:
            self.stop_signal.set()