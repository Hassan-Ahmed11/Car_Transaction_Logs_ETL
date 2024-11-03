# Big Data Engineering Project (Processing API Using Big Data Tools)

## Overview
This project demonstrates a data engineering pipeline designed on CentOS 6.5 with Hadoop and other Big Data tools. The pipeline pulls data from an external API, processes it in real-time, and stores it in a cloud database.

**Pipeline Summary:**
1. **Data Collection**: A Python script pulls user data from a python script that generates car transactions logs.
2. **Ingestion**: The python script make a kafka topic then ingests the data and sends it to Apache Kafka.
4. **Storage & Processing**: Flume transfers a copy of the data from Kafka (as a consumer) to HDFS, while Spark processes data from Kafka (as a consumer) in real-time.
5. **Storage in Cloud**: Processed data is stored in InfluxDB on the cloud.
6. **Analysis & Visualization**:  Data is analyzed and visualized using Grafana Cloud, providing real-time insights and dashboards for monitoring user metrics and trends.

## Project Architecture
- **Python Script**: Simulates and stream car transaction data to a Kafka topic while providing an API endpoint to receive and log custom messages into Kafka.
- **Apache Kafka**: Manages data streaming and messaging between producers and consumers.
- **Apache Flume**: Stream data from a Kafka topic to an HDFS directory using Apache Flume, with a memory channel to buffer data between the source and sink.
- **Apache Spark**: Consumes data from Kafka for real-time processing.
- **InfluxDB**: Stores processed data for analytics and visualization on the cloud.
- **Grafana Cloud**:  Provides a platform for visualizing and analyzing data stored in InfluxDB, enabling the creation of interactive dashboards and reports to monitor user metrics and trends in real-time.

[Project Architecture Diagram]
<img width="959" alt="image" src="https://github.com/user-attachments/assets/f2a09030-fb86-46e6-9343-c63471f54db3">

---

## Prerequisites

- **Virtual Machine**: CentOS 6.5 (or any compatible machine depending on your setup)
- **Hadoop**: For distributed storage
- **Apache Flume**: For data ingestion
- **Apache Kafka**: For data streaming
- **Apache Spark**: For real-time data processing
- **InfluxDB**: For cloud-based storage
- **Grafana Cloud**: For data visualization and analysis

Ensure all tools are properly installed and configured in your environment. Follow their official installation guides as necessary.

Adjust this project's files (Configurations & Python Scripts) to match your setup.

---

## Project Setup

### 1. Python Script for generate logs and flask API with kafka producer
This script pulls user data from the RandomUser API and saves it to a specified local directory.

**`generate_logs.py`**
```python
# generate_logs.py
from flask import Flask, request, jsonify, Response
from kafka import KafkaProducer
import random
import uuid
import time
import json

app = Flask(__name__)

# Kafka configuration - Update with broker and topic details
KAFKA_BROKER = 'localhost:9092'  # Kafka broker address
TOPIC = 'car-transactions-logs'  # Kafka topic name

# Initialize Kafka Producer with error handling
try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("Kafka producer created successfully.")
except Exception as e:
    print(f"Failed to connect to Kafka broker: {e}")

# Sample data for generating realistic car transactions
buyers = ["John Doe", "Jane Smith", "Alice Johnson", "Michael Brown", "Emily Davis"]
car_brands_models = {"Toyota": ["Camry", "Corolla"], "Ford": ["F-150", "Mustang"]}
colors = ["Red", "Blue", "Black"]
countries = ["USA", "Canada", "Germany"]
branches = ["New York", "Toronto", "Berlin"]
years = [2015, 2016, 2017, 2018]

# Generate car transaction data with realistic attributes
def generate_car_transaction():
    brand = random.choice(list(car_brands_models.keys()))
    return {
        "transaction_id": str(uuid.uuid4()),
        "buyer_id": str(uuid.uuid4()),
        "buyer_name": random.choice(buyers),
        "car_brand": brand,
        "car_model": random.choice(car_brands_models[brand]),
        "year": random.choice(years),
        "color": random.choice(colors),
        "country": random.choice(countries),
        "branch": random.choice(branches),
        "transaction_price": round(random.uniform(20000, 80000), 2)
    }

# Endpoint to stream car transactions
@app.route('/api/stream_car_transactions', methods=['GET'])
def stream_car_transactions():
    def generate_and_send_transactions():
        start_time = time.time()
        end_time = start_time + 300  # 5-minute streaming window

        while True:
            if time.time() >= end_time:  # Sleep after 5 minutes
                print("Sleeping for 10 minutes...")
                time.sleep(600)
                start_time = time.time()
                end_time = start_time + 300

            transaction_data = generate_car_transaction()
            try:
                producer.send(TOPIC, transaction_data)  # Send transaction to Kafka
                print(f"Sent transaction data to Kafka: {transaction_data}")
            except Exception as e:
                print(f"Error sending data to Kafka: {e}")

            yield f"data:{json.dumps(transaction_data)}\n\n"  # Stream transaction
            time.sleep(2)  # Stream interval

    return Response(generate_and_send_transactions(), mimetype="text/event-stream")

# Endpoint to receive custom log messages and send to Kafka
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
    app.run(debug=True, port=5000)  # Run Flask app on port 5000
```
### 2. Configure Kafka
Set up Kafka to receive data from Flume.

- Create a new topic:
  ```bash
  kafka-topics.sh --create --topic <my-kafka-topic> --bootstrap-server localhost:9092
  ```
  **The project's topic name is `user_logs`**

  ```bash
  kafka-topics.sh --create --topic car-transactions-logs --bootstrap-server localhost:9092
  ```
### 3. Configure Flume

Set up Flume configurations:
- The configuration will consume data from Kafka and store it in HDFS.
  
#### Configuration: Kafka Source to HDFS Sink

This configuration reads data from the Kafka topic and writes it to HDFS.

**Kafka to HDFS `kafkatohdfs.conf`:**
```properties
# Define agent with source, sink, and channel
agent1.sources = kafka-source
agent1.sinks = hdfs-sink
agent1.channels = mem-channel

# Kafka source configuration
agent1.sources.kafka-source.type = org.apache.flume.source.kafka.KafkaSource
agent1.sources.kafka-source.kafka.bootstrap.servers = localhost:9092  # Update with your Kafka broker address
agent1.sources.kafka-source.kafka.topics = car-transactions-logs  # Kafka topic name

# HDFS sink configuration
agent1.sinks.hdfs-sink.type = hdfs
agent1.sinks.hdfs-sink.hdfs.path = hdfs://localhost:9000/Cars  # HDFS path to store data
agent1.sinks.hdfs-sink.hdfs.fileType = DataStream  # Stream data type
agent1.sinks.hdfs-sink.hdfs.writeFormat = Text  # Output format
agent1.sinks.hdfs-sink.hdfs.rollInterval = 60  # Time in seconds for file roll-over

# Memory channel configuration
agent1.channels.mem-channel.type = memory

# Source-to-channel and sink-to-channel bindings
agent1.sources.kafka-source.channels = mem-channel
agent1.sinks.hdfs-sink.channel = mem-channel
```
### 4. Configure Spark
Use Spark to consume data from Kafka, process it, and send results to InfluxDB.

#### Spark Script
This Spark application reads data from Kafka, processes it, and writes it to InfluxDB.

***Make sure to replace placeholders such as `your-influxdb-url`, `your-org-id`, `your-bucket-name`, `precision`, `your-influxdb-token`***

**Spark Application `pyspark_influx.py`:**
```python
from pyspark.sql import SparkSession
from pyspark.sql import Row
from kafka import KafkaConsumer
import json
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Initialize Spark session for data processing
spark = SparkSession.builder \
    .appName("KafkaToSparkCarTransactions") \
    .getOrCreate()

# InfluxDB configuration - Replace these fields as needed
influxdb_url = "https://us-east-1-1.aws.cloud2.influxdata.com"  # Your InfluxDB URL
token = "your_token_here"  # Your InfluxDB token
org = "your_organization"  # Your organization name in InfluxDB
bucket = "ETL_Project"  # Name of the bucket in InfluxDB

# Initialize InfluxDB client
client = InfluxDBClient(url=influxdb_url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Define schema for car transaction logs in Spark
schema = ["transaction_id", "buyer_id", "buyer_name", "car_brand", "car_model", 
          "year", "color", "country", "branch", "transaction_price"]

# Initialize Kafka consumer for reading car transaction data
consumer = KafkaConsumer(
    'car-transactions-logs',  # Kafka topic name
    bootstrap_servers='localhost:9092',  # Kafka broker address
    auto_offset_reset='latest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Accumulation of rows and configuration for batch processing
rows = []
batch_size = 100  # Number of records to process in each batch
max_messages = 100  # Total messages to process before stopping
message_count = 0  # Counter for processed messages

# Process each message from Kafka
for message in consumer:
    data = message.value  # Deserialized data

    # Create a Row object for Spark with transaction details
    row = Row(
        transaction_id=data['transaction_id'], 
        buyer_id=data['buyer_id'], 
        buyer_name=data['buyer_name'], 
        car_brand=data['car_brand'], 
        car_model=data['car_model'], 
        year=int(data['year']), 
        color=data['color'], 
        country=data['country'], 
        branch=data['branch'], 
        transaction_price=float(data['transaction_price'])
    )
    rows.append(row)
    message_count += 1

    # Process the batch when it reaches the defined batch size
    if len(rows) == batch_size:
        df = spark.createDataFrame(rows, schema=schema)
        df.show()  # Show the data batch

        # Write data to InfluxDB for storage and analysis
        for row in df.collect():
            point = Point("car_transaction_data")\
                .tag("transaction_id", row.transaction_id)\
                .tag("buyer_id", row.buyer_id)\
                .tag("buyer_name", row.buyer_name)\
                .tag("car_brand", row.car_brand)\
                .tag("car_model", row.car_model)\
                .tag("country", row.country)\
                .tag("branch", row.branch)\
                .field("year", row.year)\
                .field("transaction_price", row.transaction_price)\
                .field("color", row.color)
            write_api.write(bucket=bucket, org=org, record=point)
        rows = []  # Reset rows list for the next batch

    # Stop processing after reaching max_messages
    if message_count >= max_messages:
        print(f"Processed {max_messages} messages. Stopping.")
        break

# Process any remaining rows
if rows:
    df = spark.createDataFrame(rows, schema=schema)
    df.show()
    for row in df.collect():
        point = Point("car_transaction_data")\
            .tag("transaction_id", row.transaction_id)\
            .tag("buyer_id", row.buyer_id)\
            .tag("buyer_name", row.buyer_name)\
            .tag("car_brand", row.car_brand)\
            .tag("car_model", row.car_model)\
            .tag("country", row.country)\
            .tag("branch", row.branch)\
            .field("year", row.year)\
            .field("transaction_price", row.transaction_price)\
            .field("color", row.color)
        write_api.write(bucket=bucket, org=org, record=point)

# Clean up resources
consumer.close()
client.close()
```
### 5. Configure InfluxDB Cloud
Set up InfluxDB Cloud to store processed data from Spark. 
Follow the [InfluxDB installation guide](https://docs.influxdata.com/influxdb/cloud/get-started/setup/) to set up InfluxDB Cloud.

1. **Sign Up and Create a Bucket**: 
   - If you haven't already, sign up for an InfluxDB Cloud account at [InfluxDB Cloud](https://cloud2.influxdata.com/signup).
   - Once logged in, create a new bucket where you will store the processed data. 

2. **Retrieve Connection Details**: 
   - Go to your InfluxDB Cloud dashboard and navigate to the **Data** section to find your organization and bucket information.
   - Collect your **API Token**, **organization ID**, and **bucket name**, as you will need these for your Spark application.

3. **Configure Connection in Spark**: 
   Ensure your Spark application is configured to connect to InfluxDB Cloud by replacing the placeholders in your Spark script with your InfluxDB Cloud details:
   - `your-influxdb-url`: Use the InfluxDB Cloud API endpoint (e.g., `https://us-west-2-1.aws.cloud2.influxdata.com`).
   - `your_bucket-name`: The name of the bucket you created.
   - `your_org-id`: Your organization ID from InfluxDB Cloud.
   - `your_api_token`: The API token you generated.

### 6. Configure Grafana Cloud

1. **Sign Up and Create a Dashboard**: 
   - Sign up at [Grafana Cloud](https://grafana.com/products/cloud/) and create a new dashboard for visualizing data.

2. **Add InfluxDB Data Source**: 
   - In the dashboard, navigate to **Data Sources** and select **Add Data Source**. Choose **InfluxDB**.

3. **Configure InfluxDB Connection**: 
   - Fill in the connection details:
     - **URL**: Use your InfluxDB Cloud API endpoint.
     - **Database**: Enter your bucket name.
     - **Password**: Input your API token.
  
4. **Test Data Source**: 
   - Click **Save & Test** to ensure the connection is successful.

5. **Create Visualizations**: 
   - Add panels to your dashboard for various visualizations like time series graphs and tables, customizing queries and settings as needed.

6. **Set Up Alerts**: 
   - Optionally, configure alerts to notify you of significant data changes by enabling alerts in the panel settings and defining notification conditions.

---

## Usage

1. **Ensure all of the Prerequisites services working (HDFS, YARN, ZooKeeper, Kafka)**:
   - For HDFS & YARN:
     ```bash
     start-all.sh
     ```
   - For ZooKeeper & Kafka"
     ```bash
     cd $KAFKA_HOME
     ```
     ```bash
     bin/zookeeper-server-start.sh config/zookeeper.properties
     ```
     ```bash
     bin/kafka-server-start.sh config/server.properties
     ```
2. **Create Kafka Topic**:
     ```bash
     cd $KAFKA_HOME
     ```
     ```bash
     bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic car-transactions-logs
     ```
3. **Put Flume config files in config directory**:
     ```bash
     cp /<your-path>/api_to_kafka.conf $FLUME_HOME/conf
     ```
     ```bash
     cp /<your-path>/kafka_to_hdfs.conf $FLUME_HOME/conf
     ```
4. **Run Flume Agent**:
   ```bash
   $FLUME_HOME/bin/flume-ng agent --conf conf --conf-file $FLUME_HOME/conf/kafkatohdfs.conf --name agent1 -Dflume.root.logger=DEBUG,console
   ```
5. **Run the Python script to fetch data**:
   ```bash
   python3 /<your-path>/connection_script.py
   ```
6. **Submit the Spark job**:
   
   	**Note that you must have the needed packages to connect to Kafka from Spark.**
   
   	**You also must change the numbers in this command to match your versions of Kafka and Sprak**
   ```bash
   spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 pyspark_influx.py 
   ```
6. **Verify data in InfluxDB Cloud**:
   
   Check your InfluxDB Cloud dashboard to ensure data is being written to your specified bucket.
   
[InfluxDB Results]
<img width="944" alt="image" src="https://github.com/user-attachments/assets/7cb76155-e105-4adc-8429-58bf228a5566">

---
## Data Analysis & Visualization with Grafana

To visualize and analyze the data ingested into InfluxDB Cloud, I utilized **Grafana**, a powerful open-source analytics and monitoring platform. Grafana allows for real-time monitoring and data visualization, making it an essential tool in my project. Below are key points about how I integrated Grafana into my project:

- **Data Visualization**: Grafana enables the creation of dynamic dashboards, where I can visualize time-series data collected from various sources. This helped in identifying trends, patterns, and anomalies within the data.

- **Integration with InfluxDB Cloud**: I configured Grafana to connect to my InfluxDB Cloud instance, allowing for seamless querying of data stored in the InfluxDB database. This integration facilitated real-time data analysis through Flux queries.

- **Custom Dashboards**: I created custom dashboards tailored to specific metrics relevant to my project. These dashboards include various visualizations such as graphs, tables, and gauges, providing a comprehensive view of the data.

- **Alerts and Notifications**: Grafana's alerting features enabled me to set up notifications based on certain thresholds, ensuring timely responses to significant changes in the data.

By leveraging Grafana, I was able to enhance the analytical capabilities of my project, making the data not only accessible but also actionable.

[Grafana Results]
<img width="946" alt="image" src="https://github.com/user-attachments/assets/0e9c4a6a-7c00-44ba-9188-5db7ae2b8e0d">


---

## Project Status and Future Work

This project successfully establishes a real-time data pipeline using Flume, Kafka, Spark, and InfluxDB Cloud. The data flows seamlessly from data generation through processing and storage in the cloud.

### Future Enhancements

- **Data Processing Optimization**: Implement advanced data transformation techniques in Spark, such as structured streaming optimizations and partitioning strategies, to handle even larger datasets more efficiently.

- **Expanded Data Sources and Outputs**: 
   - Add new data sources or APIs to enrich the dataset.
   - Consider integrating additional output storage or analytics solutions, such as Elasticsearch, for more versatile data use cases.

---

## Acknowledgments

- [Apache Flume](https://flume.apache.org/) for its data ingestion capabilities.
- [Apache Kafka](https://kafka.apache.org/) for managing data streaming.
- [Apache Spark](https://spark.apache.org/) for real-time data processing.
- [Apache Hadoop](https://hadoop.apache.org/) for distributed storage solutions.
- [InfluxDB Cloud](https://www.influxdata.com/products/influxdb-cloud/) for its powerful cloud-based data storage and processing tools.
- [Grafana](https://grafana.com/) for its exceptional data visualization and monitoring capabilities.

