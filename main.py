# main.py
import argparse
from coros_to_garmin import CorosToGarmin
from garmin_to_coros import GarminToCoros

def main():
    parser = argparse.ArgumentParser(description='COROS <-> Garmin 데이터 연동')
    parser.add_argument('--mode', choices=['coros2garmin', 'garmin2coros'], required=True, help='동작 모드')
    parser.add_argument('-d', '--day', type=str, help='연동할 날짜 지정 (yyyymmdd)')
    parser.add_argument('-m', '--month', type=str, help='연동할 월 지정 (yyyymm)')
    parser.add_argument('-all', '--all', action='store_true', help='전체 데이터 연동')
    parser.add_argument('-u', '--upload-only', action='store_true', help='다운로드된 FIT 파일만 업로드')
    parser.add_argument('-f', '--file', type=str, nargs='*', help='특정 FIT 파일(들)만 업로드')
    args = parser.parse_args()

    # 날짜 기본값: 전일자
    if not args.day and not args.month and not args.all:
        from datetime import datetime, timedelta
        args.day = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

    if args.mode == 'coros2garmin':
        CorosToGarmin().run(args)
    elif args.mode == 'garmin2coros':
        GarminToCoros().run(args)

if __name__ == "__main__":
    main()