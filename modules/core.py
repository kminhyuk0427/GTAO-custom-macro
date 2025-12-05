import time
import threading
import ctypes
from ctypes import c_ulong, c_ushort, c_long, Structure, Union, POINTER, windll

# DirectInput 구조체
PUL = POINTER(c_ulong)

class KeyBdInput(Structure):
    _fields_ = [("wVk", c_ushort), ("wScan", c_ushort), ("dwFlags", c_ulong), 
                ("time", c_ulong), ("dwExtraInfo", PUL)]

class HardwareInput(Structure):
    _fields_ = [("uMsg", c_ulong), ("wParamL", c_ushort), ("wParamH", c_ushort)]

class MouseInput(Structure):
    _fields_ = [("dx", c_long), ("dy", c_long), ("mouseData", c_ulong), 
                ("dwFlags", c_ulong), ("time", c_ulong), ("dwExtraInfo", PUL)]

class Input_I(Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

class Input(Structure):
    _fields_ = [("type", c_ulong), ("ii", Input_I)]

SendInput = windll.user32.SendInput

# 스캔코드 맵
SCANCODE_MAP = {
    # 숫자
    '0': 0x0B, '1': 0x02, '2': 0x03, '3': 0x04, '4': 0x05,
    '5': 0x06, '6': 0x07, '7': 0x08, '8': 0x09, '9': 0x0A,
    
    # 알파벳
    'q': 0x10, 'w': 0x11, 'e': 0x12, 'r': 0x13, 't': 0x14,
    'y': 0x15, 'u': 0x16, 'i': 0x17, 'o': 0x18, 'p': 0x19,
    'a': 0x1E, 's': 0x1F, 'd': 0x20, 'f': 0x21, 'g': 0x22,
    'h': 0x23, 'j': 0x24, 'k': 0x25, 'l': 0x26,
    'z': 0x2C, 'x': 0x2D, 'c': 0x2E, 'v': 0x2F, 'b': 0x30,
    'n': 0x31, 'm': 0x32,
    
    # 방향키
    'up': 0xC8, 'down': 0xD0, 'left': 0xCB, 'right': 0xCD,
    
    # 특수키
    'space': 0x39, 'enter': 0x1C, 'shift': 0x2A, 'ctrl': 0x1D,
    'alt': 0x38, 'tab': 0x0F, 'esc': 0x01, 'backspace': 0x0E,
    'delete': 0xD3, 'insert': 0xD2, 'home': 0xC7, 'end': 0xCF,
    'pageup': 0xC9, 'pagedown': 0xD1,
    
    # 기능키
    'f1': 0x3B, 'f2': 0x3C, 'f3': 0x3D, 'f4': 0x3E,
    'f5': 0x3F, 'f6': 0x40, 'f7': 0x41, 'f8': 0x42,
    'f9': 0x43, 'f10': 0x44, 'f11': 0x57, 'f12': 0x58,
    
    # 락 키
    'capslock': 0x3A, 'numlock': 0x45, 'scrolllock': 0x46,
    'printscreen': 0xB7, 'pause': 0xC5,
    
    # 기호
    '-': 0x0C, '=': 0x0D, '[': 0x1A, ']': 0x1B,
    ';': 0x27, "'": 0x28, '`': 0x29, '\\': 0x2B,
    ',': 0x33, '.': 0x34, '/': 0x35,
    
    # 넘버패드
    'num0': 0x52, 'num1': 0x4F, 'num2': 0x50, 'num3': 0x51,
    'num4': 0x4B, 'num5': 0x4C, 'num6': 0x4D, 'num7': 0x47,
    'num8': 0x48, 'num9': 0x49,
    'num/': 0xB5, 'num*': 0x37, 'num-': 0x4A, 'num+': 0x4E,
    'num.': 0x53, 'numenter': 0x9C,
    
    # 윈도우 키
    'win': 0xDB, 'rightwin': 0xDC, 'menu': 0xDD,
    
    # 확장 컨트롤 키
    'rightshift': 0x36, 'rightctrl': 0x9D, 'rightalt': 0xB8,
}

# Extended 키
EXTENDED_KEYS = frozenset({
    'up', 'down', 'left', 'right',
    'delete', 'insert', 'home', 'end', 'pageup', 'pagedown',
    'num/', 'numenter', 'rightctrl', 'rightalt', 'rightshift',
    'win', 'rightwin', 'menu', 'printscreen'
})

# 상수
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

# 안전 설정
MAX_ITERATIONS = 10000  # mode1 최대 반복 횟수
CHECK_INTERVAL = 0.001  # 종료 체크 간격
CLEANUP_DELAY = 0.15    # 실행 키 정리 딜레이
MODE2_BLOCK_DELAY = 0.05  # mode2 차단 해제 딜레이

class MacroCore:
    """매크로 코어 엔진"""
    __slots__ = ('macro_enabled', 'macros', 'timings', 'mode2_events',
                 'pressed_keys', 'executing_keys', 'user_triggers',
                 'is_running', 'current_macro', 'stop_signal',
                 '_extra', '_input_cache', '_cleanup_timers', '_lock')
    
    def __init__(self):
        self.macro_enabled = True
        self.macros = {}
        self.timings = {'press': 0.02, 'release': 0.02, 'sequence': 0.02}
        self.mode2_events = {}
        
        self.pressed_keys = set()
        self.executing_keys = set()
        self.user_triggers = set()
        
        self.is_running = False
        self.current_macro = None
        self.stop_signal = threading.Event()
        
        # DirectInput 캐싱
        self._extra = c_ulong(0)
        self._input_cache = {}
        self._cleanup_timers = {}
        self._lock = threading.Lock()
    
    def configure(self, macros, timings):
        """설정 적용"""
        if not isinstance(macros, dict) or not isinstance(timings, dict):
            raise ValueError("Invalid configuration format")
        
        self.macros = macros
        self.timings = timings
        
        # mode 2 이벤트 초기화
        for key, info in macros.items():
            if info.get('mode') == 2:
                self.mode2_events[key] = threading.Event()
                self.mode2_events[key].set()
    
    def toggle_macro(self):
        """매크로 토글"""
        self.macro_enabled = not self.macro_enabled
        if not self.macro_enabled:
            self._force_stop_all()
        return self.macro_enabled
    
    def _force_stop_all(self):
        """모든 매크로 강제 중지"""
        with self._lock:
            self.stop_signal.set()
            self.is_running = False
            self.current_macro = None
            self.pressed_keys.clear()
    
    def _send_input(self, scan_code, is_extended, is_keyup):
        """DirectInput 전송"""
        flags = KEYEVENTF_SCANCODE
        if is_extended:
            flags |= KEYEVENTF_EXTENDEDKEY
        if is_keyup:
            flags |= KEYEVENTF_KEYUP
        
        cache_key = (scan_code, flags)
        if cache_key not in self._input_cache:
            ii = Input_I()
            ii.ki = KeyBdInput(0, scan_code, flags, 0, POINTER(c_ulong)(self._extra))
            self._input_cache[cache_key] = Input(c_ulong(1), ii)
        
        SendInput(1, ctypes.pointer(self._input_cache[cache_key]), ctypes.sizeof(Input))
    
    def _should_stop_mode1(self, trigger_key):
        """mode1 중단 조건 체크"""
        return (trigger_key not in self.pressed_keys or 
                not self.macro_enabled or 
                self.stop_signal.is_set())
    
    def _interruptible_sleep(self, duration, trigger_key):
        """중단 가능한 sleep"""
        if duration <= 0:
            return True
        
        end_time = time.perf_counter() + duration
        
        while time.perf_counter() < end_time:
            if self._should_stop_mode1(trigger_key):
                return False
            time.sleep(CHECK_INTERVAL)
        
        return not self._should_stop_mode1(trigger_key)
    
    def _execute_key(self, key, trigger_key, hold, delay, mode):
        """단일 키 실행"""
        # 트리거 키는 딜레이만 처리
        if key == trigger_key:
            if delay > 0:
                if mode == 1:
                    return self._interruptible_sleep(delay, trigger_key)
                else:
                    time.sleep(delay)
            return True
        
        # 스캔코드 조회
        scan_code = SCANCODE_MAP.get(key)
        if scan_code is None:
            return True
        
        is_extended = key in EXTENDED_KEYS
        is_macro_trigger = key in self.macros
        
        # 매크로 트리거면 실행 목록 추가
        if is_macro_trigger:
            self.executing_keys.add(key)
        
        try:
            # mode 1 중단 체크
            if mode == 1 and self._should_stop_mode1(trigger_key):
                return False
            
            # 키 눌림
            self._send_input(scan_code, is_extended, False)
            
            # hold 대기
            if hold > 0:
                if mode == 1:
                    if not self._interruptible_sleep(hold, trigger_key):
                        self._send_input(scan_code, is_extended, True)
                        return False
                else:
                    time.sleep(hold)
            
            # 키 뗌
            self._send_input(scan_code, is_extended, True)
            
            # delay 대기
            if delay > 0:
                if mode == 1:
                    return self._interruptible_sleep(delay, trigger_key)
                else:
                    time.sleep(delay)
            
            return True
        
        except Exception:
            # 예외 발생 시 키 해제 보장
            try:
                self._send_input(scan_code, is_extended, True)
            except:
                pass
            return False
        
        finally:
            if is_macro_trigger:
                # 비동기 정리
                old_timer = self._cleanup_timers.get(key)
                if old_timer:
                    old_timer.cancel()
                
                timer = threading.Timer(CLEANUP_DELAY, self._cleanup_executing_key, args=(key,))
                self._cleanup_timers[key] = timer
                timer.start()
    
    def _cleanup_executing_key(self, key):
        """실행 키 정리"""
        self.executing_keys.discard(key)
        self._cleanup_timers.pop(key, None)
    
    def _run_once(self, trigger, actions):
        """mode 2: 1회 실행"""
        event = self.mode2_events.get(trigger)
        if event:
            event.clear()
        
        try:
            for hold, key, delay in actions:
                if not self.macro_enabled:
                    break
                self._execute_key(key, trigger, hold, delay, 2)
        finally:
            if event:
                event.set()
    
    def _run_repeat(self, trigger, actions):
        """mode 1: 연속 반복 (무한루프 방지)"""
        iteration_count = 0
        
        try:
            while not self.stop_signal.is_set():
                # 중단 조건 체크
                if self._should_stop_mode1(trigger):
                    break
                
                # 안전장치
                iteration_count += 1
                if iteration_count > MAX_ITERATIONS:
                    break
                
                # 액션 실행
                for hold, key, delay in actions:
                    if self._should_stop_mode1(trigger):
                        return
                    
                    if not self._execute_key(key, trigger, hold, delay, 1):
                        return
                
                # 시퀀스 딜레이
                if not self._interruptible_sleep(self.timings['sequence'], trigger):
                    break
        
        finally:
            # 확실한 상태 정리
            with self._lock:
                self.is_running = False
                self.current_macro = None
                self.pressed_keys.discard(trigger)
    
    def start(self, trigger):
        """매크로 시작"""
        if not self.macro_enabled:
            return False
        
        info = self.macros.get(trigger)
        if not info:
            return False
        
        mode = info.get('mode', 0)
        if mode == 0:
            return False
        
        actions = info.get('actions', [])
        if not actions:
            return False
        
        if mode == 2:
            # mode 2: 중복 실행 방지
            event = self.mode2_events.get(trigger)
            if event and not event.is_set():
                return False
            
            threading.Thread(
                target=self._run_once,
                args=(trigger, actions),
                daemon=True
            ).start()
            return True
        
        elif mode == 1:
            # mode 1: 단일 실행만 허용
            with self._lock:
                if self.is_running:
                    return False
                
                self.is_running = True
                self.current_macro = trigger
                self.stop_signal.clear()
            
            threading.Thread(
                target=self._run_repeat,
                args=(trigger, actions),
                daemon=True
            ).start()
            return True
        
        return False
    
    def stop(self, trigger):
        """매크로 중단"""
        with self._lock:
            if self.current_macro == trigger:
                self.stop_signal.set()
                self.is_running = False
                self.pressed_keys.discard(trigger)
    
    def should_block_trigger(self, key):
        """트리거 차단 확인"""
        return key in self.executing_keys
    
    def cleanup(self):
        """종료 시 리소스 정리"""
        self.macro_enabled = False
        self.stop_signal.set()
        
        # 타이머 취소
        for timer in list(self._cleanup_timers.values()):
            try:
                timer.cancel()
            except:
                pass
        self._cleanup_timers.clear()
        
        # 상태 초기화
        self.pressed_keys.clear()
        self.executing_keys.clear()
        self.user_triggers.clear()