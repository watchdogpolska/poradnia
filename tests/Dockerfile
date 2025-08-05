FROM cypress/included:14.5.3

RUN apt-get update && apt-get install -y wait-for-it

WORKDIR /e2e
COPY . .

# If you still want to npm install (for mysql2, node-fetch etc.)
RUN npm install && npm ci

RUN cypress verify

# Use cypres immage entrypoint to run tests
