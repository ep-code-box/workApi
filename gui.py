import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap.widgets import DateEntry
from coros_to_garmin import CorosToGarmin
from garmin_to_coros import GarminToCoros
import threading
import os
import sys

# PyInstaller/로컬 환경 모두에서 동작하는 경로 반환 함수
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

class ConfigDialog(tk.Toplevel):
    def __init__(self, master, config_path):
        super().__init__(master)
        self.title("설정 (config.py)")
        self.config_path = config_path
        self.resizable(False, False)
        # 필드
        self.coros_email = tk.StringVar()
        self.coros_password = tk.StringVar()
        self.garmin_username = tk.StringVar()
        self.garmin_password = tk.StringVar()
        self.output_dir = tk.StringVar()
        self._load_config()
        # UI
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="COROS 이메일:").grid(row=0, column=0, sticky="e"); ttk.Entry(frm, textvariable=self.coros_email, width=30).grid(row=0, column=1)
        ttk.Label(frm, text="COROS 비밀번호:").grid(row=1, column=0, sticky="e"); ttk.Entry(frm, textvariable=self.coros_password, show="*", width=30).grid(row=1, column=1)
        ttk.Label(frm, text="Garmin 이메일:").grid(row=2, column=0, sticky="e"); ttk.Entry(frm, textvariable=self.garmin_username, width=30).grid(row=2, column=1)
        ttk.Label(frm, text="Garmin 비밀번호:").grid(row=3, column=0, sticky="e"); ttk.Entry(frm, textvariable=self.garmin_password, show="*", width=30).grid(row=3, column=1)
        ttk.Label(frm, text="출력 폴더:").grid(row=4, column=0, sticky="e"); ttk.Entry(frm, textvariable=self.output_dir, width=30).grid(row=4, column=1)
        ttk.Button(frm, text="저장", command=self.save).grid(row=5, column=0, pady=10)
        ttk.Button(frm, text="닫기", command=self.destroy).grid(row=5, column=1, pady=10)
    def _load_config(self):
        import re
        # config.py가 없으면 기본값으로 초기화
        if not os.path.exists(self.config_path):
            self.coros_email.set("")
            self.coros_password.set("")
            self.garmin_username.set("")
            self.garmin_password.set("")
            self.output_dir.set("./exports")
            return
        with open(self.config_path, encoding="utf-8") as f:
            text = f.read()
        def get_val(key):
            m = re.search(rf'{key}\s*=\s*["\"](.*?)["\"]', text)
            return m.group(1) if m else ""
        def get_val_dir(key):
            m = re.search(rf'{key}\s*=\s*["\']?(.*?)["\']?$', text, re.MULTILINE)
            return m.group(1) if m else ""
        self.coros_email.set(get_val('COROS_EMAIL'))
        self.coros_password.set(get_val('COROS_PASSWORD'))
        self.garmin_username.set(get_val('GARMIN_USERNAME'))
        self.garmin_password.set(get_val('GARMIN_PASSWORD'))
        self.output_dir.set(get_val_dir('OUTPUT_DIR'))
    def save(self):
        # config.py가 이미 있으면 함수 부분은 유지, 계정 정보만 갱신
        func_code = ""
        if os.path.exists(self.config_path):
            with open(self.config_path, encoding="utf-8") as f:
                text = f.read()
            import re
            m = re.search(r'(def load_config\s*\(.*?\):[\s\S]*)', text)
            if m:
                func_code = '\n' + m.group(1)
        if not func_code:
            # load_config 함수가 없으면 기본 함수 추가
            func_code = '''\ndef load_config(config_path="config.py"):\n    import re, os\n    config = {{}}\n    if not os.path.exists(config_path):\n        return config\n    with open(config_path, encoding="utf-8") as f:\n        text = f.read()\n    def get_val(key):\n        m = re.search(rf'{key}\\s*=\\s*[\"\\\"](.*?)[\"\\\"]', text)\n        return m.group(1) if m else ""\n    def get_val_dir(key):\n        m = re.search(rf'{key}\\s*=\\s*[\"\\']?(.*?)[\"\\']?$', text, re.MULTILINE)\n        return m.group(1) if m else ""\n    config['COROS_EMAIL'] = get_val('COROS_EMAIL')\n    config['COROS_PASSWORD'] = get_val('COROS_PASSWORD')\n    config['GARMIN_USERNAME'] = get_val('GARMIN_USERNAME')\n    config['GARMIN_PASSWORD'] = get_val('GARMIN_PASSWORD')\n    config['OUTPUT_DIR'] = get_val_dir('OUTPUT_DIR')\n    return config\n'''
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write(f'COROS_EMAIL     = "{self.coros_email.get()}"\n')
            f.write(f'COROS_PASSWORD  = "{self.coros_password.get()}"\n')
            f.write(f'GARMIN_USERNAME = "{self.garmin_username.get()}"\n')
            f.write(f'GARMIN_PASSWORD = "{self.garmin_password.get()}"\n')
            f.write(f'OUTPUT_DIR = "{self.output_dir.get()}"\n')
            f.write(func_code)
        tk.messagebox.showinfo("저장 완료", "설정이 저장되었습니다.")

class SyncGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("COROS ↔ Garmin 연동")
        # 창 크기 고정 해제 및 최소/최대 크기 제한 해제 (원복)
        self.root.resizable(True, True)
        # self.root.update_idletasks()
        # self.root.minsize(self.root.winfo_width(), self.root.winfo_height())
        # self.root.maxsize(self.root.winfo_width(), self.root.winfo_height())
        self.mode = tk.StringVar(value="coros2garmin")
        self.date_type = tk.StringVar(value="day")
        self.selected_date = tk.StringVar()
        self.selected_month = tk.StringVar()
        self.file_list = []
        self.log_text = tk.StringVar()
        self.action_mode = tk.StringVar(value="download")
        self.config_path = resource_path("config.py")
        if not os.path.exists(self.config_path):
            tk.messagebox.showinfo("설정 필요", "최초 실행 시 [설정(config)] 버튼을 눌러 계정 정보를 입력하세요.")
        self.create_widgets()

    def create_widgets(self):
        self.frm = ttk.Frame(self.root, padding=8)  # 패딩 더 줄임
        self.frm.pack(fill=tk.BOTH, expand=True)
        frm = self.frm

        # 타이틀 (중앙 정렬)
        title = ttk.Label(frm, text="COROS ↔ Garmin Activity Sync", font=("Segoe UI", 13, "bold"), foreground="#2c3e50", anchor="center", justify="center")
        title.grid(row=0, column=0, columnspan=4, pady=(0, 5), sticky="ew")
        frm.grid_columnconfigure(0, weight=1)
        frm.grid_columnconfigure(1, weight=1)
        frm.grid_columnconfigure(2, weight=1)
        frm.grid_columnconfigure(3, weight=1)
        # 구분선
        ttk.Separator(frm, orient="horizontal").grid(row=1, column=0, columnspan=5, sticky="ew", pady=2)

        # 모드 선택
        ttk.Label(frm, text="모드 선택:", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky="e", pady=2)
        ttk.Radiobutton(frm, text="COROS → Garmin", variable=self.mode, value="coros2garmin").grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(frm, text="Garmin → COROS", variable=self.mode, value="garmin2coros").grid(row=2, column=2, sticky="w")

        # 실행 모드 선택 (모드선택 바로 아래)
        ttk.Label(frm, text="실행 모드:", font=("Segoe UI", 11, "bold")).grid(row=3, column=0, sticky="e", pady=2)
        ttk.Radiobutton(frm, text="다운로드만", variable=self.action_mode, value="download", command=self.update_file_picker_visibility).grid(row=3, column=1, sticky="w")
        ttk.Radiobutton(frm, text="업로드만", variable=self.action_mode, value="upload", command=self.update_file_picker_visibility).grid(row=3, column=2, sticky="w")
        ttk.Radiobutton(frm, text="다운로드+업로드", variable=self.action_mode, value="both", command=self.update_file_picker_visibility).grid(row=3, column=3, sticky="w")

        # 날짜/월/전체 선택 (세로 배치, 아래로 한 칸 이동)
        self.range_label = ttk.Label(frm, text="연동 범위:", font=("Segoe UI", 11, "bold"))
        self.date_type_frame = ttk.Frame(frm)
        self.range_label.grid(row=4, column=0, sticky="ne", pady=2)
        self.date_type_frame.grid(row=4, column=1, rowspan=3, sticky="w", pady=2)
        self.day_radio = ttk.Radiobutton(self.date_type_frame, text="날짜", variable=self.date_type, value="day", command=self.update_date_widgets)
        self.month_radio = ttk.Radiobutton(self.date_type_frame, text="월", variable=self.date_type, value="month", command=self.update_date_widgets)
        self.all_radio = ttk.Radiobutton(self.date_type_frame, text="전체", variable=self.date_type, value="all", command=self.update_date_widgets)
        self.day_radio.pack(anchor="w")
        self.month_radio.pack(anchor="w")
        self.all_radio.pack(anchor="w")
        # 날짜 선택 위젯 위치 조정
        # import locale
        from datetime import datetime, timedelta
        # # 시스템 로케일을 한국(ko_KR.UTF-8)로 고정
        # try:
        #     locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
        # except locale.Error:
        #     pass  # 시스템에 한글 로케일이 없으면 무시
        # 기본값: 빈 값, placeholder: 어제 날짜 (dd/mm/yyyy)
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%x")
        self.date_entry = DateEntry(frm, width=10, bootstyle="info")  # locale 옵션 제거, 시스템 locale만 적용
        self.date_entry.grid(row=5, column=2, columnspan=2, sticky="ew", pady=1)  # 항상 배치
        self.date_entry.entry.delete(0, 'end')
        self.date_entry.entry.config(foreground="#888")
        self.date_entry.entry.insert(0, yesterday)  # 힌트처럼 어제 날짜 표시 (dd/mm/yyyy)
        # 힌트 라벨 추가 (예: 03/07/2025)
        # self.date_hint_label = ttk.Label(frm, text="예: 03/07/2025 (dd/mm/yyyy)", font=("Segoe UI", 8), foreground="#888")
        # self.date_hint_label.grid(row=6, column=2, columnspan=2, sticky="w", pady=(0,2))
        def on_focus_in(event=None):
            pass
        def on_focus_out(event=None):
            # 항상 date 객체로 받아서 string으로 변환
            try:
                val = self.date_entry.get_date()
            except Exception:
                val = self.date_entry.entry.get()
            self.selected_date.set(val)
        def on_date_selected(event=None):
            # 달력에서 날짜를 선택하면 yyyy-mm-dd로 entry에 넣고 색상도 검정색
            try:
                val = self.date_entry.get_date()
            except Exception:
                val = self.date_entry.entry.get()
            self.date_entry.entry.delete(0, 'end')
            self.date_entry.entry.insert(0, val)
            self.date_entry.entry.config(foreground="#222")
            self.selected_date.set(val)
        self.date_entry.entry.bind('<FocusIn>', on_focus_in)
        self.date_entry.entry.bind('<FocusOut>', on_focus_out)
        self.date_entry.entry.bind('<Return>', on_focus_out)
        self.date_entry.entry.bind('<Tab>', on_focus_out)
        self.date_entry.entry.bind('<Button-1>', on_focus_out)
        self.date_entry.bind('<<DateEntrySelected>>', on_date_selected)
        self.month_entry = ttk.Combobox(frm, width=5, textvariable=self.selected_month, values=self.get_month_list())  # width 더 축소
        self.month_entry.grid(row=5, column=2, columnspan=2, sticky="ew", pady=1)
        self.update_date_widgets()

        # 파일 선택 (업로드만 모드에서만 표시)
        self.file_btn = ttk.Button(frm, text="FIT 파일 선택", bootstyle="secondary-outline", width=10, command=self.select_files)  # width 더 축소
        self.file_label = ttk.Label(frm, text="(선택 안함)", foreground="#888")
        self.update_file_picker_visibility()

        # 실행 버튼 (가로 전체, 세로는 여유)
        ttk.Button(frm, text="실행", bootstyle="success", width=1, command=self.run_action).grid(row=7, column=0, columnspan=4, sticky="ew", pady=10, padx=2)
        # 상단에 [설정] 버튼 (오른쪽 상단, 가로폭 더 축소)
        ttk.Button(frm, text="설정", bootstyle="info-outline", width=4, command=self.open_config_dialog).grid(row=0, column=3, padx=2, sticky="e")

        # 로그 출력 (더 넓고, 폰트/배경 강조)
        log_frame = ttk.Frame(frm, borderwidth=1, relief="solid")
        log_frame.grid(row=8, column=0, columnspan=5, pady=(4, 0), sticky="ew")
        self.log_box = tk.Text(log_frame, height=7, width=48, state="disabled", font=("Consolas", 9), bg="#f8f9fa", fg="#222")  # 크기 더 축소
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

    def append_log(self, msg, tag=None):
        self.log_box.config(state="normal")
        if tag == "error":
            self.log_box.insert(tk.END, msg + "\n", "error")
        elif tag == "success":
            self.log_box.insert(tk.END, msg + "\n", "success")
        else:
            self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")
        # 스타일 태그
        self.log_box.tag_config("error", foreground="#c0392b", font=("Consolas", 11, "bold"))
        self.log_box.tag_config("success", foreground="#27ae60", font=("Consolas", 11, "bold"))

    def update_date_widgets(self):
        if self.date_type.get() == "day":
            self.date_entry.grid()
            # self.date_hint_label.grid()
            self.month_entry.grid_remove()
        elif self.date_type.get() == "month":
            self.date_entry.grid_remove()
            # self.date_hint_label.grid_remove()
            self.month_entry.grid()
        else:
            self.date_entry.grid_remove()
            # self.date_hint_label.grid_remove()
            self.month_entry.grid_remove()

    def get_month_list(self):
        from datetime import datetime
        now = datetime.now()
        months = [f"{y}{m:02d}" for y in range(now.year-5, now.year+1) for m in range(1,13)]
        return months[::-1]  # 최신월이 위로

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("FIT files", "*.fit")])
        if files:
            self.file_list = list(files)
            self.file_label.config(text=f"{len(files)}개 파일 선택됨")
        else:
            self.file_list = []
            self.file_label.config(text="(선택 안함)")

    def run_action(self):
        mode = self.action_mode.get()
        self.log_box.config(state="normal"); self.log_box.delete(1.0, tk.END); self.log_box.config(state="disabled")
        if mode == "download":
            args = self.build_args(download_only=True)
            args.download_only = True
            self.append_log("[다운로드 시작]", tag="success")
            threading.Thread(target=self._run_download, args=(args,)).start()
        elif mode == "upload":
            args = self.build_args(upload_only=True)
            args.upload_only = True
            self.append_log("[업로드 시작]", tag="success")
            threading.Thread(target=self._run_upload, args=(args,)).start()
        else:  # both
            args = self.build_args()
            self.append_log("[다운로드+업로드 시작]", tag="success")
            threading.Thread(target=self._run_both, args=(args,)).start()

    def _run_download(self, args):
        self.append_log("[다운로드 진행 중...]")
        try:
            if args.mode == "coros2garmin":
                CorosToGarmin().run(args)
            else:
                GarminToCoros().run(args)
            self.append_log("[다운로드 완료]", tag="success")
        except Exception as e:
            self.append_log(f"[다운로드 오류] {e}", tag="error")

    def _run_upload(self, args):
        self.append_log("[업로드 진행 중...]")
        args.upload_only = True
        try:
            if args.mode == "coros2garmin":
                CorosToGarmin().run(args)
            else:
                GarminToCoros().run(args)
            self.append_log("[업로드 완료]", tag="success")
        except Exception as e:
            self.append_log(f"[업로드 오류] {e}", tag="error")

    def _run_both(self, args):
        self.append_log("[다운로드+업로드 진행 중...]")
        try:
            if args.mode == "coros2garmin":
                CorosToGarmin().run(args)
                self.append_log("[COROS→Garmin 완료]", tag="success")
            elif args.mode == "garmin2coros":
                GarminToCoros().run(args)
                self.append_log("[Garmin→COROS 완료]", tag="success")
            self.append_log("[다운로드+업로드 전체 완료]", tag="success")
        except Exception as e:
            self.append_log(f"[다운로드+업로드 오류] {e}", tag="error")

    def build_args(self, download_only=False, upload_only=False):
        class Args: pass
        args = Args()
        args.mode = self.mode.get()
        args.day = None
        args.month = None
        args.all = False
        args.upload_only = upload_only
        args.file = self.file_list if self.file_list else None
        if self.date_type.get() == "day":
            try:
                date_obj = self.date_entry.get_date()
                args.day = date_obj.strftime("%Y%m%d")
            except Exception:
                raw = self.selected_date.get()
                args.day = str(raw).replace("-", "").replace("/", "")  # fallback: 항상 문자열 yyyymmdd
        elif self.date_type.get() == "month":
            args.month = self.month_entry.get()
        elif self.date_type.get() == "all":
            args.all = True
        return args

    def on_dateentry_click(self, event):
        # DateEntry 팝업이 너무 빨리 닫히는 현상 방지용
        try:
            self.date_entry.after(100, lambda: self.date_entry.event_generate('<Down>'))
        except Exception:
            pass

    def open_config_dialog(self):
        ConfigDialog(self.root, self.config_path)

    def update_file_picker_visibility(self):
        # 업로드만 모드에서만 파일 선택 버튼/라벨 표시, 그 외에는 연동범위 표시
        if self.action_mode.get() == "upload":
            self.file_btn.grid(row=4, column=1, sticky="w", pady=2)
            self.file_label.grid(row=4, column=2, columnspan=2, sticky="w")
            self.range_label.grid_remove()
            self.date_type_frame.grid_remove()
            self.date_entry.grid_remove()
            self.month_entry.grid_remove()
            # 빈 공간을 채워 세로폭 유지
            # spacer를 실행 버튼과 동일한 row(7)에 grid하여 버튼 위치를 항상 고정
            if not hasattr(self, '_spacer_row6'):
                self._spacer_row6 = ttk.Frame(self.frm, height=1)
            self.frm.grid_rowconfigure(6, minsize=0)
            self._spacer_row6.grid(row=6, column=0, columnspan=4)
        else:
            self.file_btn.grid_remove()
            self.file_label.grid_remove()
            self.range_label.grid(row=4, column=0, sticky="ne", pady=2)
            self.date_type_frame.grid(row=4, column=1, rowspan=3, sticky="w", pady=2)
            self.update_date_widgets()
            # spacer 제거
            if hasattr(self, '_spacer_row6'):
                self._spacer_row6.grid_remove()

if __name__ == "__main__":
    import ttkbootstrap as tb
    root = tb.Window(themename="flatly")  # modern theme
    root.resizable(False, False)  # 창 크기 조절 불가
    # 아이콘 설정
    try:
        icon_path = resource_path("icon.png")
        icon_img = tk.PhotoImage(file=icon_path)
        root.iconphoto(True, icon_img)
    except Exception as e:
        print("아이콘 로드 실패:", e)
    app = SyncGUI(root)
    root.mainloop()
