CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password BYTEA NOT NULL
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL
);

CREATE TABLE sale_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    starting_price NUMERIC NOT NULL,
    end_date TIMESTAMP NOT NULL,
    seller_id INTEGER REFERENCES users(id)
);

CREATE TABLE bids (
    id SERIAL PRIMARY KEY,
    sale_item_id uuid REFERENCES sale_items(id),
    user_id INTEGER REFERENCES users(id),
    price NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bids_saleitem_price ON bids(sale_item_id, price DESC);


