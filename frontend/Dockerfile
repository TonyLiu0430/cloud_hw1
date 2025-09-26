FROM oven/bun:latest
WORKDIR /app

COPY package.json bun.lock ./
RUN bun install

COPY . .
#RUN bun run build

CMD ["bun", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]