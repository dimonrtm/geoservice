# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS base
WORKDIR /app

# dependencies layer (кэш)
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN if [ -f package-lock.json ]; then npm ci; \
    elif [ -f pnpm-lock.yaml ]; then corepack enable && pnpm i --frozen-lockfile; \
    elif [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    else npm i; fi

COPY . .

# ---- dev ----
FROM base AS dev
EXPOSE 5173
CMD ["sh","-lc","npm run dev -- --host 0.0.0.0 --port 5173"]

# ---- build ----
FROM base AS build
RUN npm run build

# ---- prod ----
FROM nginx:1.27-alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
