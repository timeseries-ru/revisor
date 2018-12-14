cd server/
gunicorn revisor_server:api --reload --limit-request-line 0 --workers 4 --preload
cd ..
