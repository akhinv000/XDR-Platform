from opensearch_client import client

try:
    print("Ping:", client.ping())
    print(client.info())
except Exception as e:
    print(type(e).__name__)
    print(e)