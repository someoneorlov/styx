FROM node:22-alpine AS test_builder
ENV NODE_ENV production
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
RUN npm run build