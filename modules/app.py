import keyboard
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from core import MacroCore
from handler import EventHandler
from tray import TrayIcon

class MacroApp:
    """매크로 애플리케이션"""
    __slots__ = ('core', 'handler', 'tray', 'toggle_key', 'force_quit_keys')

    def __init__(self):
        self.core = MacroCore()
        self.handler = None
        self.tray = TrayIcon(self.on_exit)
        self.toggle_key = '`'
        self.force_quit_keys = ['alt', 'shift', 'delete']

    def on_exit(self):
        """종료 콜백"""
        if self.handler:
            self.handler.shutdown()
    
    def _normalize_macros(self, raw_macros):
        """복수 트리거를 개별로 변환"""
        if not isinstance(raw_macros, dict):
            raise ValueError("MACROS must be a dictionary")
        
        normalized = {}
        for trigger, info in raw_macros.items():
            if isinstance(trigger, tuple):
                for key in trigger:
                    if not isinstance(key, str):
                        raise ValueError(f"Trigger key must be string: {key}")
                    normalized[key] = info
            elif isinstance(trigger, str):
                normalized[trigger] = info
            else:
                raise ValueError(f"Invalid trigger type: {type(trigger)}")
        
        return normalized
    
    def _parse_action(self, action, is_last, defaults):
        """action을 (hold, key, delay) 형식으로 변환"""
        if not isinstance(action, tuple):
            raise ValueError(f"Action must be tuple: {action}")
        
        action_len = len(action)
        
        if action_len == 1:
            # ('key',)
            return (defaults['press'], action[0], 0 if is_last else defaults['release'])
        
        elif action_len == 2:
            # (hold, 'key',) or ('key', delay)
            if isinstance(action[0], (int, float)):
                return (action[0], action[1], 0 if is_last else defaults['release'])
            else:
                delay = action[1] if action[1] is not None else (0 if is_last else defaults['release'])
                return (defaults['press'], action[0], delay)
        
        elif action_len == 3:
            # (hold, 'key', delay)
            hold = action[0] if action[0] is not None else defaults['press']
            delay = action[2] if action[2] is not None else (0 if is_last else defaults['release'])
            return (hold, action[1], delay)
        
        else:
            raise ValueError(f"Action must have 1-3 elements: {action}")
    
    def _convert_actions(self, macros, defaults):
        """actions를 (hold, key, delay) 튜플로 변환"""
        converted = {}
        
        for key, info in macros.items():
            if not isinstance(info, dict):
                raise ValueError(f"Macro info must be dict for key '{key}'")
            
            if 'actions' not in info:
                raise ValueError(f"Missing 'actions' for key '{key}'")
            
            if 'mode' not in info:
                raise ValueError(f"Missing 'mode' for key '{key}'")
            
            raw_actions = info['actions']
            if not isinstance(raw_actions, list) or not raw_actions:
                raise ValueError(f"Actions must be non-empty list for key '{key}'")
            
            try:
                parsed_actions = [
                    self._parse_action(action, i == len(raw_actions) - 1, defaults)
                    for i, action in enumerate(raw_actions)
                ]
            except Exception as e:
                raise ValueError(f"Error parsing actions for key '{key}': {e}")
            
            converted[key] = {
                'actions': parsed_actions, 
                'mode': info['mode']
            }
        
        return converted
    
    def load_config(self, config):
        """설정 로드"""
        if not hasattr(config, 'MACROS'):
            raise ValueError("config.MACROS not found")
        
        # 설정 검증
        if not self.validate_config(config):
            raise ValueError("Invalid configuration")
        
        # 매크로 변환
        try:
            normalized = self._normalize_macros(config.MACROS)
            
            defaults = {
                'press': config.KEY_PRESS_DURATION,
                'release': config.KEY_RELEASE_DURATION,
                'sequence': config.SEQUENCE_DELAY
            }
            
            converted = self._convert_actions(normalized, defaults)
        except Exception as e:
            raise ValueError(f"Configuration conversion failed: {e}")
        
        # 코어 설정
        self.core.configure(converted, defaults)
        
        # 전역 설정
        self.toggle_key = config.TOGGLE_KEY
        self.force_quit_keys = getattr(config, 'FORCE_QUIT_KEYS', ['alt', 'shift', 'delete'])
        
        # 핸들러 생성
        self.handler = EventHandler(self.core, self.toggle_key, self.force_quit_keys)
    
    def setup_hooks(self):
        """키보드 훅 등록"""
        try:
            # 토글 키
            keyboard.on_press_key(self.toggle_key, self.handler.handle_press, suppress=True)
            keyboard.on_release_key(self.toggle_key, self.handler.handle_release, suppress=True)
            
            # 강제 종료 키
            for key in self.force_quit_keys:
                keyboard.on_press_key(key, self.handler.handle_press, suppress=False)
                keyboard.on_release_key(key, self.handler.handle_release, suppress=False)
            
            # 매크로 키
            for key in self.core.macros:
                keyboard.on_press_key(key, self.handler.handle_press, suppress=True)
                keyboard.on_release_key(key, self.handler.handle_release, suppress=True)
        
        except Exception as e:
            raise RuntimeError(f"Failed to setup keyboard hooks: {e}")
    
    def run(self):
        """실행"""
        # 트레이 아이콘 시작
        self.tray.run()
        
        # 키보드 훅 등록
        self.setup_hooks()
        
        # 시작 메시지
        print("=" * 60)
        print("KeyM 실행 중")
        print("=" * 60)
        print(f"토글 키: [{self.toggle_key}]")
        print(f"강제 종료: [{' + '.join(self.force_quit_keys).upper()}]")
        print(f"등록된 매크로: {len(self.core.macros)}개")
        
        # 매크로 목록 출력
        if self.core.macros:
            print("\n매크로 키:")
            for key, info in self.core.macros.items():
                mode_str = {0: "비활성", 1: "연속", 2: "단일"}.get(info['mode'], "알수없음")
                print(f"  [{key}] - {mode_str} ({len(info['actions'])}개 액션)")
        
        print("=" * 60)
        
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            print("\n인터럽트 감지됨")
            self.on_exit()
        except Exception as e:
            print(f"\n예상치 못한 오류: {e}")
            self.on_exit()
    
    def validate_config(self, cfg):
        """설정 검증 (최적화)"""
        # 필수 속성 확인
        if not hasattr(cfg, 'MACROS'):
            print("[오류] config.MACROS가 없습니다")
            return False
        
        if not hasattr(cfg, 'TOGGLE_KEY'):
            print("[오류] config.TOGGLE_KEY가 없습니다")
            return False
        
        if not hasattr(cfg, 'KEY_PRESS_DURATION'):
            print("[오류] config.KEY_PRESS_DURATION이 없습니다")
            return False
        
        if not hasattr(cfg, 'KEY_RELEASE_DURATION'):
            print("[오류] config.KEY_RELEASE_DURATION이 없습니다")
            return False
        
        if not hasattr(cfg, 'SEQUENCE_DELAY'):
            print("[오류] config.SEQUENCE_DELAY가 없습니다")
            return False
        
        # MACROS 검증
        if not isinstance(cfg.MACROS, dict):
            print("[오류] MACROS는 딕셔너리여야 합니다")
            return False
        
        if not cfg.MACROS:
            print("[오류] MACROS가 비어있습니다")
            return False
        
        # 타이밍 값 검증 (간소화)
        if cfg.KEY_PRESS_DURATION < 0 or cfg.KEY_RELEASE_DURATION < 0 or cfg.SEQUENCE_DELAY < 0:
            print("[오류] 타이밍 값은 0 이상이어야 합니다")
            return False
        
        # 각 매크로 간단 검증 (상세 검증은 load_config에서)
        for trigger, info in cfg.MACROS.items():
            if not isinstance(info, dict):
                print("[오류] 매크로 정보는 딕셔너리여야 합니다")
                return False
            
            if 'mode' not in info or 'actions' not in info:
                print("[오류] mode와 actions 필드가 필요합니다")
                return False
            
            if info['mode'] not in [0, 1, 2]:
                print("[오류] mode는 0, 1, 2 중 하나여야 합니다")
                return False
            
            if not isinstance(info['actions'], list) or not info['actions']:
                print("[오류] actions는 비어있지 않은 리스트여야 합니다")
                return False
        
        print("설정 검증 완료")
        return True