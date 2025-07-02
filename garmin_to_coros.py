from enum import Enum, auto
import os
import requests
import argparse
import hashlib
from datetime import datetime, timedelta
import concurrent.futures
import sys
import time
import random
from garminconnect import Garmin
from config import load_config

def coros_login(email, password):
    md5_pwd = hashlib.md5(password.encode('utf-8')).hexdigest()
    url = "https://teamapi.coros.com/account/login"
    payload = {
        "account": email,
        "accountType": 2,
        "pwd": md5_pwd
    }
    headers = {"Content-Type": "application/json"}
    res = requests.post(url, json=payload, headers=headers)
    res_json = res.json()
    if res_json.get("result") not in ["0000", "1000"]:
        raise Exception(f"COROS 로그인 실패: {res_json.get('message')}")
    return res_json["data"]["accessToken"]

def coros_upload_fit(token, file_path):
    url = "https://teamapi.coros.com/activity/import"
    headers = {
        "accesstoken": token
    }
    files = {
        "file": (os.path.basename(file_path), open(file_path, "rb"), "application/octet-stream")
    }
    try:
        res = requests.post(url, headers=headers, files=files)
        if res.status_code == 200:
            res_json = res.json()
            if res_json.get("result") == "0000":
                return (file_path, None)
            else:
                return (file_path, f"COROS 업로드 실패: {res_json.get('message')}")
        else:
            return (file_path, f"HTTP {res.status_code}: {res.text}")
    except Exception as e:
        return (file_path, str(e))

def garmin_login(username, password):
    try:
        garmin = Garmin(username, password)
        garmin.login()
        print("가민 로그인 성공")
        return garmin
    except Exception as e:
        print(f"가민 로그인 실패: {e}")
        return None

def garmin_get_activities(garmin, start_date, end_date):
    # Garmin API는 날짜별 활동 조회를 지원
    activities = []
    try:
        activities = garmin.get_activities_by_date(start_date, end_date)
    except Exception as e:
        print(f"가민 활동 조회 실패: {e}")
    return activities

def download_garmin_fit(garmin, activity, output_dir):
    ActivityDownloadFormat = Garmin.ActivityDownloadFormat
    # 코로스와 유사하게 날짜+id로 파일명 생성
    date_label = None
    if "startTimeLocal" in activity:
        # 예: 2025-07-02 08:00:00
        date_label = activity["startTimeLocal"].split(" ")[0].replace("-", "")
    elif "startTime" in activity:
        date_label = activity["startTime"].split(" ")[0].replace("-", "")
    else:
        date_label = "nodate"
    activity_id = activity["activityId"]
    filename = os.path.join(output_dir, f"{date_label}_{activity_id}.fit")
    if os.path.exists(filename):
        print(f"{filename} 이미 존재")
        return filename
    try:
        print(f"다운로드 시도: {activity_id}, 포맷: FIT")
        fit_data = garmin.download_activity(activity_id, dl_fmt=ActivityDownloadFormat.ORIGINAL)
        if not fit_data:
            print(f"{activity_id} 다운로드 결과가 비어 있음")
            return None
        with open(filename, "wb") as f:
            f.write(fit_data)
        print(f"{filename} 저장 완료")
        return filename
    except Exception as e:
        print(f"{activity_id} 다운로드 실패: {e}")
        return None


# 클래스화
class GarminToCoros:
    def __init__(self, output_dir=None):
        self.config = load_config()
        self.COROS_EMAIL = self.config.get('COROS_EMAIL', '')
        self.COROS_PASSWORD = self.config.get('COROS_PASSWORD', '')
        self.GARMIN_USERNAME = self.config.get('GARMIN_USERNAME', '')
        self.GARMIN_PASSWORD = self.config.get('GARMIN_PASSWORD', '')
        self.ROOT_DIR = output_dir if output_dir else self.config.get('OUTPUT_DIR', './exports')
        self.OUTPUT_DIR = os.path.join(self.ROOT_DIR, "garmin")

    def run(self, args):
        # COROS 로그인
        try:
            token = coros_login(self.COROS_EMAIL, self.COROS_PASSWORD)
            print("🔑 COROS 로그인 성공")
        except Exception as e:
            print(f"⛔ COROS 로그인 실패: {e}")
            return

        # 업로드만 옵션 (파일 직접 지정 또는 upload_only)
        if args.file:
            fit_files = args.file
            print(f"🚀 {len(fit_files)}개 FIT 파일을 선택 업로드합니다.")
            self._upload_files(token, fit_files)
            return
        elif getattr(args, 'upload_only', False):
            fit_files = [
                os.path.join(self.OUTPUT_DIR, f)
                for f in os.listdir(self.OUTPUT_DIR)
                if f.endswith(".fit")
            ]
            print(f"🚀 {len(fit_files)}개 FIT 파일을 COROS에 업로드합니다.")
            self._upload_files(token, fit_files)
            return
        # 다운로드만 옵션
        elif getattr(args, 'download_only', False):
            garmin = garmin_login(self.GARMIN_USERNAME, self.GARMIN_PASSWORD)
            if not garmin:
                print("⛔ 가민 로그인 실패. 프로그램 종료.")
                return
            fit_files = self._download_files(garmin, args)
            return  # 여기서 반드시 return해서 업로드가 실행되지 않도록!
        # 다운로드+업로드 (기본)
        else:
            garmin = garmin_login(self.GARMIN_USERNAME, self.GARMIN_PASSWORD)
            if not garmin:
                print("⛔ 가민 로그인 실패. 프로그램 종료.")
                return
            fit_files = self._download_files(garmin, args)
            self._upload_files(token, fit_files)

    def _download_files(self, garmin, args):
        # 연동 옵션 처리
        if args.day:
            start_date = end_date = datetime.strptime(args.day, "%Y%m%d").date()
            print(f"📅 일자 연동: {args.day}")
        elif args.month:
            year = int(args.month[:4])
            month = int(args.month[4:6])
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
            print(f"🗓️ 월별 연동: {args.month}")
        elif args.all:
            start_date = datetime(2010, 1, 1).date()
            end_date = datetime.now().date()
            print("🌏 전체 데이터 연동")
        else:
            yesterday = (datetime.now() - timedelta(days=1)).date()
            start_date = end_date = yesterday
            print(f"⏰ 기본(어제) 연동: {yesterday.strftime('%Y%m%d')}")

        activities = garmin_get_activities(garmin, start_date, end_date)
        if not activities:
            print("⚠️ 활동이 없습니다.")
            return []

        print(f"🔍 샘플 활동 데이터: {activities[0]}")
        print(f"🚀 총 {len(activities)}개 활동 다운로드 시작")

        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

        fit_files = []
        total = len(activities)
        done = 0
        print("⬇️ 다운로드 진행 중...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_act = {
                executor.submit(
                    download_garmin_fit,
                    garmin,
                    activity,
                    self.OUTPUT_DIR
                ): activity
                for activity in activities
            }
            for future in concurrent.futures.as_completed(future_to_act):
                fit_file = future.result()
                done += 1
                sys.stdout.write(f"\r⬇️ {done}/{total} 다운로드 완료")
                sys.stdout.flush()
                if fit_file:
                    fit_files.append(fit_file)
        print()  # 줄바꿈
        return fit_files

    def _upload_files(self, token, fit_files):
        total = len(fit_files)
        done = 0
        error_list = []
        error_count = 0
        print("⬆️ COROS 업로드 진행 중...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(coros_upload_fit, token, fit_file) for fit_file in fit_files]
            for future in concurrent.futures.as_completed(futures):
                file_path, error = future.result()
                done += 1
                if error:
                    error_count += 1
                    error_list.append(f"{file_path} | 사유: {error}")
                sys.stdout.write(f"\r⬆️ {done}/{total} 업로드 완료 (에러 {error_count}건)")
                sys.stdout.flush()
                time.sleep(random.uniform(0.2, 0.5))  # 업로드 후 짧은 대기
        print("\n✅ 모든 작업 완료.")
        if error_list:
            print("\n❌ 업로드 에러 목록:")
            for err in error_list:
                print(f"- {err}")