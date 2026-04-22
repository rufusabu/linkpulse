# ---------- Base ----------
FROM node:20-alpine AS base

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

# ---------- Development (default) ----------
FROM base AS dev

COPY . .

EXPOSE 5173

# Vite dev server — host flag makes it accessible outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---------- Production ----------
FROM base AS build

COPY . .
RUN npm run build

# Serve the static build with a lightweight server
FROM nginx:alpine AS prod

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
