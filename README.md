# 보내기 (Telegram 대량 전송 도우미)

아래 프로그램은 **Telegram MTProto(telethon)** 기반으로 특정 메시지를 여러 명에게 한 번에 보내는 간단한 데스크톱 앱입니다.
Python + Tkinter로 만들었고, `보내기.exe`로 빌드하는 방법까지 설명합니다.

## 1) 준비물

1. Telegram 계정
2. Telegram 개발자 정보
   - `api_id`, `api_hash`가 필요합니다.
   - https://my.telegram.org 에서 발급받습니다.

## 2) 설치 (처음 한 번만)

1. Python 설치 (권장: 3.10 이상)
2. 프로젝트 폴더에서 아래 명령을 실행합니다.

```bash
pip install -r requirements.txt
```

## 3) 실행 방법

```bash
python main.py
```

### 첫 실행 시 로그인

1. 앱에 `api_id`, `api_hash`를 입력합니다.
2. 전송 버튼을 누르면 전화번호를 묻는 창이 뜹니다.
3. 문자/Telegram 앱으로 받은 인증 코드를 입력합니다.
4. 2FA 비밀번호가 있는 경우 `2FA PW`에 입력합니다.

## 4) 사용 방법

1. **전송대상** 칸에 최대 50명까지 입력합니다.
   - `@username` 또는 전화번호(`+8210...`) 형식
2. **전송메시지**에 보낼 메시지를 입력합니다.
3. **전송시간**은 아래 중 하나로 입력합니다.
   - `YYYY-MM-DD HH:MM`
   - `HH:MM` (오늘/내일 자동 계산)
4. 각 줄의 **전송** 버튼을 누르면 예약 또는 즉시 전송됩니다.

## 5) 실행파일(보내기.exe) 만들기

1. PyInstaller 설치

```bash
pip install pyinstaller
```

2. exe 빌드

```bash
pyinstaller --onefile --noconsole --name 보내기 main.py
```

3. `dist/보내기.exe` 파일이 생성됩니다.

## 6) 참고사항

- MTProto 방식(telethon) 사용
- 한 번 로그인하면 세션 파일(`send_session.session`)이 생성됩니다.
- Telegram 정책에 따라 과도한 발송은 제한될 수 있습니다.
