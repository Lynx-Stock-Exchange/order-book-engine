from app.order import Order, OrderType, Side
from app.order_book import OrderBook
from app.matcher import match

book = OrderBook("AAPL")

buy = Order(
    "1", "platform1", "user1",
    "STOCK", "AAPL",
    OrderType.LIMIT, Side.BUY,
    100, 130
)

sell = Order(
    "2", "platform1", "user2",
    "STOCK", "AAPL",
    OrderType.LIMIT, Side.SELL,
    50, 129
)

book.add(buy)
book.add(sell)

trades = match(book, 129)

print(trades)
print(buy.status, buy.filled_quantity)
print(sell.status, sell.filled_quantity)




print("\n--- TEST 1: MARKET BUY ---")

book = OrderBook("AAPL")

market_buy = Order(
    "1", "platform1", "user1",
    "STOCK", "AAPL",
    OrderType.MARKET, Side.BUY,
    30
)

book.add(market_buy)

trades = match(book, 100)

print(trades)
print(market_buy.status, market_buy.filled_quantity)




print("\n--- TEST 2: LIMIT BUY trigger ---")

book = OrderBook("AAPL")

buy = Order("1", "p", "u", "STOCK", "AAPL", OrderType.LIMIT, Side.BUY, 10, 105)
book.add(buy)

trades = match(book, 100)

print(trades)
print(buy.status)  # FILLED




print("\n--- TEST 2b: LIMIT BUY no trigger ---")

book = OrderBook("AAPL")

buy = Order("1", "p", "u", "STOCK", "AAPL", OrderType.LIMIT, Side.BUY, 10, 95)
book.add(buy)

trades = match(book, 100)

print(trades)
print(buy.status)  #  PENDING




print("\n--- TEST 3: LIMIT SELL trigger ---")

book = OrderBook("AAPL")

sell = Order("1", "p", "u", "STOCK", "AAPL", OrderType.LIMIT, Side.SELL, 10, 95)
book.add(sell)

trades = match(book, 100)

print(trades)
print(sell.status)  #  FILLED




print("\n--- TEST 4: PARTIAL FILL ---")

book = OrderBook("AAPL")

big_order = Order("1", "p", "u", "STOCK", "AAPL", OrderType.MARKET, Side.BUY, 100)
book.add(big_order)

trades = match(book, 100, max_liquidity_per_tick=50)

print(trades)
print(big_order.status)          #  PARTIALLY_FILLED
print(big_order.filled_quantity) #  50




print("\n--- TEST 5: SECOND PARTIAL ---")

book = OrderBook("AAPL")

order = Order("1", "p", "u", "STOCK", "AAPL", OrderType.MARKET, Side.BUY, 100)
book.add(order)

# tick 1
match(book, 100, max_liquidity_per_tick=40)

print(order.status, order.filled_quantity)  # 40

# tick 2
match(book, 100, max_liquidity_per_tick=40)

print(order.status, order.filled_quantity)  # 80

# tick 3
match(book, 100, max_liquidity_per_tick=40)

print(order.status, order.filled_quantity)  # 100 + FILLED





print("\n--- TEST 6: BUY + SELL compete ---")

book = OrderBook("AAPL")

buy = Order("1", "p", "u", "STOCK", "AAPL", OrderType.MARKET, Side.BUY, 80)
sell = Order("2", "p", "u", "STOCK", "AAPL", OrderType.MARKET, Side.SELL, 80)

book.add(buy)
book.add(sell)

trades = match(book, 100, max_liquidity_per_tick=100)

print(trades)
print("BUY:", buy.filled_quantity)
print("SELL:", sell.filled_quantity)





print("\n--- TEST 7: WEIGHTED AVG ---")

book = OrderBook("AAPL")

order = Order("1", "p", "u", "STOCK", "AAPL", OrderType.MARKET, Side.BUY, 100)
book.add(order)

match(book, 100, max_liquidity_per_tick=50)
match(book, 120, max_liquidity_per_tick=50)

print(order.average_fill_price)  # 110





print("\n--- TEST 8: CANCELLED ---")

book = OrderBook("AAPL")

order = Order("1", "p", "u", "STOCK", "AAPL", OrderType.MARKET, Side.BUY, 50)
order.cancel()

book.add(order)

trades = match(book, 100)

print(trades)  # empty