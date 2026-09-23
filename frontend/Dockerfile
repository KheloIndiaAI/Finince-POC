# Build the React app, then serve the static files with nginx. nginx also
# proxies /api to the backend, so the browser only ever talks to one origin.
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Empty base URL: the app calls /api/... on its own origin, which nginx proxies.
ENV VITE_API_BASE_URL=""
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
