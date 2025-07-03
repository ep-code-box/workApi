# PyInstaller spec file for COROS <-> Garmin Activity Migration GUI
# 빌드: pyinstaller pyinstaller.spec

block_cipher = None

import sys
import os
from PyInstaller.utils.hooks import collect_submodules

# 데이터 파일(설정, 예시 등) 포함
datas = [
    ('config.py', '.'),
    ('config.py.example', '.'),
    ('main.py', '.'),
    ('coros_to_garmin.py', '.'),
    ('garmin_to_coros.py', '.'),
    ('icon.png', '.'),
]

# 주요 다운로드 필요 외부 패키지 (requirements.txt에 반드시 포함되어야 함)
# - requests
# - garminconnect
# - ttkbootstrap
# - tkcalendar
# - (필요시) gooey

# spec에서 누락 방지용 hiddenimports (동적 import 등)
hiddenimports = (
    collect_submodules('ttkbootstrap') +
    collect_submodules('tkcalendar') +
    collect_submodules('garminconnect')
)

# 경로 처리: 실행파일/스크립트 위치 기준으로 상대경로 처리
# (main.py, gui.py 등에서 아래 함수 사용 권장)
def resource_path(relative_path):
    """PyInstaller 환경/로컬 환경 모두에서 동작하는 경로 반환"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# 빌드 대상: gui.py (windowed)
icon_file = 'icon.png'
a = Analysis([
    'gui.py',
],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='coros_garmin_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 콘솔로 에러 메시지 확인
    icon=icon_file,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='coros_garmin_gui'
)
