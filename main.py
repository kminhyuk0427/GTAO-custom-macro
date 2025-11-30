import keyboard
import time
import threading
import sys
import os

class GameMacro:
    def __init__(self):
        self.active = True
        
        # 현재 눌린 키 추적
        self.pressed_keys = set()
        
        # 매크로 실행 상태
        self.macro_running = False
        self.current_macro_key = None
        self.stop_event = threading.Event()
        self.macro_lock = threading.Lock()
        
        # ========================================
        # 매크로 설정
        # ========================================
        self.macros = {
            '1': ['q', 'w'],              # 1번 키: q, w 반복
            '2': ['1', '2'],              # 2번 키: 1, 2 반복
            '3': ['a', 's', 'd'],         # 3번 키: a, s, d 반복
            '4': ['z', 'x', 'c', 'v'],    # 4번 키: z, x, c, v 반복
            '5': ['shift', 'space'],      # 5번 키: shift, space 반복
        }
        
        # ========================================
        # 실행 속도 설정
        # ========================================
        self.key_press_duration = 0.01    # 키 누르는 시간 (초)
        self.key_release_duration = 0.01  # 키 떼는 시간 (초)
        self.sequence_delay = 0.02        # 시퀀스 반복 간격 (초)
        
        # 시작 정보 출력
        self.print_banner()
        self.print_info()
        
    def print_banner(self):
        """프로그램 배너 출력"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print('''--------hello gta--------''')
    
    def print_info(self):
        """프로그램 정보 출력"""
        print("\n설정된 매크로:")
        print("─" * 70)
        for trigger, actions in self.macros.items():
            actions_str = ' -> '.join(actions)
            print(f"  [{trigger}] -> {actions_str} (반복)")
        
        print("\n사용법:")
        print("─" * 70)
        print("  • 매크로 키를 누르고 있으면 연속 반복됩니다")
        print("  • 키를 떼면 즉시 중단됩니다")
        print("  • 매크로 실행 중에는 다른 매크로가 무시됩니다")
        print("  • 트리거 키는 입력되지 않습니다 (완전 차단)")
        
        print(f"\n실행 속도:")
        print("─" * 70)
        print(f"  • 키 입력 간격: {self.key_press_duration*1000:.1f}ms")
        print(f"  • 반복 대기 시간: {self.sequence_delay*1000:.1f}ms")
        
        print("\n[ESC] 프로그램 종료")
        print("═" * 70)
        print("\n대기 중...\n")
    
    def press_and_release(self, key_char):
        """키 누르고 떼기"""
        try:
            keyboard.press(key_char)
            time.sleep(self.key_press_duration)
            keyboard.release(key_char)
            time.sleep(self.key_release_duration)
        except Exception as e:
            print(f"키 입력 오류 ({key_char}): {e}")
    
    def execute_macro_sequence(self, keys):
        """매크로 시퀀스 한 번 실행"""
        for key in keys:
            # 중단 요청 확인
            if self.stop_event.is_set():
                return False
            self.press_and_release(key)
        
        # 시퀀스 완료 후 대기
        time.sleep(self.sequence_delay)
        return True
    
    def macro_loop(self, trigger_key, keys):
        """매크로 반복 실행 루프"""
        keys_str = ' -> '.join(keys)
        print(f"시작: [{trigger_key}] -> {keys_str}")
        
        cycle_count = 0
        start_time = time.time()
        
        try:
            while not self.stop_event.is_set():
                # 트리거 키가 여전히 눌려있는지 확인
                if trigger_key not in self.pressed_keys:
                    break
                
                # 매크로 시퀀스 실행
                if not self.execute_macro_sequence(keys):
                    break
                
                cycle_count += 1
        
        finally:
            # 실행 시간 계산
            elapsed = time.time() - start_time
            
            # 매크로 종료 처리
            with self.macro_lock:
                self.macro_running = False
                self.current_macro_key = None
            
            print(f"종료: [{trigger_key}] (반복: {cycle_count}회, 시간: {elapsed:.2f}초)")
    
    def start_macro(self, trigger_key):
        """매크로 시작"""
        with self.macro_lock:
            # 이미 매크로가 실행 중이면 무시
            if self.macro_running:
                print(f"무시: [{trigger_key}] (실행 중: [{self.current_macro_key}])")
                return
            
            # 매크로 시작
            self.macro_running = True
            self.current_macro_key = trigger_key
            self.stop_event.clear()
        
        # 별도 스레드에서 매크로 실행
        macro_thread = threading.Thread(
            target=self.macro_loop,
            args=(trigger_key, self.macros[trigger_key]),
            daemon=True
        )
        macro_thread.start()
    
    def stop_macro(self, trigger_key):
        """매크로 중단"""
        if self.current_macro_key == trigger_key:
            self.stop_event.set()
    
    def on_key_press(self, event):
        """키 눌림 이벤트"""
        key_char = event.name
        
        # ESC 키로 종료
        if key_char == 'esc':
            print("\n" + "═" * 70)
            print("프로그램을 종료합니다...")
            print("═" * 70)
            self.active = False
            self.stop_event.set()
            sys.exit(0)
        
        # 이미 눌린 키면 무시
        if key_char in self.pressed_keys:
            return
        
        # 눌린 키 추가
        self.pressed_keys.add(key_char)
        
        # 매크로 키인 경우
        if key_char in self.macros:
            self.start_macro(key_char)
            # 트리거 키 입력 차단
            return False
    
    def on_key_release(self, event):
        """키 떼기 이벤트"""
        key_char = event.name
        
        # 눌린 키에서 제거
        self.pressed_keys.discard(key_char)
        
        # 매크로 키인 경우 중단
        if key_char in self.macros:
            self.stop_macro(key_char)
            # 트리거 키 입력 차단
            return False
    
    def run(self):
        """프로그램 실행"""
        # 모든 매크로 키에 대해 후킹 등록
        for macro_key in self.macros.keys():
            # suppress=True로 트리거 키 입력 완전 차단
            keyboard.on_press_key(macro_key, self.on_key_press, suppress=True)
            keyboard.on_release_key(macro_key, self.on_key_release, suppress=True)
        
        # ESC 키 등록
        keyboard.on_press_key('esc', self.on_key_press, suppress=False)
        
        # 프로그램 대기
        keyboard.wait()

def main():
    """메인 함수"""
    try:
        macro = GameMacro()
        macro.run()
    except KeyboardInterrupt:
        print("\n\n프로그램이 사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n오류 발생: {e}")
        print("\n상세 오류 정보:")
        import traceback
        traceback.print_exc()
        input("\n아무 키나 눌러 종료...")
        sys.exit(1)

if __name__ == "__main__":
    main()