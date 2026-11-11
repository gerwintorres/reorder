-- Queries behind the product repository. The values are examples: the
-- repository sends them as bound parameters, never inside the SQL text.

-- Create a product and return it with its generated id.
-- owner_id must reference an existing user.
INSERT INTO products (owner_id, sku, name)
VALUES (1, 'A-100', 'Oil filter')
RETURNING id, owner_id, sku, name;

-- Get one product by id. The owner filter stops a user from reading another
-- user's product by guessing its id.
SELECT id, owner_id, sku, name
FROM products
WHERE id = 1 AND owner_id = 1;

-- One page of an owner's products. Without ORDER BY the row order is not
-- guaranteed, so pages could repeat or skip rows. Sorting by sku lets the
-- (owner_id, sku) unique index serve both the filter and the order.
SELECT id, owner_id, sku, name
FROM products
WHERE owner_id = 1
ORDER BY sku
LIMIT 50 OFFSET 0;

-- Total number of the owner's products, for the page metadata.
SELECT count(*) AS total
FROM products
WHERE owner_id = 1;

-- Weekly sales of a product, oldest week first. The (product_id, week_start)
-- unique index finds the product's rows without reading the whole table.
SELECT week_start, qty, revenue, profit
FROM weekly_sales
WHERE product_id = 1
ORDER BY week_start;
