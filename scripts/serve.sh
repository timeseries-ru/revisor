cd server/
gunicorn revisor_server:api --reload --limit-request-line 0
cd ..
