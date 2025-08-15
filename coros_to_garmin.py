import os
import sys
import concurrent.futures
from datetime import datetime, timedelta

from migrator import BaseMigrator
from constants import COROS_DIR_NAME

class CorosToGarmin(BaseMigrator):
    """COROS에서 Garmin으로 활동을 이전합니다."""
    def __init__(self, output_dir=None):
        super().__init__(COROS_DIR_NAME, output_dir)

    def _download_activities(self, args):
        self.coros_client.login()

        if args.day:
            start_day = end_day = args.day
        elif args.month:
            year, month = int(args.month[:4]), int(args.month[4:6])
            start_day = f"{year:04d}{month:02d}01"
            next_month = datetime(year, month, 1).replace(day=28) + timedelta(days=4)
            end_day = (next_month - timedelta(days=next_month.day)).strftime('%Y%m%d')
        elif args.all:
            start_day = "20100101"
            end_day = datetime.now().strftime('%Y%m%d')
        else:
            start_day = end_day = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')

        print(f"🔍 {start_day} ~ {end_day} COROS 활동을 조회합니다.")
        activities = self.coros_client.get_activities(start_day, end_day)

        if not activities:
            print("⚠️ 해당 기간에 다운로드할 활동이 없습니다.")
            return [], None

        print(f"🚀 총 {len(activities)}개 활동 다운로드 시작")
        fit_files = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_map = { executor.submit(self.coros_client.download_fit_file, act["labelId"], act["sportType"], self.output_dir): act for act in activities }
            for future in concurrent.futures.as_completed(future_map):
                activity = future_map[future]
                try:
                    fit_content = future.result()
                    if fit_content:
                        date_label = str(activity.get("date", ""))[:8]
                        filename = os.path.join(self.output_dir, f"{date_label}_{activity['labelId']}.fit")
                        with open(filename, 'wb') as f: f.write(fit_content)
                        fit_files.append(filename)
                        print(f"⬇️ 다운로드 완료: {os.path.basename(filename)}")
                except Exception as e:
                    print(f"❌ 다운로드 실패 (ID: {activity['labelId']}): {e}")
        
        return fit_files, {"coros_activities": activities}

    def _upload_activities(self, fit_files, **kwargs):
        self.garmin_client.login()
        coros_activities = kwargs.get("coros_activities", [])
        if not coros_activities:
            print("⚠️ 활동 컨텍스트가 없어 중복 체크를 건너뜁니다.")
            garmin_activities = []
        else:
            try:
                start_date = min(datetime.strptime(str(act['date'])[:8], '%Y%m%d') for act in coros_activities)
                end_date = max(datetime.strptime(str(act['date'])[:8], '%Y%m%d') for act in coros_activities)
                print(f"🔍 {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} Garmin 활동을 조회하여 중복을 확인합니다.")
                garmin_activities = self.garmin_client.get_activities_by_date(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            except Exception as e:
                print(f"⚠️ Garmin 활동 조회 실패, 중복 체크를 건너뜁니다: {e}")
                garmin_activities = []

        # Build a list of existing Garmin activities for a more nuanced check
        garmin_activities_for_check = []
        for act in garmin_activities:
            try:
                start_time_utc = datetime.fromtimestamp(act['startTimeInSeconds'] + act['startTimeOffsetInSeconds'])
                duration_sec = int(act['durationInSeconds'])
                garmin_activities_for_check.append({
                    "start_minute": start_time_utc.strftime('%Y%m%d%H%M'),
                    "duration": duration_sec
                })
            except (KeyError, TypeError):
                continue # Skip activities missing necessary data

        files_to_upload = []
        for fit_file in fit_files:
            is_duplicate = False
            try:
                label_id = os.path.basename(fit_file).split('_')[1].split('.')[0]
                c_act = next((act for act in coros_activities if str(act.get('labelId')) == label_id), None)
                if c_act:
                    date_val = str(c_act.get('date', ''))
                    try:
                        c_start_dt = datetime.strptime(date_val, '%Y%m%d%H%M%S')
                        c_start_minute = c_start_dt.strftime('%Y%m%d%H%M')
                        c_duration_sec = int(c_act.get('duration', 0))

                        # Perform the nuanced duplicate check
                        for g_act_check in garmin_activities_for_check:
                            if g_act_check['start_minute'] == c_start_minute:
                                if abs(g_act_check['duration'] - c_duration_sec) < 15: # 15-second tolerance
                                    is_duplicate = True
                                    break
                        
                        if is_duplicate:
                            print(f"⏭️ 건너뛰기 (오차범위 내 중복된 활동 발견): {os.path.basename(fit_file)}")
                            continue

                    except ValueError:
                        print(f"- [정보] COROS 활동(ID: {label_id})의 날짜 형식이 예상과 다릅니다. 중복 검사를 건너뛰고 업로드를 시도합니다.")
            
            except (IndexError, StopIteration):
                print(f"⚠️ 파일명 형식 오류 또는 활동 정보를 찾을 수 없음, 업로드 목록에 포함: {os.path.basename(fit_file)}")
            
            files_to_upload.append(fit_file)

        if not files_to_upload:
            print("✅ 업로드할 새로운 활동이 없습니다.")
            return

        print(f"⬆️ {len(files_to_upload)}개 신규 활동 Garmin 업로드 진행 중...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_map = {executor.submit(self.garmin_client.upload_activity, file): file for file in files_to_upload}
            for future in concurrent.futures.as_completed(future_map):
                filename = future_map[future]
                try:
                    future.result()
                    print(f"⬆️ 업로드 성공: {os.path.basename(filename)}")
                except Exception as e:
                    print(f"❌ 업로드 실패 ({os.path.basename(filename)}): {e}")