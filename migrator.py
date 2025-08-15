import os
import sys
import concurrent.futures
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from utils import load_config
from client import CorosClient, GarminClient
from constants import DEFAULT_OUTPUT_DIR

class BaseMigrator(ABC):
    """데이터 마이그레이션의 공통 로직을 담는 추상 기본 클래스"""
    def __init__(self, output_dir_name, output_dir=None):
        self.config = load_config()
        self.coros_client = CorosClient(self.config.get('COROS_EMAIL'), self.config.get('COROS_PASSWORD'))
        self.garmin_client = GarminClient(self.config.get('GARMIN_USERNAME'), self.config.get('GARMIN_PASSWORD'))
        
        root_dir = output_dir if output_dir else self.config.get('OUTPUT_DIR', DEFAULT_OUTPUT_DIR)
        self.output_dir = os.path.join(root_dir, output_dir_name)
        os.makedirs(self.output_dir, exist_ok=True)

    @abstractmethod
    def _download_activities(self, args):
        """소스 플랫폼에서 활동을 다운로드합니다. 자식 클래스에서 구현해야 합니다."""
        pass

    @abstractmethod
    def _upload_activities(self, fit_files, **kwargs):
        """대상 플랫폼으로 활동을 업로드합니다. 자식 클래스에서 구현해야 합니다."""
        pass

    def run(self, args):
        """마이그레이션 프로세스를 실행하는 메인 메서드"""
        # 업로드 전용 모드
        if args.upload_only:
            if not args.file:
                print("[오류] 업로드 전용 모드에서는 --file 인자가 필수입니다.")
                return
            print(f"🚀 {len(args.file)}개 FIT 파일을 업로드합니다.")
            self._upload_activities(args.file)
            return

        # 다운로드 전용 모드
        if args.download_only:
            print("⬇️ 활동 다운로드를 시작합니다.")
            self._download_activities(args)
            return

        # 기본 (다운로드 + 업로드) 모드
        print("⬇️ 활동 다운로드를 시작합니다.")
        fit_files, context = self._download_activities(args)
        if not fit_files:
            print("✅ 처리할 파일이 없어 종료합니다.")
            return
        
        print(f"\n⬆️ {len(fit_files)}개 FIT 파일 업로드를 시작합니다.")
        self._upload_activities(fit_files, **context)
