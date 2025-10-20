# =========================================================
# 🧩 ChainFeed Makefile
# Developer + Docker Integration
# =========================================================

.PHONY: test coverage lint build run logs stop clean network dev

# ─────────────────────────────────────────────────────────────
# 🧪 Development Utilities
# ─────────────────────────────────────────────────────────────
# Run all tests with proper PYTHONPATH
test:
	PYTHONPATH=. pytest test

# Run tests with coverage (optional)
coverage:
	PYTHONPATH=. pytest --cov=core test

# Run linter (if using one)
lint:
	ruff check .

# ─────────────────────────────────────────────────────────────
# 🐳 Docker Lifecycle
# ─────────────────────────────────────────────────────────────
IMAGE_NAME = chainfeed
CONTAINER_NAME = chainfeed
NETWORK_NAME = chainfeed-net
APP_DIR = $(shell pwd)

# Build the container image
build:
	@echo "🐳 Building ChainFeed Docker image..."
	docker build -t $(IMAGE_NAME) .

# Create Docker network (safe if exists)
network:
	@echo "🌐 Ensuring Docker network exists..."
	docker network inspect $(NETWORK_NAME) >/dev/null 2>&1 || docker network create $(NETWORK_NAME)

# Run container (mode defaults to historical unless overridden)
run:
	@echo "🚀 Starting ChainFeed container..."
	@if [ -z "$$MODE" ]; then MODE=historical; fi; \
	docker run -d --name $(CONTAINER_NAME) \
		--network $(NETWORK_NAME) \
		--env MODE=$$MODE \
		--env POLYGON_API_KEY=$${POLYGON_API_KEY} \
		-v $(APP_DIR)/data:/app/data \
		-v $(APP_DIR)/groups.yaml:/app/groups.yaml \
		$(IMAGE_NAME)

# Tail logs
logs:
	docker logs -f $(CONTAINER_NAME)

# Stop container safely
stop:
	@echo "🛑 Stopping ChainFeed container..."
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

# Clean all Docker cache and logs
clean:
	@echo "🧹 Cleaning up containers, logs, and cache..."
	docker system prune -f
	rm -rf data/live_logs/* data/historical_logs/* || true

# Open an interactive dev shell inside the container
dev:
	@echo "🧠 Opening ChainFeed interactive shell..."
	docker exec -it $(CONTAINER_NAME) /bin/bash