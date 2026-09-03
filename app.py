import csv
import random
from datetime import datetime, timedelta

# Number of transactions we want
NUM_TRANSACTIONS = 500

# Starting date
start_date = datetime(2026, 8, 1)

transactions = []

for i in range(1, NUM_TRANSACTIONS + 1):

    transaction_id = f"TX{i:04d}"
    amount = random.choice([499, 799, 999, 1499, 2499, 4999, 9999])

    payment_date = start_date + timedelta(days=random.randint(0, 30))

    status = random.choice([
        "SUCCESS",
        "SUCCESS",
        "SUCCESS",
        "FAILED"
    ])

    transactions.append({
        "transaction_id": transaction_id,
        "amount": amount,
        "payment_date": payment_date.strftime("%Y-%m-%d"),
        "status": status
    })


# Save the data
with open("data/payments.csv", "w", newline="") as file:

    fieldnames = [
        "transaction_id",
        "amount",
        "payment_date",
        "status"
    ]

    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(transactions)


print("✅ Payment dataset created!")
print("📊 Transactions:", NUM_TRANSACTIONS)
print("📁 Saved to: data/payments.csv")