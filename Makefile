.PHONY: install run test clean docker prod-up prod-down prod-logs prod-backup

install:
	pip install -r requirements.txt

run:
	python run.py

test:
	python -m pytest -q

clean:
	rm -f instance/*.sqlite3 instance/*.sqlite3-* ; find . -name __pycache__ -type d -prune -exec rm -rf {} +

docker:
	docker compose up --build

# ---- production (run on the server, next to .env.prod) ----
PROD = docker compose -f docker-compose.prod.yml --env-file .env.prod

prod-up:        ## build and start (or update) the API + tunnel
	$(PROD) up -d --build

prod-down:
	$(PROD) down

prod-logs:
	$(PROD) logs -f --tail 100

prod-backup:    ## copy the database volume to ./backups/
	mkdir -p backups
	docker run --rm -v myctf_myctf_instance:/data -v "$$PWD/backups":/backup alpine \
	  tar czf /backup/myctf-$$(date +%F).tgz -C /data .
