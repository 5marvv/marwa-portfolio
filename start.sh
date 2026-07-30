#!/bin/bash

# 1. Start sub-services in the background
(cd project/ai_analytics && uvicorn app:app --host 127.0.0.1 --port 5001) &
(cd project/AIFA && PORT=5002 python aifa.py) &
(cd project/automated_ai && uvicorn main:app --host 127.0.0.1 --port 5003) &
(cd project/devhub_project && PORT=5004 python devhub.py) &
(cd project/movie && PORT=5005 python movie.py) &
(cd project/queitspace && uvicorn QS:app --host 127.0.0.1 --port 5006) &
(cd project/stock_dashboard && PORT=5007 python stock.py) &

# Give sub-services time to initialize
sleep 3

# 2. Launch main Gateway on host PORT (Foreground process)
python server.py