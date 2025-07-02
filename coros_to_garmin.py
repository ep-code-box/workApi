from config import COROS_EMAIL, COROS_PASSWORD, GARMIN_USERNAME, GARMIN_PASSWORD, OUTPUT_DIR

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
        # output_dir이 주어지면 사용, 아니면 config의 OUTPUT_DIR
        self.ROOT_DIR = output_dir if output_dir else OUTPUT_DIR
        self.OUTPUT_DIR = os.path.join(self.ROOT_DIR, "coros")

    def garmin_login(self, username, password):
        try:
            garmin = Garmin(username, password)
            garmin.login()
            print("가민 로그인 성공")
            return garmin
        except Exception as e:
            print(f"가민 로그인 실패: {e}")
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
        # COROS 로그인 체크
        if not args.upload_only and not args.file:
            try:
                token = coros_login(COROS_EMAIL, COROS_PASSWORD)
                print("🔑 COROS 로그인 성공")
            except Exception as e:
                print(f"⛔ COROS 로그인 실패: {e}")
                return
        else:
            token = None

        # 가민 로그인 체크
        garmin = self.garmin_login(GARMIN_USERNAME, GARMIN_PASSWORD)
        if not garmin:
            print("⛔ 가민 로그인 실패. 프로그램 종료.")
            return

        # 특정 파일만 업로드 옵션
        if args.file:
            fit_files = args.file
            print(f"🚀 {len(fit_files)}개 FIT 파일을 선택 업로드합니다.")
        elif args.upload_only:
            # OUTPUT_DIR 내의 모든 .fit 파일을 업로드
            fit_files = [
                os.path.join(self.OUTPUT_DIR, f)
                for f in os.listdir(self.OUTPUT_DIR)
                if f.endswith(".fit")
            ]
            print(f"🚀 {len(fit_files)}개 FIT 파일을 가민에 업로드합니다.")
        else:
            # 연동 옵션 처리
            if args.day:
                print(f"📅 일자 연동: {args.day}")
                activities = coros_get_activities(token, args.day, args.day)
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
                return

            print(f"🔍 샘플 활동 데이터: {activities[0]}")
            print(f"🚀 총 {len(activities)}개 활동 다운로드 및 업로드 시작")

            os.makedirs(self.OUTPUT_DIR, exist_ok=True)

            # 병렬 다운로드
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

        # 병렬 업로드
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
