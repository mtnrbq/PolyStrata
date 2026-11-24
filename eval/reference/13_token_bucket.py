import time


class TokenBucket:
    def __init__(self, rate, capacity, clock=time.monotonic):
        if rate <= 0 or capacity <= 0:
            raise ValueError((rate, capacity))
        self.rate, self.capacity, self.clock = rate, capacity, clock
        self.tokens, self.last = capacity, clock()

    def _refill(self):
        now = self.clock()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now

    def available(self):
        self._refill()
        return self.tokens

    def allow(self, tokens=1.0):
        if tokens <= 0 or tokens > self.capacity:
            raise ValueError(tokens)
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
