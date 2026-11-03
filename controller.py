# controller.py
# The two signal controllers that get compared.

from fuzzy_logic import compute_green_time


class FixedTimeController:
    """normal signal - same green time every phase, ignores traffic"""

    def __init__(self, green=30):
        self.green = green
        self.name = f"Fixed-time ({green}s)"

    def get_green_time(self, direction, queue_len, avg_wait):
        return self.green


class FuzzyController:
    """asks the fuzzy system for every phase"""

    def __init__(self):
        self.name = "Fuzzy logic"
        self.last_result = None

    def get_green_time(self, direction, queue_len, avg_wait):
        self.last_result = compute_green_time(queue_len, avg_wait)
        return self.last_result["green_time"]
