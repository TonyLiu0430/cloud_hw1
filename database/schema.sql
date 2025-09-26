CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(64) UNIQUE NOT NULL,
    password BYTEA NOT NULL
);

CREATE TABLE sale_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    starting_price NUMERIC NOT NULL,
    end_date TIMESTAMP NOT NULL,
    seller_id uuid REFERENCES users(id)
);

CREATE TABLE sale_item_images (
    id SERIAL PRIMARY KEY,
    sale_item_id uuid REFERENCES sale_items(id),
    image_url TEXT NOT NULL
);

CREATE TABLE bids (
    id SERIAL PRIMARY KEY,
    sale_item_id uuid REFERENCES sale_items(id),
    user_id uuid REFERENCES users(id),
    price NUMERIC NOT NULL,   
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bids_saleitem_price ON bids(sale_item_id, price DESC);


