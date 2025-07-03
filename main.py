# main.py
import argparse

from coros_to_garmin import CorosToGarmin
from garmin_to_coros import GarminToCoros
# try:
#     from gooey import Gooey
# except ImportError:
#     Gooey = lambda *a, **k: (lambda f: f)

# @Gooey(program_name="COROS ↔ Garmin 데이터 연동")
def main():
    parser = argparse.ArgumentParser(description='COROS <-> Garmin 데이터 연동')
    parser.add_argument('--mode', choices=['coros2garmin', 'garmin2coros'], required=True, help='동작 모드')
    parser.add_argument('-d', '--day', type=str, help='연동할 날짜 지정 (yyyymmdd)')
    parser.add_argument('-m', '--month', type=str, help='연동할 월 지정 (yyyymm)')
    parser.add_argument('-all', '--all', action='store_true', help='전체 데이터 연동')
    parser.add_argument('-u', '--upload-only', action='store_true', help='다운로드된 FIT 파일만 업로드')
    parser.add_argument('-f', '--file', type=str, nargs='*', help='특정 FIT 파일(들)만 업로드')
    args = parser.parse_args()

    # 인자 유효성 체크 및 안내
    if args.upload_only:
        # 업로드 온리: 파일 인자 필수, 날짜/월/전체 인자 무시
        if not args.file:
            print("[오류] 업로드만 모드에서는 -f/--file FIT 파일을 반드시 지정해야 합니다.")
            return
        # 날짜/월/전체 인자 무시 안내
        if args.day or args.month or args.all:
            print("[안내] 업로드만 모드에서는 날짜/월/전체 인자는 무시됩니다.")
    else:
        # 다운로드/다운로드+업로드: 날짜/월/전체 인자 필요, 파일 인자 무시
        if not (args.day or args.month or args.all):
            from datetime import datetime, timedelta
            args.day = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            print(f"[안내] 날짜/월/전체 인자가 없어 기본값({args.day})이 사용됩니다.")
        if args.file:
            print("[안내] 다운로드/다운로드+업로드 모드에서는 파일 인자는 무시됩니다.")

    if args.mode == 'coros2garmin':
        CorosToGarmin().run(args)
    elif args.mode == 'garmin2coros':
        GarminToCoros().run(args)

if __name__ == "__main__":
    main()