import os
import sys
import re

def resource_path(relative_path):
    """ PyInstaller/로컬 환경 모두에서 리소스 파일의 절대 경로를 반환합니다. """
    try:
        # PyInstaller는 임시 폴더를 생성하고 _MEIPASS에 경로를 저장합니다.
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def load_config(config_path=None):
    """ config.py 파일에서 설정을 읽어 딕셔너리로 반환합니다. """
    if config_path is None:
        # 기본 config.py 파일 경로를 동적으로 찾습니다.
        # 이 코드는 utils.py에 있으므로, 상위 디렉토리의 config.py를 찾아야 합니다.
        base_dir = os.path.dirname(resource_path('.'))
        config_path = os.path.join(base_dir, "config.py")

    config = {}
    if not os.path.exists(config_path):
        print(f"[오류] 설정 파일을 찾을 수 없습니다: {config_path}")
        return config

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            text = f.read()

        def get_val(key):
            """ 정규표현식으로 설정 값을 추출합니다. """
            m = re.search(rf'{key}\s*=\s*["\'](.*?)["\']', text)
            return m.group(1) if m else ""

        config['COROS_EMAIL'] = get_val('COROS_EMAIL')
        config['COROS_PASSWORD'] = get_val('COROS_PASSWORD')
        config['GARMIN_USERNAME'] = get_val('GARMIN_USERNAME')
        config['GARMIN_PASSWORD'] = get_val('GARMIN_PASSWORD')
        config['OUTPUT_DIR'] = get_val('OUTPUT_DIR') or './exports' # 기본값 설정

    except Exception as e:
        print(f"[오류] 설정 파일 읽기 실패: {e}")

    return config
