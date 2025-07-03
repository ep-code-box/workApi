def parse_day(day_str):
    # 지원: 20250703, 2025-07-03
    if not day_str:
        return None
    try:
        return datetime.strptime(day_str, "%Y%m%d").date()
    except ValueError:
        return datetime.strptime(day_str, "%Y-%m-%d").date()
from config import load_config

import os
import requests
import hashlib
import argparse
from datetime import datetime, timedelta
from garminconnect import Garmin
import concurrent.futures
import sys
import time
import random


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
    #print("COROS 로그인 응답:", res_json)
    if res_json.get("result") not in ["0000", "1000"]:
        raise Exception(f"COROS 로그인 실패: {res_json.get('message')}")
    return res_json["data"]["accessToken"]

def coros_get_activities(token, start_day, end_day):
    headers = {
        "accesstoken": token,
        "Content-Type": "application/json"
    }
    url = f"https://teamapi.coros.com/activity/query?size=50&pageNumber=1&startDay={start_day}&endDay={end_day}&modeList="
    res = requests.get(url, headers=headers)
    return res.json().get("data", {}).get("dataList", [])

def coros_get_month_activities(token, year_month):
    start_day = f"{year_month}01"
    year = int(year_month[:4])
    month = int(year_month[4:6])
    if month == 12:
        end_year = year + 1
        end_month = 1
    else:
        end_year = year
        end_month = month + 1
    end_day = (datetime(end_year, end_month, 1) - timedelta(days=1)).strftime("%Y%m%d")
    return coros_get_activities(token, start_day, end_day)

def coros_get_all_activities(token):
    headers = {
        "accesstoken": token,
        "Content-Type": "application/json"
    }
    page_index = 1
    all_activities = []
    while True:
        url = f"https://teamapi.coros.com/activity/query?size=50&pageNumber={page_index}&modeList="
        res = requests.get(url, headers=headers).json()
        if not res.get("data", {}).get("dataList"):
            break
        all_activities.extend(res["data"]["dataList"])
        page_index += 1
    return all_activities

def coros_download_fit(token, label_id, sport_type, date_label, output_dir):
    filename = os.path.join(output_dir, f"{date_label}_{label_id}.fit")
    if os.path.exists(filename):
        return filename
    url = (
        "https://teamapi.coros.com/activity/detail/download"
        f"?labelId={label_id}&sportType={sport_type}&fileType=4"
    )
    headers = {
        "accessToken": token,
    }
    try:
        res = requests.get(url, headers=headers)
        try:
            res_json = res.json()
        except Exception:
            return None

        if res_json.get("result") == "0000" and "fileUrl" in res_json.get("data", {}):
            file_url = res_json["data"]["fileUrl"]
            fit_res = requests.get(file_url)
            if fit_res.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(fit_res.content)
                return filename
            else:
                return None
        else:
            return None
    except Exception:
        return None


# 클래스화
class CorosToGarmin:
    def __init__(self, output_dir=None):
        self.config = load_config()
        self.COROS_EMAIL = self.config.get('COROS_EMAIL', '')
        self.COROS_PASSWORD = self.config.get('COROS_PASSWORD', '')
        self.GARMIN_USERNAME = self.config.get('GARMIN_USERNAME', '')
        self.GARMIN_PASSWORD = self.config.get('GARMIN_PASSWORD', '')
        self.ROOT_DIR = output_dir if output_dir else self.config.get('OUTPUT_DIR', './exports')
        self.OUTPUT_DIR = os.path.join(self.ROOT_DIR, "coros")
        self.garmin = None  # 로그인된 Garmin 객체
        self.coros_token = None  # 로그인된 COROS 토큰

    def garmin_login(self, username, password):
        if self.garmin is not None:
            print("🔑 이미 가민 로그인됨")
            return self.garmin
        try:
            garmin = Garmin(username, password)
            garmin.login()
            print("🔑 가민 로그인 성공")
            self.garmin = garmin
            return garmin
        except Exception as e:
            print(f"⛔ 가민 로그인 실패: {e}")
            self.garmin = None
            return None
    def coros_login(self, email, password):
        if self.coros_token is not None:
            print("🔑 이미 COROS 로그인됨")
            return self.coros_token
        try:
            token = coros_login(email, password)
            print("🔑 COROS 로그인 성공")
            self.coros_token = token
            return token
        except Exception as e:
            print(f"⛔ COROS 로그인 실패: {e}")
            self.coros_token = None
            return None

    def upload_to_garmin(self, file_path, garmin):
        try:
            result = garmin.upload_activity(file_path)
            time.sleep(random.uniform(0.2, 0.5))  # 업로드 후 짧은 대기
            return (file_path, None)  # 성공
        except Exception as e:
            time.sleep(random.uniform(3, 5))  # 에러 시 충분히 대기
            return (file_path, str(e))  # 실패

    def run(self, args):
        # 업로드만: 가민만 로그인
        if getattr(args, 'upload_only', False) or getattr(args, 'file', None):
            garmin = self.garmin_login(self.GARMIN_USERNAME, self.GARMIN_PASSWORD)
            if not garmin:
                print("⛔ 가민 로그인 실패. 프로그램 종료.")
                return
            fit_files = args.file if getattr(args, 'file', None) else [
                os.path.join(self.OUTPUT_DIR, f)
                for f in os.listdir(self.OUTPUT_DIR)
                if f.endswith(".fit")
            ]
            print(f"🚀 {len(fit_files)}개 FIT 파일을 가민에 업로드합니다.")
            self._upload_files(garmin, fit_files)
            return
        # 다운로드만: 코로스만 로그인
        elif getattr(args, 'download_only', False):
            token = self.coros_login(self.COROS_EMAIL, self.COROS_PASSWORD)
            if not token:
                print("⛔ COROS 로그인 실패. 프로그램 종료.")
                return
            fit_files = self._download_files(token, args)
            return
        # 다운로드+업로드: 둘 다 로그인
        else:
            token = self.coros_login(self.COROS_EMAIL, self.COROS_PASSWORD)
            if not token:
                print("⛔ COROS 로그인 실패. 프로그램 종료.")
                return
            garmin = self.garmin_login(self.GARMIN_USERNAME, self.GARMIN_PASSWORD)
            if not garmin:
                print("⛔ 가민 로그인 실패. 프로그램 종료.")
                return
            fit_files = self._download_files(token, args)
            self._upload_files(garmin, fit_files)

    def _download_files(self, token, args):
        if args.day:
            # day 파라미터가 YYYY-MM-DD 또는 YYYYMMDD 모두 지원
            day_str = args.day
            if '-' in day_str:
                day_fmt = day_str.replace('-', '')
            else:
                day_fmt = day_str
            print(f"📅 일자 연동: {day_fmt}")
            activities = coros_get_activities(token, day_fmt, day_fmt)
        elif args.month:
            print(f"🗓️ 월별 연동: {args.month}")
            activities = coros_get_month_activities(token, args.month)
        elif args.all:
            print("🌏 전체 데이터 연동")
            activities = coros_get_all_activities(token)
            print(f"📦 전체 활동 개수: {len(activities)}")
        else:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            print(f"⏰ 기본(어제) 연동: {yesterday}")
            activities = coros_get_activities(token, yesterday, yesterday)

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
            future_to_activity = {
                executor.submit(
                    coros_download_fit,
                    token,
                    activity["labelId"],
                    activity["sportType"],
                    activity["date"],
                    self.OUTPUT_DIR
                ): activity
                for activity in activities
            }
            for future in concurrent.futures.as_completed(future_to_activity):
                fit_file = future.result()
                done += 1
                sys.stdout.write(f"\r⬇️ {done}/{total} 다운로드 완료")
                sys.stdout.flush()
                if fit_file:
                    fit_files.append(fit_file)
        print()  # 줄바꿈
        return fit_files

    def _upload_files(self, garmin, fit_files):
        total = len(fit_files)
        done = 0
        error_list = []
        error_count = 0
        print("⬆️ 가민 업로드 진행 중...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(self.upload_to_garmin, fit_file, garmin) for fit_file in fit_files]
            for future in concurrent.futures.as_completed(futures):
                file_path, error = future.result()
                done += 1
                if error:
                    error_count += 1
                    error_list.append(f"{file_path} | 사유: {error}")
                sys.stdout.write(f"\r⬆️ {done}/{total} 업로드 완료 (에러 {error_count}건)")
                sys.stdout.flush()
        print("\n✅ 모든 작업 완료.")
        if error_list:
            print("\n❌ 업로드 에러 목록:")
            for err in error_list:
                print(f"- {err}")
