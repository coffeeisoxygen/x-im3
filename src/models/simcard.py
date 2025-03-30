class SimCard:
    def __init__(self, iccid, msisdn, signal):
        self.iccid = iccid
        self.msisdn = msisdn
        self.signal = signal

    def add_response(self, response):
        self.responses.append(response)

    def __repr__(self):
        return f"ICCID: {self.iccid}, MSISDN: {self.msisdn}, Signal: {self.signal}"
