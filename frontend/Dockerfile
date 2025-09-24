FROM oven/bun:latest

WORKDIR /app

COPY . .

RUN bun install

RUN bun run build

CMD ["bun", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]