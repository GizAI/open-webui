PORT="${PORT:-8080}"
export PYTHONHOME=/root/miniconda3/envs/open-webui/
uvicorn open_webui.main:app --port $PORT --host 0.0.0.0 --forwarded-allow-ips '*' --reload
