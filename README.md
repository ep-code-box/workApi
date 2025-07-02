# COROS <-> Garmin Activity Migration

이 프로젝트는 COROS 계정과 Garmin Connect 계정 간 활동 데이터를 양방향으로 전송하는 Python 스크립트입니다.

## 주요 기능

- CLI와 GUI(모던 ttkbootstrap 기반) 모두 지원
- COROS→Garmin, Garmin→COROS 양방향 연동 지원
- 날짜/월/전체/특정 파일 등 다양한 범위 선택 가능
- 다운로드/업로드/다운로드+업로드 모드 분리 (GUI/CLI 모두)
- 모든 파일 입출력은 `exports/coros`, `exports/garmin` 폴더 사용
- cross-platform: Windows/macOS 모두 지원
- 에러/진행상황/로그 출력 강화
- 파일명 규칙: `YYYYMMDD_activityId.fit` (Garmin도 동일)
- 환경설정은 `config.py`로 분리, 예시는 `config.py.example` 참고
- GUI: 날짜선택은 ttkbootstrap의 DateEntry 사용 (tkcalendar 불필요)
- GUI: 비동기(스레드) 처리로 UI 멈춤 없음
- GUI: 파일 선택, 로그 출력, 각종 옵션 직관적 제공
- **다운로드/업로드 분리:** 다운로드만, 업로드만, 다운로드+업로드를 명확히 분리하여 실행 가능 (GUI/CLI 모두)
- **날짜 선택 안정화:** DateEntry 값이 항상 selected_date와 동기화, 내부적으로 %Y%m%d로 변환하여 백엔드에 전달
- **Garmin 다운로드 파일명:** COROS와 동일하게 `YYYYMMDD_activityId.fit` 형식으로 저장


## 폴더 구조

```
config.py           # 환경설정 (계정정보 등)
config.py.example   # 예시 환경설정
coros_to_garmin.py  # COROS→Garmin 연동 클래스
garmin_to_coros.py  # Garmin→COROS 연동 클래스
gui.py              # GUI (ttkbootstrap 기반)
main.py             # CLI 진입점
README.md           # 설명서
exports/
  coros/            # COROS FIT 파일 저장/업로드용
  garmin/           # Garmin FIT 파일 저장/업로드용
```

## 설치 및 실행

1. **Python 3.9+** 필요 (tkinter, ttkbootstrap, garminconnect 등)
2. `config.py.example`을 복사해 `config.py` 작성 (계정정보 등 입력)
3. 패키지 설치:
   ```bash
   pip install -r requirements.txt
   # 또는
   pip install ttkbootstrap garminconnect
   ```
4. **GUI 실행:**
   ```bash
   python gui.py
   ```
5. **CLI 실행:**
   ```bash
   python main.py --help
   ```

#### macOS에서 GUI 오류시

- python.org 공식 Python 권장 (Homebrew python은 tkinter 미포함)
- `python3 -m pip install ttkbootstrap` 등으로 패키지 설치
- 환경변수 `TK_SILENCE_DEPRECATION=1` 필요시 추가


## CLI 사용 예시

```bash
# COROS→Garmin, 2024년 6월 1일 활동만 다운로드+업로드
python main.py --mode coros2garmin --day 20240601

# Garmin→COROS, 2024년 6월 전체 활동 업로드만
python main.py --mode garmin2coros --month 202406 --upload-only

# 특정 FIT 파일만 업로드
python main.py --mode coros2garmin --file exports/coros/20240601_123456.fit --upload-only
```

## GUI 주요 기능

- **모드 선택:** COROS→Garmin, Garmin→COROS
- **범위 선택:** 날짜/월/전체/특정 파일
- **실행 모드:** 다운로드만/업로드만/다운로드+업로드
- **날짜 선택:** ttkbootstrap의 DateEntry (달력)
- **월 선택:** Combobox로 연월(YYYYMM) 선택
- **파일 선택:** 파일 다중 선택 가능
- **로그:** 진행상황/에러 실시간 표시
- **비동기:** 스레드 처리로 UI 멈춤 없음
- **다운로드/업로드 분리:** 각 모드별로 별도 실행 (다운로드만, 업로드만, 다운로드+업로드)
- **날짜 선택 안정화:** DateEntry 값이 항상 selected_date와 동기화, 내부적으로 %Y%m%d로 변환하여 백엔드에 전달

## 파일명 규칙

- 모든 다운로드 FIT 파일은 `YYYYMMDD_activityId.fit` 형식 (Garmin도 동일)

## 기타 참고

- `config.py`에 계정정보 등 필수 입력
- `exports/coros`, `exports/garmin` 폴더 자동 생성
- Windows/macOS 모두 동작 확인
- ttkbootstrap 기반 GUI로 별도 tkcalendar 불필요

## 변경 이력

- 2024-07: 구조 대개편, CLI/GUI 통합, 파일명 규칙 통일, DateEntry 안정화, garminconnect 최신화 등
  - 다운로드/업로드 분리, DateEntry 값 동기화, 파일명 규칙 통일, GUI/CLI 옵션 일치 등 최신 구조 반영

## GUI 사용법 (ttkbootstrap 기반)

- GUI 실행:
    ```bash
    python gui.py
    ```
- **실행 전**
    - `pip install ttkbootstrap` 필요 (최초 1회)
    - macOS에서 tkinter/tcl/tk 최신 버전 권장
- **기능**
    - 날짜/월/전체/특정 파일/업로드만/다운로드+업로드 모두 지원
    - 날짜 선택은 modern 달력(DateEntry) 위젯 사용, macOS에서도 안정적
    - 파일명: COROS/가민 모두 `YYYYMMDD_activityId.fit` 형식으로 저장
    - 로그/진행상황 실시간 표시

## 실행 파일(배포용) 만들기

- PyInstaller로 단일 실행 파일(EXE, macOS app 등) 생성 가능
- spec 파일 예시: `pyinstaller.spec` 제공
- 빌드 명령:
  ```bash
  pip install pyinstaller
  pyinstaller pyinstaller.spec
  ```
- 빌드 후 `dist/coros_garmin_gui`(또는 .exe) 실행
- **경로 처리:**
  - 코드에서 파일/폴더 접근 시 반드시 아래 함수로 경로 처리:
    ```python
    import os, sys
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, relative_path)
    # 예시: OUTPUT_DIR = resource_path('exports')
    ```
  - config.py, exports/ 등은 실행파일과 같은 폴더에 두는 것을 권장
- macOS: app 번들로 만들려면 py2app 등도 활용 가능
- 빌드 후 첫 실행은 느릴 수 있음(압축 해제 때문)
- 자세한 옵션은 PyInstaller 공식문서 참고

---

문의: [nightace7@live.co.kr]