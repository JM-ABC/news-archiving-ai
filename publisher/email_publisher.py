from typing import List


class EmailPublisher:
    def __init__(self, api_key: str, from_addr: str, to_addrs: List[str], bcc_addrs: List[str] = None):
        self._api_key = api_key
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.bcc_addrs = bcc_addrs or []

    def send(self, subject: str, html: str) -> bool:
        if not self._api_key:
            print("[email] API 키 없음 — 건너뜀")
            return False
        try:
            import resend
            resend.api_key = self._api_key
            params = {
                "from": self.from_addr,
                "to": self.to_addrs,
                "subject": subject,
                "html": html,
            }
            if self.bcc_addrs:
                params["bcc"] = self.bcc_addrs
            resend.Emails.send(params)
            print(f"[email] 발송 완료 → {self.to_addrs}")
            return True
        except Exception as e:
            print(f"[email] 발송 실패: {e}")
            return False
