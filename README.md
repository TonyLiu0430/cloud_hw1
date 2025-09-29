# run
docker compose up --build

# run with cloudflared tunnel
docker compose --profile tunnel up -d

# delete volumes
docker compose down -v

will migreate to k3s soon