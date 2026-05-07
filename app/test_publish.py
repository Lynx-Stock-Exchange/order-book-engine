from app.kafka.producer import publish

publish("stock_prices", {
    "ticker": "AAPL",
    "price": 250
})

print("EVENT SENT")