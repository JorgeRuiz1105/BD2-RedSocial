import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient
from cassandra.cluster import Cluster
import redis

# Gestión de conexiones

def get_postgres_connection():
    try:
        conn = psycopg2.connect(
            dbname="red_social_db",
            user="postgres",
            password="admin123",
            host="localhost",
            port="5433"
        )
        return conn
    except Exception as e:
        print(f"Error conectando a PostgreSQL: {e}")
        return None

def get_mongo_connection():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["red_social_nosql"]
        return db
    except Exception as e:
        print(f"Error conectando a MongoDB: {e}")
        return None

def get_cassandra_connection():
    try:
        cluster = Cluster(['localhost'], port=9042)
        session = cluster.connect()
        return session
    except Exception as e:
        print(f"Error conectando a Cassandra: {e}")
        return None

def get_redis_connection():
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping() # ping para ver si responde
        return r
    except Exception as e:
        print(f"Error conectando a Redis: {e}")
        return None