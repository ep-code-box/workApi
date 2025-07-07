# COROS ↔ Garmin Activity Migration

이 프로젝트는 COROS 계정과 Garmin Connect 계정 간 활동 데이터를 양방향으로 전송하는 Python 애플리케이션입니다.

## ✨ 주요 기능

- 🖥️ **CLI와 GUI 모두 지원** - 명령줄과 모던한 GUI(ttkbootstrap 기반) 인터페이스
- 🔄 **양방향 연동** - COROS→Garmin, Garmin→COROS 모두 지원
- 📅 **유연한 범위 선택** - 특정 날짜/월/전체/개별 파일 선택 가능
- ⚡ **모드 분리** - 다운로드만/업로드만/다운로드+업로드 선택 실행
- 📁 **체계적인 파일 관리** - `exports/coros`, `exports/garmin` 폴더로 자동 분류
- 🌍 **크로스 플랫폼** - Windows/macOS 모두 지원
- 📊 **실시간 로그** - 진행상황과 에러 메시지 실시간 표시
- 🏷️ **통일된 파일명** - `YYYYMMDD_activityId.fit` 형식으로 일관성 유지
- 🔧 **스마트 경로 처리** - 어디서 실행하든 config.py를 자동으로 찾아 로드

## 폴더 구조

```
config.py           # 환경설정 (계정정보 등)
config.py.example   # 예시 환경설정
coros_to_garmin.py  # COROS→Garmin 연동 클래스
garmin_to_coros.py  # Garmin→COROS 연동 클래스
gui.py              # GUI (ttkbootstrap/tkcalendar 기반)
main.py             # CLI 진입점
README.md           # 설명서
pyinstaller.spec    # 빌드 스펙(윈도우/기본)
pyinstaller_mac.spec# 빌드 스펙(macOS)
icon.png            # 대표 아이콘(윈도우: .ico, 맥: .icns 권장)
exports/
  coros/            # COROS FIT 파일 저장/업로드용
  garmin/           # Garmin FIT 파일 저장/업로드용
```

## 🚀 설치 및 실행

### 📋 사전 요구사항
- **Python 3.9 이상** (Python 3.13 권장)
- **tkinter** (Python 기본 포함, macOS는 별도 설치 필요할 수 있음)

### 📦 1단계: 프로젝트 다운로드
```bash
git clone <repository-url>
cd workApi
```

### ⚙️ 2단계: 패키지 설치
```bash
# requirements.txt를 이용한 설치 (권장)
pip install -r requirements.txt

# 또는 개별 설치
pip install ttkbootstrap tkcalendar garminconnect requests
```

### 🔧 3단계: 설정 파일 생성
```bash
# config.py.example을 복사하여 config.py 생성
cp config.py.example config.py

# config.py 파일을 편집하여 계정 정보 입력
# COROS_EMAIL = "your_coros_email@example.com"
# COROS_PASSWORD = "your_coros_password"
# GARMIN_USERNAME = "your_garmin_username"
# GARMIN_PASSWORD = "your_garmin_password"
```

> **💡 스마트 경로 처리**: 이 프로젝트는 어디서 실행하든 자동으로 config.py 파일을 찾습니다. PyInstaller로 빌드된 실행 파일이나 다른 디렉토리에서 실행해도 올바른 config.py를 로드합니다.

### 🖥️ 4단계: 실행

#### GUI 실행 (권장)
```bash
python gui.py
# 또는 macOS에서
python3 gui.py
```

#### CLI 실행
```bash
# 도움말 보기
python main.py --help

# 기본 사용법
python main.py --mode coros2garmin --day 20241201
```

#### macOS 설정 (tkinter 관련 문제 해결)

macOS에서 tkinter 관련 문제가 발생하는 경우, 제공된 자동 설치 스크립트를 사용하세요:

```bash
# 실행 권한 부여 후 자동 설치
chmod +x macTk.sh && ./macTk.sh
```

**스크립트 수행 작업:**
- Homebrew를 통한 Python 3.13 및 python-tk 설치
- Tcl/Tk 경로 환경변수 설정
- tkinter 설치 확인 및 테스트

**수동 설치 (필요시):**
- python.org 공식 Python 권장 (Homebrew python은 tkinter 미포함)
- 환경변수 `TK_SILENCE_DEPRECATION=1` 추가
- 아이콘은 .icns 권장

## 💻 CLI 사용 예시

### 기본 명령어 구조
```bash
python main.py --mode [coros2garmin|garmin2coros] [옵션]
```

### 📅 날짜별 동기화
```bash
# COROS → Garmin: 어제 활동 다운로드 + 업로드
python main.py --mode coros2garmin --day 20241201

# Garmin → COROS: 특정 날짜 활동 다운로드 + 업로드  
python main.py --mode garmin2coros --day 20241201

# 오늘 날짜로 자동 설정 (인자 없을 때)
python main.py --mode coros2garmin
```

### 📆 월별 동기화
```bash
# COROS → Garmin: 2024년 12월 전체 활동
python main.py --mode coros2garmin --month 202412

# Garmin → COROS: 2024년 11월 전체 활동
python main.py --mode garmin2coros --month 202411
```

### 🌍 전체 동기화
```bash
# COROS → Garmin: 모든 활동 데이터
python main.py --mode coros2garmin --all

# Garmin → COROS: 모든 활동 데이터 (주의: 시간이 오래 걸림)
python main.py --mode garmin2coros --all
```

### ⬆️ 업로드 전용 모드
```bash
# 이미 다운로드된 특정 파일만 업로드
python main.py --mode coros2garmin --upload-only --file exports/coros/20241201_123456.fit

# 여러 파일 동시 업로드
python main.py --mode coros2garmin --upload-only --file exports/coros/20241201_*.fit

# 폴더 내 모든 파일 업로드
python main.py --mode garmin2coros --upload-only --file exports/garmin/*.fit
```

### 🔧 고급 옵션
```bash
# 다운로드만 실행 (업로드 안함)
python main.py --mode coros2garmin --day 20241201 --download-only

# 특정 월의 데이터를 업로드만
python main.py --mode coros2garmin --month 202412 --upload-only
```

## 🖼️ GUI 주요 기능

### 🎛️ 인터페이스 구성
- **🔄 모드 선택** - COROS→Garmin, Garmin→COROS 라디오 버튼
- **📅 범위 선택** - 날짜/월/전체/특정 파일 탭 구성
- **⚡ 실행 모드** - 다운로드만/업로드만/다운로드+업로드 선택
- **📊 실시간 로그** - 진행상황과 에러 메시지 실시간 표시

### 🛠️ 고급 기능
- **📅 달력 위젯** - ttkbootstrap DateEntry로 직관적인 날짜 선택
- **📂 파일 브라우저** - 다중 파일 선택 및 드래그 앤 드롭 지원
- **🔄 비동기 처리** - 백그라운드 실행으로 UI 멈춤 없음
- **💾 설정 관리** - GUI에서 직접 계정 정보 입력 및 저장

### 📱 사용자 경험
- **🎨 모던 테마** - ttkbootstrap 기반 깔끔한 디자인
- **🔔 알림 시스템** - 작업 완료/오류 시 팝업 알림
- **📈 진행률 표시** - 프로그레스 바로 작업 진행도 확인

## 📁 파일명 규칙

모든 FIT 파일은 다음 형식으로 저장됩니다:
```
YYYYMMDD_activityId.fit
```

**예시:**
- `20241201_987654321.fit` - 2024년 12월 1일의 활동 ID 987654321
- `20241215_123456789.fit` - 2024년 12월 15일의 활동 ID 123456789

## 📦 빌드 및 배포 (실행 파일 만들기)

### 🛠️ PyInstaller 설치 및 빌드
```bash
# PyInstaller 설치
pip install pyinstaller

# Windows/Linux 빌드
pyinstaller pyinstaller.spec

# macOS 빌드  
pyinstaller pyinstaller_mac.spec
```

### 📂 빌드 결과물
빌드 완료 후 `dist/` 폴더에 실행 파일이 생성됩니다:
- **Windows**: `coros_garmin_gui.exe`
- **macOS**: `coros_garmin_gui.app`
- **Linux**: `coros_garmin_gui`

### 🎨 아이콘 설정
- **Windows**: `.ico` 파일 권장
- **macOS**: `.icns` 파일 권장  
- **Linux**: `.png` 파일 사용 가능

### ⚠️ 주의사항
- 첫 실행 시 압축 해제로 인해 시간이 걸릴 수 있습니다
- `config.py`는 스마트 경로 처리로 자동 탐지되므로 위치 걱정 없음
- `exports/` 폴더는 자동 생성됩니다
- 빌드 후 테스트를 통해 모든 기능이 정상 작동하는지 확인하세요

## 🔧 문제 해결

### 🔧 일반적인 문제 해결

#### 설정 관련
- **config.py 파일이 없음**: `cp config.py.example config.py`로 설정 파일 생성
- **로그인 실패**: config.py의 계정 정보 확인
- **config.py 못 찾는 오류**: 스마트 경로 처리로 자동 해결 (어디서 실행해도 OK)

#### 네트워크 및 업로드
- **파일 업로드 실패**: 네트워크 연결 및 API 제한 확인
- **연결 타임아웃**: 잠시 후 재시도

#### 플랫폼별 문제

**macOS:**
```bash
# tkinter 문제 (자동 해결)
chmod +x macTk.sh && ./macTk.sh

# 수동 해결
brew install python-tk
export TK_SILENCE_DEPRECATION=1
python3 --version  # 3.9 이상 필요
```

**Windows:**
```bash
# 패키지 설치 오류
pip install --upgrade pip setuptools wheel

# 실행 파일 디버깅 (pyinstaller.spec에서 console=True)
```

## 📞 지원 및 문의

- **이메일**: nightace7@live.co.kr
- **이슈 리포트**: GitHub Issues 활용
- **기능 요청**: Pull Request 환영

---

**⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!**