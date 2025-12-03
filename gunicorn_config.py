bind = "127.0.0.1:8015"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
max_requests = 1000
max_requests_jitter = 100
preload_app = True