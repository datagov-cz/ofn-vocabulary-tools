FROM node:20 AS build
WORKDIR /client
COPY . .
RUN npm ci
RUN npm run build

FROM nginx:latest AS deploy
COPY --from=build /client/dist /usr/share/nginx/html
