import os
import concurrent.futures
from datetime import datetime, timedelta

from migrator import BaseMigrator
from constants import GARMIN_DIR_NAME

class GarminToCoros(BaseMigrator):
    """Garmin에서 COROS로 활동을 이전합니다."""
    def __init__(self, output_dir=None):
        super().__init__(GARMIN_DIR_NAME, output_dir)

    def _download_activities(self, args):
        """Garmin API에서 활동을 다운로드합니다."""
        self.garmin_client.login()

        if args.day:
            start_date = end_date = datetime.strptime(args.day, '%Y%m%d').strftime('%Y-%m-%d')
        elif args.month:
            year, month = int(args.month[:4]), int(args.month[4:6])
            start_date = datetime(year, month, 1).strftime('%Y-%m-%d')
            next_month = datetime(year, month, 1).replace(day=28) + timedelta(days=4)
            end_date = (next_month - timedelta(days=next_month.day)).strftime('%Y-%m-%d')
        elif args.all:
            start_date = "2010-01-01"
            end_date = datetime.now().strftime('%Y-%m-%d')
        else:
            start_date = end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        print(f"🔍 {start_date} ~ {end_date} Garmin 활동을 조회합니다.")
        activities = self.garmin_client.get_activities_by_date(start_date, end_date)

        if not activities:
            print("⚠️ 해당 기간에 다운로드할 활동이 없습니다.")
            return [], None

        print(f"🚀 총 {len(activities)}개 활동 다운로드 시작")
        fit_files = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_map = {executor.submit(self.garmin_client.download_activity, act['activityId']): act for act in activities}
            for future in concurrent.futures.as_completed(future_map):
                activity = future_map[future]
                try:
                    fit_content = future.result()
                    if fit_content:
                        date_label = activity["startTimeLocal"].split(" ")[0].replace("-", "")
                        filename = os.path.join(self.output_dir, f"{date_label}_{activity['activityId']}.fit")
                        with open(filename, 'wb') as f:
                            f.write(fit_content)
                        fit_files.append(filename)
                        print(f"⬇️ 다운로드 완료: {os.path.basename(filename)}")
                except Exception as e:
                    print(f"❌ 다운로드 실패 (ID: {activity['activityId']}): {e}")
        
        # COROS 업로드 시에는 특별한 context가 필요 없으므로 빈 dict 반환
        return fit_files, {}

    def _upload_activities(self, fit_files, **kwargs):
        """다운로드된 FIT 파일을 COROS에 업로드합니다."""
        self.coros_client.login()

        # COROS는 중복 체크 기능이 API에 내장되어 있으므로 별도 로직은 생략합니다.
        print(f"⬆️ {len(fit_files)}개 활동 COROS 업로드 진행 중...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_map = {executor.submit(self.coros_client.upload_activity, file): file for file in fit_files}
            for future in concurrent.futures.as_completed(future_map):
                filename = future_map[future]
                try:
                    success, message = future.result()
                    if success:
                        print(f"⬆️ 업로드 성공: {os.path.basename(filename)}")
                    else:
                        print(f"❌ 업로드 실패 ({os.path.basename(filename)}): {message}")
                except Exception as e:
                    print(f"❌ 업로드 실패 ({os.path.basename(filename)}): {e}")
