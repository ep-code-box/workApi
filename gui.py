import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap.widgets import DateEntry
from coros_to_garmin import CorosToGarmin
from garmin_to_coros import GarminToCoros
import threading

class SyncGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("COROS <-> Garmin 연동 GUI")
        self.mode = tk.StringVar(value="coros2garmin")
        self.date_type = tk.StringVar(value="day")
        self.selected_date = tk.StringVar()
        self.selected_month = tk.StringVar()
        self.file_list = []
        self.log_text = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        # 모드 선택
        ttk.Label(frm, text="모드 선택:").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(frm, text="COROS → Garmin", variable=self.mode, value="coros2garmin").grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(frm, text="Garmin → COROS", variable=self.mode, value="garmin2coros").grid(row=0, column=2, sticky="w")

        # 날짜/월/전체 선택
        ttk.Label(frm, text="연동 범위:").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(frm, text="날짜", variable=self.date_type, value="day", command=self.update_date_widgets).grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(frm, text="월", variable=self.date_type, value="month", command=self.update_date_widgets).grid(row=1, column=2, sticky="w")
        ttk.Radiobutton(frm, text="전체", variable=self.date_type, value="all", command=self.update_date_widgets).grid(row=1, column=3, sticky="w")

        # 날짜 선택 위젯 (ttkbootstrap DateEntry)
        self.date_entry = DateEntry(frm, width=12, bootstyle="info")
        self.date_entry.grid(row=2, column=1, sticky="w")
        # DateEntry는 get() 대신 entry.get() 사용, 날짜 선택 시 selected_date에 값 저장
        def update_selected_date(event=None):
            self.selected_date.set(self.date_entry.entry.get())
        self.date_entry.entry.bind('<FocusOut>', update_selected_date)
        self.date_entry.entry.bind('<Return>', update_selected_date)
        self.date_entry.entry.bind('<Tab>', update_selected_date)
        self.date_entry.entry.bind('<Button-1>', update_selected_date)
        # DateEntry 달력에서 날짜 선택 시에도 동기화
        self.date_entry.bind('<<DateEntrySelected>>', update_selected_date)
        # 월 선택 위젯
        self.month_entry = ttk.Combobox(frm, width=7, textvariable=self.selected_month, values=self.get_month_list())
        self.month_entry.grid(row=2, column=2, sticky="w")
        self.update_date_widgets()

        # 파일 선택
        ttk.Button(frm, text="특정 FIT 파일 선택", command=self.select_files).grid(row=3, column=0, sticky="w")
        self.file_label = ttk.Label(frm, text="(선택 안함)")
        self.file_label.grid(row=3, column=1, columnspan=3, sticky="w")

        # 실행 모드 선택
        self.action_mode = tk.StringVar(value="download")
        ttk.Label(frm, text="실행 모드:").grid(row=4, column=0, sticky="w")
        ttk.Radiobutton(frm, text="다운로드만", variable=self.action_mode, value="download").grid(row=4, column=1, sticky="w")
        ttk.Radiobutton(frm, text="업로드만", variable=self.action_mode, value="upload").grid(row=4, column=2, sticky="w")
        ttk.Radiobutton(frm, text="다운로드+업로드", variable=self.action_mode, value="both").grid(row=4, column=3, sticky="w")

        # 실행 버튼
        ttk.Button(frm, text="실행", command=self.run_action).grid(row=5, column=0, pady=10)
        # 로그 출력
        self.log_box = tk.Text(frm, height=12, width=70, state="disabled")
        self.log_box.grid(row=6, column=0, columnspan=4, pady=10)

    def update_date_widgets(self):
        if self.date_type.get() == "day":
            self.date_entry.grid()
            self.month_entry.grid_remove()
        elif self.date_type.get() == "month":
            self.date_entry.grid_remove()
            self.month_entry.grid()
        else:
            self.date_entry.grid_remove()
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
        if mode == "download":
            args = self.build_args(download_only=True)
            args.download_only = True
            self.log_box.config(state="normal"); self.log_box.delete(1.0, tk.END)
            self.log_box.insert(tk.END, "[다운로드 시작]\n"); self.log_box.config(state="disabled")
            threading.Thread(target=self._run_download, args=(args,)).start()
        elif mode == "upload":
            args = self.build_args(upload_only=True)
            args.upload_only = True
            self.log_box.config(state="normal"); self.log_box.delete(1.0, tk.END)
            self.log_box.insert(tk.END, "[업로드 시작]\n"); self.log_box.config(state="disabled")
            threading.Thread(target=self._run_upload, args=(args,)).start()
        else:  # both
            args = self.build_args()
            self.log_box.config(state="normal"); self.log_box.delete(1.0, tk.END)
            self.log_box.insert(tk.END, "[다운로드+업로드 시작]\n"); self.log_box.config(state="disabled")
            threading.Thread(target=self._run_both, args=(args,)).start()

    def _run_download(self, args):
        self.append_log("[다운로드 진행 중...]")
        if args.mode == "coros2garmin":
            CorosToGarmin().run(args)
        else:
            GarminToCoros().run(args)
        self.append_log("[다운로드 완료]")

    def _run_upload(self, args):
        self.append_log("[업로드 진행 중...]")
        # 업로드만 옵션 활성화
        args.upload_only = True
        if args.mode == "coros2garmin":
            CorosToGarmin().run(args)
        else:
            GarminToCoros().run(args)
        self.append_log("[업로드 완료]")

    def _run_both(self, args):
        self.append_log("[다운로드+업로드 진행 중...]")
        if args.mode == "coros2garmin":
            CorosToGarmin().run(args)
            GarminToCoros().run(args)
        else:
            GarminToCoros().run(args)
            CorosToGarmin().run(args)
        self.append_log("[다운로드+업로드 완료]")

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
            # DateEntry는 MM/DD/YYYY 형식이므로 변환 필요
            import datetime
            raw = self.selected_date.get()
            try:
                dt = datetime.datetime.strptime(raw, "%m/%d/%Y")
                args.day = dt.strftime("%Y%m%d")
            except Exception:
                args.day = raw.replace("-", "")  # fallback
        elif self.date_type.get() == "month":
            args.month = self.month_entry.get()
        elif self.date_type.get() == "all":
            args.all = True
        return args

    def append_log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    def on_dateentry_click(self, event):
        # DateEntry 팝업이 너무 빨리 닫히는 현상 방지용
        try:
            self.date_entry.after(100, lambda: self.date_entry.event_generate('<Down>'))
        except Exception:
            pass

if __name__ == "__main__":
    import ttkbootstrap as tb
    root = tb.Window(themename="flatly")  # modern theme
    app = SyncGUI(root)
    root.mainloop()
