#!/usr/bin/env python3
"""
Health check script for data-visualization service.
"""

import os
import sys
import redis
import requests

def main():
    try:
        # Check Redis connection
        redis_host = os.getenv('REDIS_HOST', 'redis-service')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            socket_connect_timeout=5
        )
        redis_client.ping()
        
        # Check if Streamlit is responding
        response = requests.get('http://localhost:8501/healthz', timeout=5)
        if response.status_code == 200:
            print("OK")
            sys.exit(0)
        else:
            print("FAIL - Streamlit not responding")
            sys.exit(1)
            
    except Exception as e:
        print(f"FAIL - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()