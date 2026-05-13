class MarketState:
    is_open = True

    @classmethod
    def open_market(cls):
        cls.is_open = True

    @classmethod
    def close_market(cls):
        cls.is_open = False