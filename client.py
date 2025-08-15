import requests
import hashlib
import os
from garminconnect import Garmin

from constants import (
    COROS_LOGIN_URL,
    COROS_ACTIVITY_QUERY_URL,
    COROS_DOWNLOAD_URL,
    COROS_UPLOAD_URL,
    COROS_SUCCESS_CODE
)

class CorosClient:
    """COROS API와 통신을 담당하는 클라이언트"""
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.token = None

    def login(self):
        """COROS API에 로그인하여 토큰을 발급받습니다."""
        md5_pwd = hashlib.md5(self.password.encode('utf-8')).hexdigest()
        payload = {"account": self.email, "accountType": 2, "pwd": md5_pwd}
        headers = {"Content-Type": "application/json"}
        try:
            res = requests.post(COROS_LOGIN_URL, json=payload, headers=headers)
            res.raise_for_status()
            res_json = res.json()
            if res_json.get("result") != COROS_SUCCESS_CODE:
                raise Exception(f"COROS 로그인 실패: {res_json.get('message')}")
            self.token = res_json["data"]["accessToken"]
            print("🔑 COROS 로그인 성공")
            return self.token
        except requests.exceptions.RequestException as e:
            raise Exception(f"COROS API 요청 실패: {e}")

    def get_activities(self, start_day, end_day, size=50):
        """지정된 기간의 활동 목록을 가져옵니다."""
        if not self.token:
            raise Exception("COROS 클라이언트가 로그인되지 않았습니다.")
        
        activities = []
        page_number = 1
        while True:
            url = f"{COROS_ACTIVITY_QUERY_URL}?size={size}&pageNumber={page_number}&startDay={start_day}&endDay={end_day}&modeList="
            headers = {"accesstoken": self.token, "Content-Type": "application/json"}
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            res_json = res.json()
            data = res_json.get("data", {}).get("dataList", [])
            if not data:
                break
            activities.extend(data)
            page_number += 1
        return activities

    def download_fit_file(self, label_id, sport_type, output_dir):
        """특정 활동의 FIT 파일을 다운로드합니다."""
        if not self.token:
            raise Exception("COROS 클라이언트가 로그인되지 않았습니다.")

        url = f"{COROS_DOWNLOAD_URL}?labelId={label_id}&sportType={sport_type}&fileType=4"
        headers = {"accessToken": self.token}
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        res_json = res.json()

        if res_json.get("result") == COROS_SUCCESS_CODE and "fileUrl" in res_json.get("data", {}):
            file_url = res_json["data"]["fileUrl"]
            fit_res = requests.get(file_url)
            fit_res.raise_for_status()
            return fit_res.content
        return None

    def upload_activity(self, file_path):
        """FIT 파일을 COROS에 업로드합니다."""
        if not self.token:
            raise Exception("COROS 클라이언트가 로그인되지 않았습니다.")

        url = COROS_UPLOAD_URL
        headers = {"accesstoken": self.token}
        with open(file_path, 'rb') as f:
            files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
            res = requests.post(url, headers=headers, files=files)
            res.raise_for_status()
            res_json = res.json()
            if res_json.get("result") == COROS_SUCCESS_CODE:
                return True, res_json.get('message', '성공')
            else:
                return False, res_json.get('message', '알 수 없는 오류')

class GarminClient:
    """Garmin Connect API와 통신을 담당하는 클라이언트"""
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.client = None

    def login(self):
        """Garmin Connect에 로그인합니다."""
        try:
            self.client = Garmin(self.username, self.password)
            self.client.login()
            print("🔑 Garmin 로그인 성공")
            return True
        except Exception as e:
            self.client = None
            raise Exception(f"Garmin 로그인 실패: {e}")

    def get_activities_by_date(self, start_date, end_date):
        """지정된 기간의 활동 목록을 가져옵니다."""
        if not self.client:
            raise Exception("Garmin 클라이언트가 로그인되지 않았습니다.")
        return self.client.get_activities_by_date(start_date, end_date)

    def download_activity(self, activity_id):
        """특정 활동을 FIT 파일로 다운로드합니다."""
        if not self.client:
            raise Exception("Garmin 클라이언트가 로그인되지 않았습니다.")
        return self.client.download_activity(
            activity_id, dl_fmt=self.client.ActivityDownloadFormat.ORIGINAL
        )

    def upload_activity(self, file_path):
        """FIT 파일을 Garmin Connect에 업로드합니다."""
        if not self.client:
            raise Exception("Garmin 클라이언트가 로그인되지 않았습니다.")
        return self.client.upload_activity(file_path)
