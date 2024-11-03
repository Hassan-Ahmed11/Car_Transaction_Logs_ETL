from flask import Flask, request, jsonify, Response
from kafka import KafkaProducer
import random
import uuid
import time
import json

app = Flask(__name__)

# Kafka configuration
KAFKA_BROKER = 'localhost:9092'
TOPIC = 'car-transactions-logs'

# Create Kafka Producer with error handling
try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("Kafka producer created successfully.")
except Exception as e:
    print(f"Failed to connect to Kafka broker: {e}")

# Sample data for realistic car transactions
buyers = [
    "John Doe", "Jane Smith", "Alice Johnson", "Michael Brown", "Emily Davis",
    "David Wilson", "Sarah Lewis", "Robert Walker", "Jessica Lee", "Daniel White",
    "Sophia Harris", "James Martin", "Olivia Thompson", "William Hall", "Ava Scott",
    "Mason Clark", "Isabella Rodriguez", "Liam Robinson", "Mia Young", "Ethan King",
    "Charlotte Wright", "Logan Green", "Amelia Adams", "Jacob Turner", "Aiden Nelson"
]

car_brands_models = {
    "Toyota": ["Camry", "Corolla", "RAV4"],
    "Ford": ["F-150", "Mustang", "Explorer"],
    "BMW": ["X5", "3 Series", "5 Series"],
    "Tesla": ["Model S", "Model 3", "Model X"],
    "Mercedes": ["C-Class", "E-Class", "GLE"],
    "Honda": ["Civic", "Accord", "CR-V"],
    "Audi": ["A4", "Q5", "A6"],
    "Chevrolet": ["Silverado", "Equinox", "Malibu"],
    "Hyundai": ["Elantra", "Santa Fe", "Tucson"],
    "Nissan": ["Altima", "Rogue", "Sentra"]
}

colors = ["Red", "Blue", "Black", "White", "Gray", "Green", "Yellow", "Silver"]
countries = ["USA", "Canada", "Germany", "UK", "Australia", "France", "Italy", "Japan", "South Korea", "Mexico"]
branches = ["New York", "Toronto", "Berlin", "London", "Sydney", "Paris", "Rome", "Tokyo", "Seoul", "Mexico City"]
years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]

# Function to generate realistic car transaction data
def generate_car_transaction():
    brand = random.choice(list(car_brands_models.keys()))
    transaction_data = {
        "transaction_id": str(uuid.uuid4()),
        "buyer_id": str(uuid.uuid4()),
        "buyer_name": random.choice(buyers),
        "car_brand": brand,
        "car_model": random.choice(car_brands_models[brand]),
        "year": random.choice(years),
        "color": random.choice(colors),
        "country": random.choice(countries),
        "branch": random.choice(branches),
        "transaction_price": round(random.uniform(20000, 80000), 2)  # Price range for analysis
    }
    return transaction_data

# Streaming endpoint
@app.route('/api/stream_car_transactions', methods=['GET'])
def stream_car_transactions():
    def generate_and_send_transactions():
        start_time = time.time()
        end_time = start_time + 300

        while True:
            # Reset timer if 5 minutes have passed
            if time.time() >= end_time:
                print("Sleeping for 10 minutes...")
                time.sleep(600)
                start_time = time.time()
                end_time = start_time + 300

            transaction_data = generate_car_transaction()
            try:
                producer.send(TOPIC, transaction_data)  # Send data to Kafka
                print(f"Sent transaction data to Kafka: {transaction_data}")
            except Exception as e:
                print(f"Error sending data to Kafka: {e}")

            yield f"data:{json.dumps(transaction_data)}\n\n"  # For streaming
            time.sleep(2)  # New log every 2 seconds

    return Response(generate_and_send_transactions(), mimetype="text/event-stream")

# Endpoint to receive log messages
@app.route('/api/logs', methods=['POST'])
def log_message():
    data = request.json
    try:
        producer.send(TOPIC, data)
        print(f"Received log data: {data}")
        return jsonify({"status": "success", "message": "Log received", "data": data}), 200
    except Exception as e:
        print(f"Error sending log to Kafka: {e}")
        return jsonify({"status": "error", "message": "Failed to send log to Kafka"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

