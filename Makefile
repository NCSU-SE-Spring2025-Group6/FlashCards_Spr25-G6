serve-backend:
	gunicorn -b 127.0.0.1:5000 backend.src.api:app

.PHONY: serve-backend