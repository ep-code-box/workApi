# PyInstaller spec file for COROS <-> Garmin Activity Migration GUI
# 빌드: pyinstaller pyinstaller.spec

block_cipher = None

import sys
import os
from PyInstaller.utils.hooks import collect_submodules

# 외부 모듈 자동 포함 (ttkbootstrap 등)
hiddenimports = collect_submodules('ttkbootstrap')

# 데이터 파일(설정, 예시, exports 폴더) 포함
# (exports 폴더는 빈 폴더로는 포함 안되므로 최소 1개 더미파일 필요)
datas = [
    ('config.py', '.'),
    ('config.py.example', '.'),
    ('README.md', '.'),
    ('exports/coros', 'exports/coros'),
    ('exports/garmin', 'exports/garmin'),
]

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
    console=False,  # GUI only
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
