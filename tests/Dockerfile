FROM cypress/base:14

RUN apt-get update
RUN apt-get install -y wait-for-it

WORKDIR /e2e

RUN npm install --save-dev cypress
RUN npm install --save-dev mysql

RUN npx cypress verify

COPY . .

CMD ["npx", "cypress", "run"]
