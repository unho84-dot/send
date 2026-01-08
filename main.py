import asyncio
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from telethon import TelegramClient


RECIPIENT_LIMIT = 50
MESSAGE_ROWS = 6
SESSION_NAME = "send_session"


@dataclass
class MessageRow:
    message_entry: tk.Entry
    time_entry: tk.Entry
    send_button: tk.Button


class TelegramSenderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("보내기")
        self.root.geometry("980x620")

        self._build_ui()

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_api_section(left_frame)
        self._build_messages_section(left_frame)
        self._build_recipients_section(right_frame)

    def _build_api_section(self, parent: ttk.Frame) -> None:
        api_frame = ttk.LabelFrame(parent, text="계정 정보", padding=10)
        api_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(api_frame, text="api_id").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.api_id_entry = ttk.Entry(api_frame, width=30)
        self.api_id_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(api_frame, text="api_hash").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.api_hash_entry = ttk.Entry(api_frame, width=30)
        self.api_hash_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(api_frame, text="2FA PW").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.api_password_entry = ttk.Entry(api_frame, width=30, show="*")
        self.api_password_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(api_frame, text="※ 처음 실행 시 전화번호/인증코드 입력이 필요합니다.").grid(
            row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(6, 0)
        )

    def _build_messages_section(self, parent: ttk.Frame) -> None:
        messages_frame = ttk.LabelFrame(parent, text="메시지 및 발송 시간", padding=10)
        messages_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(messages_frame)
        header.pack(fill=tk.X)
        ttk.Label(header, text="전송메시지").grid(row=0, column=0, padx=5, sticky=tk.W)
        ttk.Label(header, text="전송시간").grid(row=0, column=1, padx=5, sticky=tk.W)

        self.message_rows: list[MessageRow] = []

        for index in range(MESSAGE_ROWS):
            row_frame = ttk.Frame(messages_frame)
            row_frame.pack(fill=tk.X, pady=4)

            message_entry = ttk.Entry(row_frame, width=40)
            message_entry.grid(row=0, column=0, padx=5, sticky=tk.W)

            time_entry = ttk.Entry(row_frame, width=20)
            time_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
            time_entry.insert(0, "YYYY-MM-DD HH:MM 또는 HH:MM")

            send_button = ttk.Button(
                row_frame,
                text="전송",
                command=lambda idx=index: self._handle_send(idx),
                width=10,
            )
            send_button.grid(row=0, column=2, padx=5)

            self.message_rows.append(
                MessageRow(message_entry=message_entry, time_entry=time_entry, send_button=send_button)
            )

        self.status_label = ttk.Label(messages_frame, text="대기 중", foreground="blue")
        self.status_label.pack(anchor=tk.W, pady=(10, 0))

    def _build_recipients_section(self, parent: ttk.Frame) -> None:
        recipients_frame = ttk.LabelFrame(parent, text="전송대상 (최대 50명)", padding=10)
        recipients_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(recipients_frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(recipients_frame, orient="vertical", command=canvas.yview)
        self.recipients_container = ttk.Frame(canvas)

        self.recipients_container.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=self.recipients_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.recipient_entries: list[tk.Entry] = []
        for index in range(RECIPIENT_LIMIT):
            row_frame = ttk.Frame(self.recipients_container)
            row_frame.pack(fill=tk.X, pady=2)

            ttk.Label(row_frame, text=f"{index + 1:02d}").pack(side=tk.LEFT, padx=(0, 6))
            entry = ttk.Entry(row_frame, width=30)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.recipient_entries.append(entry)

        help_text = ttk.Label(
            recipients_frame,
            text="※ 사용자 아이디(@username) 또는 전화번호(+8210...) 입력",
        )
        help_text.pack(anchor=tk.W, pady=(6, 0))

    def _handle_send(self, row_index: int) -> None:
        message = self.message_rows[row_index].message_entry.get().strip()
        time_text = self.message_rows[row_index].time_entry.get().strip()

        if not message:
            messagebox.showwarning("입력 필요", "메시지를 입력해주세요.")
            return

        recipients = [entry.get().strip() for entry in self.recipient_entries if entry.get().strip()]
        if not recipients:
            messagebox.showwarning("입력 필요", "전송대상을 최소 1명 입력해주세요.")
            return

        send_time = self._parse_send_time(time_text) if time_text else None
        if isinstance(send_time, str):
            messagebox.showerror("시간 형식 오류", send_time)
            return

        if send_time:
            delay = max((send_time - datetime.now()).total_seconds(), 0)
            self._update_status(f"{send_time:%Y-%m-%d %H:%M}에 예약되었습니다.")
            timer = threading.Timer(delay, lambda: self._start_send_thread(message, recipients))
            timer.daemon = True
            timer.start()
        else:
            self._start_send_thread(message, recipients)

    def _start_send_thread(self, message: str, recipients: list[str]) -> None:
        self._update_status("전송 중...")
        thread = threading.Thread(
            target=lambda: asyncio.run(self._send_message_async(message, recipients)),
            daemon=True,
        )
        thread.start()

    def _update_status(self, text: str) -> None:
        self.root.after(0, lambda: self.status_label.config(text=text))

    def _prompt_string(self, title: str, prompt: str, show: str | None = None) -> str | None:
        result: dict[str, str | None] = {"value": None}
        event = threading.Event()

        def ask() -> None:
            result["value"] = simpledialog.askstring(title, prompt, show=show)
            event.set()

        self.root.after(0, ask)
        event.wait()
        return result["value"]

    def _parse_send_time(self, time_text: str) -> datetime | None | str:
        if not time_text:
            return None

        time_text = time_text.replace("또는", "").strip()
        if not time_text:
            return None

        formats = ["%Y-%m-%d %H:%M", "%H:%M"]
        parsed_time = None
        for fmt in formats:
            try:
                parsed_time = datetime.strptime(time_text, fmt)
                break
            except ValueError:
                continue

        if parsed_time is None:
            return "시간 형식은 'YYYY-MM-DD HH:MM' 또는 'HH:MM'입니다."

        if parsed_time.year == 1900:
            now = datetime.now()
            parsed_time = parsed_time.replace(year=now.year, month=now.month, day=now.day)
            if parsed_time < now:
                parsed_time += timedelta(days=1)

        if parsed_time < datetime.now():
            return "예약 시간이 과거입니다. 미래 시간을 입력해주세요."

        return parsed_time

    async def _send_message_async(self, message: str, recipients: list[str]) -> None:
        api_id_text = self.api_id_entry.get().strip()
        api_hash = self.api_hash_entry.get().strip()
        password = self.api_password_entry.get().strip() or None

        if not api_id_text or not api_hash:
            self._update_status("api_id와 api_hash를 입력해주세요.")
            return

        try:
            api_id = int(api_id_text)
        except ValueError:
            self._update_status("api_id는 숫자여야 합니다.")
            return

        async with TelegramClient(SESSION_NAME, api_id, api_hash) as client:
            if not await client.is_user_authorized():
                phone = self._prompt_string("전화번호", "전화번호를 입력하세요 (+8210...):")
                if not phone:
                    self._update_status("전화번호 입력이 취소되었습니다.")
                    return

                await client.send_code_request(phone)
                code = self._prompt_string("인증 코드", "문자 또는 앱으로 받은 인증 코드를 입력하세요:")
                if not code:
                    self._update_status("인증 코드 입력이 취소되었습니다.")
                    return

                try:
                    await client.sign_in(phone=phone, code=code)
                except Exception:
                    if not password:
                        self._update_status("2FA 비밀번호가 필요합니다.")
                        return
                    await client.sign_in(password=password)

            success_count = 0
            for recipient in recipients:
                try:
                    await client.send_message(recipient, message)
                    success_count += 1
                except Exception:
                    continue

        self._update_status(f"전송 완료: {success_count}/{len(recipients)}")


def main() -> None:
    root = tk.Tk()
    app = TelegramSenderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
