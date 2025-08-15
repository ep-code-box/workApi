import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap.widgets import DateEntry
import threading
import os
import sys
from datetime import datetime, timedelta
import ttkbootstrap as tb

# Refactored imports
from utils import resource_path, load_config
from coros_to_garmin import CorosToGarmin
from garmin_to_coros import GarminToCoros

LOG_FILENAME = "activity_sync.log"

class Logger:
    """stdout/stderr를 tkinter 위젯과 로그 파일 모두에 리디렉션하는 클래스"""
    def __init__(self, widget, log_file, tag="stdout"):
        self.widget = widget
        self.log_file = log_file
        self.tag = tag

    def write(self, msg):
        if self.widget and self.widget.root.winfo_exists():
            self.widget.root.after(0, self.widget.append_log, msg, self.tag)
        if self.log_file:
            self.log_file.write(msg)

    def flush(self):
        if self.log_file:
            self.log_file.flush()

class ConfigDialog(tk.Toplevel):
    def __init__(self, master, config_path):
        super().__init__(master)
        self.title("설정 (config.py)")
        self.config_path = config_path
        self.resizable(False, False)
        
        self.coros_email = tk.StringVar()
        self.coros_password = tk.StringVar()
        self.garmin_username = tk.StringVar()
        self.garmin_password = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        self._load_config_to_ui()
        self._create_widgets()

    def _load_config_to_ui(self):
        config = load_config(self.config_path)
        self.coros_email.set(config.get('COROS_EMAIL', ''))
        self.coros_password.set(config.get('COROS_PASSWORD', ''))
        self.garmin_username.set(config.get('GARMIN_USERNAME', ''))
        self.garmin_password.set(config.get('GARMIN_PASSWORD', ''))
        self.output_dir.set(config.get('OUTPUT_DIR', './exports'))

    def _create_widgets(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="COROS 이메일:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frm, textvariable=self.coros_email, width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frm, text="COROS 비밀번호:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frm, textvariable=self.coros_password, show="*", width=40).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frm, text="Garmin 이메일:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frm, textvariable=self.garmin_username, width=40).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(frm, text="Garmin 비밀번호:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frm, textvariable=self.garmin_password, show="*", width=40).grid(row=3, column=1, padx=5, pady=5)
        ttk.Label(frm, text="출력 폴더:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frm, textvariable=self.output_dir, width=40).grid(row=4, column=1, padx=5, pady=5)
        
        btn_frm = ttk.Frame(frm)
        btn_frm.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frm, text="저장", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frm, text="닫기", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def save_config(self):
        content = f"""
COROS_EMAIL = "{self.coros_email.get()}"
COROS_PASSWORD = "{self.coros_password.get()}"
GARMIN_USERNAME = "{self.garmin_username.get()}"
GARMIN_PASSWORD = "{self.garmin_password.get()}"
OUTPUT_DIR = "{self.output_dir.get()}"
"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(content.strip())
            messagebox.showinfo("저장 완료", "설정이 저장되었습니다.", parent=self)
        except Exception as e:
            messagebox.showerror("저장 실패", f"설정 파일 저장 중 오류가 발생했습니다:\n{e}", parent=self)

class SyncGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("COROS ↔ Garmin 연동")
        self.root.resizable(True, True)

        self.mode = tk.StringVar(value="coros2garmin")
        self.action_mode = tk.StringVar(value="both")
        self.date_type = tk.StringVar(value="day")
        self.selected_month = tk.StringVar()
        self.file_list = []

        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")
        if not os.path.exists(self.config_path):
            messagebox.showinfo("설정 필요", "최초 실행 시 [설정] 버튼을 눌러 계정 정보를 입력하세요.")

        self.create_widgets()

    def create_widgets(self):
        self.frm = ttk.Frame(self.root, padding=10)
        self.frm.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(self.frm, text="COROS ↔ Garmin Activity Sync", font=("Segoe UI", 14, "bold"), anchor="center")
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky="ew")
        ttk.Button(self.frm, text="설정", bootstyle="info-outline", command=self.open_config_dialog).grid(row=0, column=3, sticky="e")

        ttk.Separator(self.frm, orient="horizontal").grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)

        dir_frame = ttk.LabelFrame(self.frm, text="방향", padding=5)
        dir_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=5)
        ttk.Radiobutton(dir_frame, text="COROS → Garmin", variable=self.mode, value="coros2garmin").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(dir_frame, text="Garmin → COROS", variable=self.mode, value="garmin2coros").pack(side=tk.LEFT, padx=5)

        action_frame = ttk.LabelFrame(self.frm, text="실행 모드", padding=5)
        action_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=5)
        ttk.Radiobutton(action_frame, text="다운로드 + 업로드", variable=self.action_mode, value="both", command=self.update_ui_visibility).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(action_frame, text="다운로드만", variable=self.action_mode, value="download", command=self.update_ui_visibility).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(action_frame, text="업로드만", variable=self.action_mode, value="upload", command=self.update_ui_visibility).pack(side=tk.LEFT, padx=5)

        self.scope_frame = ttk.LabelFrame(self.frm, text="연동 범위", padding=5)
        self.scope_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=5)
        
        self.day_radio = ttk.Radiobutton(self.scope_frame, text="날짜", variable=self.date_type, value="day", command=self.update_date_widgets)
        self.day_radio.grid(row=0, column=0, sticky='w')
        self.date_entry = DateEntry(self.scope_frame, width=12, bootstyle="info", dateformat="%Y-%m-%d")
        self.date_entry.grid(row=0, column=1)
        # Set yesterday's date as the default
        self.date_entry.entry.delete(0, tk.END)
        self.date_entry.entry.insert(0, (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))

        self.month_radio = ttk.Radiobutton(self.scope_frame, text="월", variable=self.date_type, value="month", command=self.update_date_widgets)
        self.month_radio.grid(row=1, column=0, sticky='w')
        self.month_entry = ttk.Combobox(self.scope_frame, width=10, textvariable=self.selected_month, values=self.get_month_list())
        self.month_entry.grid(row=1, column=1)
        self.month_entry.set(datetime.now().strftime("%Y%m")) # Default to current month

        self.all_radio = ttk.Radiobutton(self.scope_frame, text="전체", variable=self.date_type, value="all", command=self.update_date_widgets)
        self.all_radio.grid(row=2, column=0, sticky='w')
        
        self.file_picker_frame = ttk.LabelFrame(self.frm, text="파일 선택", padding=5)
        self.file_picker_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=5)
        self.file_btn = ttk.Button(self.file_picker_frame, text="FIT 파일 선택", command=self.select_files)
        self.file_btn.pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(self.file_picker_frame, text="(선택 안함)")
        self.file_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(self.frm, text="실행", bootstyle="success", command=self.run_action).grid(row=7, column=0, columnspan=4, sticky="ew", pady=10)

        log_frame = ttk.LabelFrame(self.frm, text="로그", padding=5)
        log_frame.grid(row=8, column=0, columnspan=4, sticky="nsew")
        self.frm.grid_rowconfigure(8, weight=1)
        self.frm.grid_columnconfigure(0, weight=1)

        self.log_box = tk.Text(log_frame, height=15, state="disabled", wrap=tk.WORD, font=("Consolas", 9))
        self.log_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_box.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.log_box.config(yscrollcommand=scrollbar.set)

        self.log_box.tag_config("stdout", foreground="#333")
        self.log_box.tag_config("stderr", foreground="#d35400", font=("Consolas", 9, "bold"))
        self.log_box.tag_config("info", foreground="#2980b9", font=("Segoe UI", 10, "bold"))

        self.update_ui_visibility()
        self.update_date_widgets()

    def update_ui_visibility(self):
        if self.action_mode.get() == "upload":
            self.scope_frame.grid_remove()
            self.file_picker_frame.grid()
        else:
            self.scope_frame.grid()
            self.file_picker_frame.grid_remove()

    def update_date_widgets(self):
        self.date_entry.entry.config(state="normal" if self.date_type.get() == "day" else "disabled")
        self.month_entry.config(state="normal" if self.date_type.get() == "month" else "disabled")

    def get_month_list(self):
        now = datetime.now()
        return [f"{y}{m:02d}" for y in range(now.year, now.year - 5, -1) for m in range(12, 0, -1)]

    def select_files(self):
        files = filedialog.askopenfilenames(title="업로드할 FIT 파일 선택", filetypes=[("FIT files", "*.fit")])
        if files:
            self.file_list = list(files)
            self.file_label.config(text=f"{len(files)}개 파일 선택됨")
        else:
            self.file_list = []
            self.file_label.config(text="(선택 안함)")

    def append_log(self, msg, tag="stdout"):
        msg = msg.strip()
        if not msg: return
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, msg + "\n", tag)
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    def run_action(self):
        self.log_box.config(state="normal")
        self.log_box.delete(1.0, tk.END)
        self.log_box.config(state="disabled")

        args = self.build_args()
        if not args: return

        target_migrator = CorosToGarmin() if args.mode == 'coros2garmin' else GarminToCoros()
        
        try:
            log_file = open(LOG_FILENAME, "w", encoding="utf-8", buffering=1)
        except IOError as e:
            messagebox.showerror("오류", f"로그 파일을 열 수 없습니다: {e}")
            return

        stdout_logger = Logger(self, log_file, "stdout")
        stderr_logger = Logger(self, log_file, "stderr")
        
        self.append_log(f"======= 실행 시작 (로그 파일: {LOG_FILENAME}) =======", "info")

        def migration_task():
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = stdout_logger
            sys.stderr = stderr_logger
            try:
                target_migrator.run(args)
                self.append_log("======= 작업 완료 =======", "info")
            except Exception as e:
                print(f"치명적인 오류 발생: {e}")
                self.append_log("======= 작업 중단 =======", "info")
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                log_file.close()

        threading.Thread(target=migration_task, daemon=True).start()

    def build_args(self):
        class Args: pass
        args = Args()
        args.mode = self.mode.get()
        
        action_mode = self.action_mode.get()
        args.download_only = (action_mode == 'download')
        args.upload_only = (action_mode == 'upload')

        if args.upload_only:
            if not self.file_list:
                messagebox.showerror("오류", "업로드할 파일을 선택하세요.")
                return None
            args.file = self.file_list
            args.day = args.month = args.all = None
        else:
            date_type = self.date_type.get()
            args.file = None
            args.day = None
            args.month = None
            args.all = False

            if date_type == 'day':
                try:
                    # Get the raw string from the entry and parse it
                    date_str = self.date_entry.entry.get()
                    datetime.strptime(date_str, "%Y-%m-%d") # Validate format
                    args.day = date_str.replace("-", "")
                except (AttributeError, ValueError):
                    messagebox.showerror("오류", "날짜 형식이 잘못되었습니다 (YYYY-MM-DD).")
                    return None
            elif date_type == 'month':
                args.month = self.month_entry.get()
                if not args.month:
                    messagebox.showerror("오류", "월을 선택하세요.")
                    return None
            elif date_type == 'all':
                args.all = True
            
        return args

    def open_config_dialog(self):
        ConfigDialog(self.root, self.config_path)

if __name__ == "__main__":
    root = tb.Window(themename="flatly")
    app = SyncGUI(root)
    root.mainloop()
