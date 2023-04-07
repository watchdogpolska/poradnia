FROM cypress/base:14.17.0

RUN apt-get update
RUN apt-get install -y wait-for-it

WORKDIR /e2e

COPY package.json package-lock.json ./

RUN npm install --save

RUN npx cypress verify

COPY . .

CMD ["npx", "cypress", "run"]
