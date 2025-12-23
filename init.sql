-- Create database schema with multiple tables and complex relationships

-- Categories table (no dependencies)
CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_category_id INTEGER REFERENCES categories(category_id)
);

-- Manufacturers/Producers table
CREATE TABLE IF NOT EXISTS manufacturers (
    manufacturer_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    country VARCHAR(100),
    founded_year INTEGER,
    website VARCHAR(200),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    contact_email VARCHAR(100),
    contact_phone VARCHAR(50),
    country VARCHAR(100),
    city VARCHAR(100),
    rating DECIMAL(3, 2),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Warehouses table
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    country VARCHAR(100),
    city VARCHAR(100),
    address TEXT,
    capacity INTEGER,
    manager_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table (depends on categories and manufacturers)
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL,
    category_id INTEGER REFERENCES categories(category_id),
    manufacturer_id INTEGER REFERENCES manufacturers(manufacturer_id),
    sku VARCHAR(100) UNIQUE,
    weight_kg DECIMAL(8, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product attributes table
CREATE TABLE IF NOT EXISTS product_attributes (
    attribute_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,
    attribute_name VARCHAR(100) NOT NULL,
    attribute_value TEXT NOT NULL
);

-- Product suppliers junction table (many-to-many)
CREATE TABLE IF NOT EXISTS product_suppliers (
    product_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,
    supplier_id INTEGER REFERENCES suppliers(supplier_id) ON DELETE CASCADE,
    supply_price DECIMAL(10, 2),
    lead_time_days INTEGER,
    minimum_order_quantity INTEGER DEFAULT 1,
    PRIMARY KEY (product_id, supplier_id)
);

-- Inventory table (tracks product quantities in warehouses)
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,
    warehouse_id INTEGER REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    last_restocked TIMESTAMP,
    UNIQUE(product_id, warehouse_id)
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    phone VARCHAR(50),
    country VARCHAR(100),
    city VARCHAR(100),
    address TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    loyalty_points INTEGER DEFAULT 0
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id) ON DELETE SET NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(12, 2) NOT NULL,
    shipping_address TEXT,
    shipping_city VARCHAR(100),
    shipping_country VARCHAR(100),
    warehouse_id INTEGER REFERENCES warehouses(warehouse_id),
    shipped_date TIMESTAMP,
    delivered_date TIMESTAMP
);

-- Order items table (many-to-many between orders and products)
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(product_id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount_percent DECIMAL(5, 2) DEFAULT 0,
    subtotal DECIMAL(12, 2) NOT NULL
);

-- Product reviews table
CREATE TABLE IF NOT EXISTS product_reviews (
    review_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(customer_id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200),
    comment TEXT,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_purchase BOOLEAN DEFAULT FALSE,
    helpful_count INTEGER DEFAULT 0
);

-- Shipments table (tracks shipping details)
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
    carrier VARCHAR(100),
    tracking_number VARCHAR(200),
    shipped_date TIMESTAMP,
    estimated_delivery TIMESTAMP,
    actual_delivery TIMESTAMP,
    status VARCHAR(50) DEFAULT 'in_transit'
);

-- Table and column comments for AI-facing schema descriptions
COMMENT ON TABLE categories IS 'Product category hierarchy with optional parent category for nesting';
COMMENT ON COLUMN categories.category_id IS 'Primary key';
COMMENT ON COLUMN categories.name IS 'Category name';
COMMENT ON COLUMN categories.description IS 'Short description of the category';
COMMENT ON COLUMN categories.parent_category_id IS 'Parent category when nested';

COMMENT ON TABLE manufacturers IS 'Product manufacturers and producers';
COMMENT ON COLUMN manufacturers.manufacturer_id IS 'Primary key';
COMMENT ON COLUMN manufacturers.name IS 'Manufacturer name';
COMMENT ON COLUMN manufacturers.country IS 'Country of origin';
COMMENT ON COLUMN manufacturers.founded_year IS 'Year the manufacturer was founded';
COMMENT ON COLUMN manufacturers.website IS 'Official website URL';
COMMENT ON COLUMN manufacturers.description IS 'Manufacturer overview';
COMMENT ON COLUMN manufacturers.created_at IS 'Record creation timestamp';

COMMENT ON TABLE suppliers IS 'Suppliers providing products to the catalog';
COMMENT ON COLUMN suppliers.supplier_id IS 'Primary key';
COMMENT ON COLUMN suppliers.name IS 'Supplier name';
COMMENT ON COLUMN suppliers.contact_email IS 'Primary contact email';
COMMENT ON COLUMN suppliers.contact_phone IS 'Primary contact phone';
COMMENT ON COLUMN suppliers.country IS 'Supplier country';
COMMENT ON COLUMN suppliers.city IS 'Supplier city';
COMMENT ON COLUMN suppliers.rating IS 'Supplier rating (0-5)';
COMMENT ON COLUMN suppliers.active IS 'Whether supplier is active';
COMMENT ON COLUMN suppliers.created_at IS 'Record creation timestamp';

COMMENT ON TABLE warehouses IS 'Physical warehouse locations for inventory';
COMMENT ON COLUMN warehouses.warehouse_id IS 'Primary key';
COMMENT ON COLUMN warehouses.name IS 'Warehouse name';
COMMENT ON COLUMN warehouses.country IS 'Country of the warehouse';
COMMENT ON COLUMN warehouses.city IS 'City of the warehouse';
COMMENT ON COLUMN warehouses.address IS 'Street address';
COMMENT ON COLUMN warehouses.capacity IS 'Storage capacity estimate';
COMMENT ON COLUMN warehouses.manager_name IS 'Responsible manager';
COMMENT ON COLUMN warehouses.created_at IS 'Record creation timestamp';

COMMENT ON TABLE products IS 'Products sold, linked to categories and manufacturers';
COMMENT ON COLUMN products.product_id IS 'Primary key';
COMMENT ON COLUMN products.name IS 'Product name';
COMMENT ON COLUMN products.description IS 'Product description';
COMMENT ON COLUMN products.price IS 'Retail price';
COMMENT ON COLUMN products.stock_quantity IS 'Current on-hand stock';
COMMENT ON COLUMN products.category_id IS 'Category reference';
COMMENT ON COLUMN products.manufacturer_id IS 'Manufacturer reference';
COMMENT ON COLUMN products.sku IS 'Unique stock keeping unit';
COMMENT ON COLUMN products.weight_kg IS 'Weight in kilograms';
COMMENT ON COLUMN products.is_active IS 'Whether the product is offered for sale';
COMMENT ON COLUMN products.created_at IS 'Record creation timestamp';

COMMENT ON TABLE product_attributes IS 'Key/value attributes for products';
COMMENT ON COLUMN product_attributes.attribute_id IS 'Primary key';
COMMENT ON COLUMN product_attributes.product_id IS 'Product reference';
COMMENT ON COLUMN product_attributes.attribute_name IS 'Attribute name';
COMMENT ON COLUMN product_attributes.attribute_value IS 'Attribute value';

COMMENT ON TABLE product_suppliers IS 'Junction table linking products to suppliers with pricing';
COMMENT ON COLUMN product_suppliers.product_id IS 'Product reference';
COMMENT ON COLUMN product_suppliers.supplier_id IS 'Supplier reference';
COMMENT ON COLUMN product_suppliers.supply_price IS 'Supplier price for the product';
COMMENT ON COLUMN product_suppliers.lead_time_days IS 'Lead time in days';
COMMENT ON COLUMN product_suppliers.minimum_order_quantity IS 'Minimum order quantity from supplier';

COMMENT ON TABLE inventory IS 'Inventory levels by product and warehouse';
COMMENT ON COLUMN inventory.inventory_id IS 'Primary key';
COMMENT ON COLUMN inventory.product_id IS 'Product reference';
COMMENT ON COLUMN inventory.warehouse_id IS 'Warehouse reference';
COMMENT ON COLUMN inventory.quantity IS 'Available quantity';
COMMENT ON COLUMN inventory.reserved_quantity IS 'Quantity reserved for orders';
COMMENT ON COLUMN inventory.last_restocked IS 'Timestamp of last restock';

COMMENT ON TABLE customers IS 'Customer profiles and contact details';
COMMENT ON COLUMN customers.customer_id IS 'Primary key';
COMMENT ON COLUMN customers.first_name IS 'First name';
COMMENT ON COLUMN customers.last_name IS 'Last name';
COMMENT ON COLUMN customers.email IS 'Customer email (unique)';
COMMENT ON COLUMN customers.phone IS 'Customer phone';
COMMENT ON COLUMN customers.country IS 'Customer country';
COMMENT ON COLUMN customers.city IS 'Customer city';
COMMENT ON COLUMN customers.address IS 'Customer address';
COMMENT ON COLUMN customers.registration_date IS 'When the customer registered';
COMMENT ON COLUMN customers.loyalty_points IS 'Loyalty points balance';

COMMENT ON TABLE orders IS 'Orders placed by customers';
COMMENT ON COLUMN orders.order_id IS 'Primary key';
COMMENT ON COLUMN orders.customer_id IS 'Customer reference';
COMMENT ON COLUMN orders.order_date IS 'Order date/time';
COMMENT ON COLUMN orders.status IS 'Order status';
COMMENT ON COLUMN orders.total_amount IS 'Order total amount';
COMMENT ON COLUMN orders.shipping_address IS 'Shipping address';
COMMENT ON COLUMN orders.shipping_city IS 'Shipping city';
COMMENT ON COLUMN orders.shipping_country IS 'Shipping country';
COMMENT ON COLUMN orders.warehouse_id IS 'Fulfilling warehouse';
COMMENT ON COLUMN orders.shipped_date IS 'When the order shipped';
COMMENT ON COLUMN orders.delivered_date IS 'When the order was delivered';

COMMENT ON TABLE order_items IS 'Line items within orders';
COMMENT ON COLUMN order_items.order_item_id IS 'Primary key';
COMMENT ON COLUMN order_items.order_id IS 'Order reference';
COMMENT ON COLUMN order_items.product_id IS 'Product reference';
COMMENT ON COLUMN order_items.quantity IS 'Quantity ordered';
COMMENT ON COLUMN order_items.unit_price IS 'Unit price at order time';
COMMENT ON COLUMN order_items.discount_percent IS 'Discount percent applied';
COMMENT ON COLUMN order_items.subtotal IS 'Line subtotal after discount';

COMMENT ON TABLE product_reviews IS 'Customer reviews for products';
COMMENT ON COLUMN product_reviews.review_id IS 'Primary key';
COMMENT ON COLUMN product_reviews.product_id IS 'Product reference';
COMMENT ON COLUMN product_reviews.customer_id IS 'Customer reference';
COMMENT ON COLUMN product_reviews.rating IS 'Star rating 1-5';
COMMENT ON COLUMN product_reviews.title IS 'Review title';
COMMENT ON COLUMN product_reviews.comment IS 'Review body text';
COMMENT ON COLUMN product_reviews.review_date IS 'When the review was posted';
COMMENT ON COLUMN product_reviews.verified_purchase IS 'Whether the review is from a verified purchase';
COMMENT ON COLUMN product_reviews.helpful_count IS 'Helpful vote count';

COMMENT ON TABLE shipments IS 'Shipment tracking for orders';
COMMENT ON COLUMN shipments.shipment_id IS 'Primary key';
COMMENT ON COLUMN shipments.order_id IS 'Order reference';
COMMENT ON COLUMN shipments.carrier IS 'Shipping carrier';
COMMENT ON COLUMN shipments.tracking_number IS 'Carrier tracking number';
COMMENT ON COLUMN shipments.shipped_date IS 'When the shipment left the warehouse';
COMMENT ON COLUMN shipments.estimated_delivery IS 'Estimated delivery date';
COMMENT ON COLUMN shipments.actual_delivery IS 'Actual delivery date';
COMMENT ON COLUMN shipments.status IS 'Current shipment status';

-- Insert categories
INSERT INTO categories (name, description, parent_category_id) VALUES
('Electronics', 'Electronic devices and gadgets', NULL),
('Computers', 'Computer hardware and accessories', 1),
('Mobile Devices', 'Smartphones and tablets', 1),
('Home & Garden', 'Home improvement and garden supplies', NULL),
('Furniture', 'Indoor and outdoor furniture', 4),
('Sports & Outdoors', 'Sports equipment and outdoor gear', NULL),
('Books', 'Books and literature', NULL),
('Clothing', 'Apparel and fashion', NULL);

-- Insert manufacturers
INSERT INTO manufacturers (name, country, founded_year, website, description) VALUES
('TechCorp Industries', 'USA', 1995, 'www.techcorp.com', 'Leading technology manufacturer'),
('GlobalTech Ltd', 'China', 2001, 'www.globaltech.cn', 'Electronics and components manufacturer'),
('EuroManufacturing GmbH', 'Germany', 1987, 'www.euromanuf.de', 'Premium quality products'),
('AsianElectronics Inc', 'Japan', 1992, 'www.asianelec.jp', 'Innovative electronics producer'),
('AmericanGoods Co', 'USA', 2005, 'www.americangoods.com', 'Domestic products manufacturer'),
('SwissQuality AG', 'Switzerland', 1978, 'www.swissquality.ch', 'High-end precision products'),
('ItalianDesign SPA', 'Italy', 1990, 'www.italiandesign.it', 'Fashion and furniture'),
('BritishMade Ltd', 'UK', 1985, 'www.britishmade.co.uk', 'Traditional craftsmanship'),
('CanadianSupply Inc', 'Canada', 2000, 'www.canadiansupply.ca', 'Outdoor and sports equipment'),
('AustralianProd Pty', 'Australia', 2010, 'www.australianprod.com.au', 'Diverse product range');

-- Insert suppliers
INSERT INTO suppliers (name, contact_email, contact_phone, country, city, rating, active) VALUES
('TechSupply Co', 'contact@techsupply.com', '+1-555-0101', 'USA', 'New York', 4.5, TRUE),
('GlobalElectronics Ltd', 'info@globalelectronics.com', '+86-555-0102', 'China', 'Shenzhen', 4.2, TRUE),
('EuroGoods GmbH', 'sales@eurogoods.de', '+49-555-0103', 'Germany', 'Berlin', 4.8, TRUE),
('AsianManufacturing Inc', 'orders@asianmfg.com', '+81-555-0104', 'Japan', 'Tokyo', 4.3, TRUE),
('LocalSuppliers LLC', 'hello@localsuppliers.com', '+1-555-0105', 'USA', 'Los Angeles', 4.0, TRUE),
('PacificTrade Co', 'sales@pacifictrade.com', '+61-555-0106', 'Australia', 'Sydney', 4.6, TRUE),
('NordicSupply AB', 'info@nordicsupply.se', '+46-555-0107', 'Sweden', 'Stockholm', 4.7, TRUE),
('LatinAmerica Dist', 'ventas@latam-dist.com', '+55-555-0108', 'Brazil', 'São Paulo', 3.9, TRUE);

-- Insert warehouses
INSERT INTO warehouses (name, country, city, address, capacity, manager_name) VALUES
('North American Hub', 'USA', 'Chicago', '123 Warehouse Ave', 50000, 'John Smith'),
('European Center', 'Germany', 'Hamburg', '456 Logistics Str', 40000, 'Hans Mueller'),
('Asian Distribution', 'China', 'Shanghai', '789 Trade Rd', 60000, 'Li Wei'),
('UK Fulfillment', 'UK', 'London', '321 Storage Lane', 35000, 'James Brown'),
('West Coast Center', 'USA', 'Seattle', '654 Depot Blvd', 45000, 'Sarah Johnson');

-- Generate 50,000 products dynamically with category-specific naming and attributes
DO $$
DECLARE
    i INTEGER;
    manufacturer_count INTEGER;

    -- Current product config variables
    prefixes TEXT[];
    suffixes TEXT[];
    price_min DECIMAL;
    price_max DECIMAL;
    weight_min DECIMAL;
    weight_max DECIMAL;
    descriptions TEXT[];

    random_name TEXT;
    random_desc TEXT;
    random_price DECIMAL(10,2);
    random_stock INTEGER;
    random_manufacturer INTEGER;
    random_sku TEXT;
    random_weight DECIMAL(8,2);
    products_per_category INTEGER;
    current_category INTEGER;
BEGIN
    SELECT COUNT(*) INTO manufacturer_count FROM manufacturers;
    products_per_category := 6250; -- 50000 / 8 categories

    -- Generate products for each category
    FOR current_category IN 1..8 LOOP
        -- Configure based on category
        CASE current_category
            WHEN 1 THEN -- Electronics
                prefixes := ARRAY['Smart', 'Digital', 'Wireless', 'LED', 'Electronic', 'Power'];
                suffixes := ARRAY['Display', 'Device', 'System', 'Unit', 'Module', 'Controller'];
                price_min := 29.99; price_max := 999.99;
                weight_min := 0.1; weight_max := 5.0;
                descriptions := ARRAY['High-quality electronics with advanced features', 'Modern electronic device for everyday use'];
            WHEN 2 THEN -- Computers
                prefixes := ARRAY['Pro', 'Elite', 'Gaming', 'Ultra', 'Performance', 'Business'];
                suffixes := ARRAY['Laptop', 'Desktop', 'Monitor', 'Keyboard', 'Mouse', 'Storage', 'Graphics', 'Processor'];
                price_min := 49.99; price_max := 2999.99;
                weight_min := 0.15; weight_max := 8.0;
                descriptions := ARRAY['High-performance computing hardware', 'Professional-grade computer equipment'];
            WHEN 3 THEN -- Mobile Devices
                prefixes := ARRAY['Smart', 'Pro', 'Max', 'Plus', 'Ultra', 'Mini'];
                suffixes := ARRAY['Phone', 'Tablet', 'Watch', 'Earbuds', 'Speaker', 'Charger', 'Case', 'Accessory'];
                price_min := 19.99; price_max := 1299.99;
                weight_min := 0.05; weight_max := 0.8;
                descriptions := ARRAY['Latest mobile technology', 'Portable and convenient device'];
            WHEN 4 THEN -- Home & Garden
                prefixes := ARRAY['Garden', 'Home', 'Outdoor', 'Indoor', 'Patio', 'Kitchen'];
                suffixes := ARRAY['Tool', 'Set', 'Kit', 'Organizer', 'Storage', 'Decor', 'Appliance'];
                price_min := 24.99; price_max := 499.99;
                weight_min := 0.5; weight_max := 25.0;
                descriptions := ARRAY['Quality home and garden product', 'Durable and practical solution'];
            WHEN 5 THEN -- Furniture
                prefixes := ARRAY['Modern', 'Classic', 'Deluxe', 'Premium', 'Contemporary', 'Traditional'];
                suffixes := ARRAY['Chair', 'Desk', 'Table', 'Sofa', 'Shelf', 'Cabinet', 'Stand', 'Lamp'];
                price_min := 79.99; price_max := 1999.99;
                weight_min := 5.0; weight_max := 50.0;
                descriptions := ARRAY['Stylish and comfortable furniture', 'High-quality craftsmanship'];
            WHEN 6 THEN -- Sports & Outdoors
                prefixes := ARRAY['Pro', 'Elite', 'Training', 'Performance', 'Outdoor', 'Fitness'];
                suffixes := ARRAY['Equipment', 'Gear', 'Apparel', 'Bag', 'Mat', 'Ball', 'Racket', 'Kit'];
                price_min := 19.99; price_max := 899.99;
                weight_min := 0.2; weight_max := 15.0;
                descriptions := ARRAY['Professional sports equipment', 'High-performance gear for athletes'];
            WHEN 7 THEN -- Books
                prefixes := ARRAY['Complete', 'Essential', 'Advanced', 'Beginner', 'Master', 'Illustrated'];
                suffixes := ARRAY['Guide', 'Handbook', 'Manual', 'Reference', 'Series', 'Collection', 'Novel', 'Encyclopedia'];
                price_min := 14.99; price_max := 89.99;
                weight_min := 0.3; weight_max := 2.0;
                descriptions := ARRAY['Comprehensive and informative', 'Essential reading material'];
            WHEN 8 THEN -- Clothing
                prefixes := ARRAY['Premium', 'Classic', 'Modern', 'Casual', 'Formal', 'Sport'];
                suffixes := ARRAY['Shirt', 'Pants', 'Jacket', 'Shoes', 'Hat', 'Accessory', 'Wear', 'Outfit'];
                price_min := 19.99; price_max := 299.99;
                weight_min := 0.1; weight_max := 2.0;
                descriptions := ARRAY['Comfortable and stylish clothing', 'High-quality fabric and design'];
        END CASE;

        FOR i IN 1..products_per_category LOOP
            random_name := prefixes[1 + floor(random() * array_length(prefixes, 1))] || ' ' ||
                          suffixes[1 + floor(random() * array_length(suffixes, 1))] || ' ' ||
                          ((current_category - 1) * products_per_category + i)::TEXT;

            random_desc := descriptions[1 + floor(random() * array_length(descriptions, 1))];
            random_price := (random() * (price_max - price_min) + price_min)::DECIMAL(10,2);
            random_stock := floor(random() * 300 + 1)::INTEGER;
            random_manufacturer := floor(random() * manufacturer_count + 1)::INTEGER;
            random_sku := 'CAT' || current_category || '-' || LPAD(i::TEXT, 6, '0');
            random_weight := (random() * (weight_max - weight_min) + weight_min)::DECIMAL(8,2);

            INSERT INTO products (name, description, price, stock_quantity, category_id, manufacturer_id, sku, weight_kg)
            VALUES (random_name, random_desc, random_price, random_stock, current_category, random_manufacturer, random_sku, random_weight);
        END LOOP;
    END LOOP;
END $$;

-- Generate product attributes dynamically (10-15% of products get attributes)
DO $$
DECLARE
    i INTEGER;
    max_product_id INTEGER;
    product_category INTEGER;
    attr_count INTEGER;

    colors TEXT[] := ARRAY['Black', 'White', 'Silver', 'Blue', 'Red', 'Gray', 'Green', 'Gold'];
    materials TEXT[] := ARRAY['Plastic', 'Metal', 'Wood', 'Leather', 'Fabric', 'Glass', 'Aluminum', 'Steel'];
    sizes TEXT[] := ARRAY['Small', 'Medium', 'Large', 'XL', 'XXL'];
    warranties TEXT[] := ARRAY['1 Year', '2 Years', '3 Years', '5 Years', 'Lifetime'];
BEGIN
    SELECT MAX(product_id) INTO max_product_id FROM products;

    -- Add attributes to every 8th product
    FOR i IN 1..max_product_id BY 8 LOOP
        SELECT category_id INTO product_category FROM products WHERE product_id = i;
        attr_count := floor(random() * 3 + 2)::INTEGER; -- 2-4 attributes per product

        -- Add color attribute
        INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
        VALUES (i, 'Color', colors[1 + floor(random() * array_length(colors, 1))]);

        -- Category-specific attributes
        IF product_category IN (1, 2, 3) THEN -- Electronics, Computers, Mobile
            INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
            VALUES (i, 'Warranty', warranties[1 + floor(random() * array_length(warranties, 1))]);

            IF random() > 0.5 THEN
                INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
                VALUES (i, 'Power', (floor(random() * 200 + 20)::TEXT) || 'W');
            END IF;
        ELSIF product_category IN (5, 4) THEN -- Furniture, Home & Garden
            INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
            VALUES (i, 'Material', materials[1 + floor(random() * array_length(materials, 1))]);

            IF random() > 0.5 THEN
                INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
                VALUES (i, 'Dimensions', (floor(random() * 50 + 20)::TEXT) || 'x' ||
                                        (floor(random() * 50 + 20)::TEXT) || 'x' ||
                                        (floor(random() * 50 + 20)::TEXT) || ' cm');
            END IF;
        ELSIF product_category = 6 THEN -- Sports
            INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
            VALUES (i, 'Size', sizes[1 + floor(random() * array_length(sizes, 1))]);
        ELSIF product_category = 7 THEN -- Books
            INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
            VALUES (i, 'Pages', (floor(random() * 800 + 100)::TEXT));

            IF random() > 0.5 THEN
                INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
                VALUES (i, 'Publisher', 'Publisher ' || (floor(random() * 20 + 1)::TEXT));
            END IF;
        ELSIF product_category = 8 THEN -- Clothing
            INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
            VALUES (i, 'Size', sizes[1 + floor(random() * array_length(sizes, 1))]);

            INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
            VALUES (i, 'Material', materials[1 + floor(random() * array_length(materials, 1))]);
        END IF;
    END LOOP;
END $$;

-- Generate product-supplier relationships (20% of products have suppliers)
DO $$
DECLARE
    i INTEGER;
    max_product_id INTEGER;
    supplier_count INTEGER;
    random_supplier INTEGER;
    random_supply_price DECIMAL(10,2);
    product_price DECIMAL(10,2);
    suppliers_per_product INTEGER;
    j INTEGER;
BEGIN
    SELECT MAX(product_id) INTO max_product_id FROM products;
    SELECT COUNT(*) INTO supplier_count FROM suppliers;

    FOR i IN 1..max_product_id BY 5 LOOP
        SELECT price INTO product_price FROM products WHERE product_id = i;
        suppliers_per_product := CASE
            WHEN random() > 0.7 THEN 2  -- 30% chance of 2 suppliers
            ELSE 1                       -- 70% chance of 1 supplier
        END;

        FOR j IN 1..suppliers_per_product LOOP
            random_supplier := floor(random() * supplier_count + 1)::INTEGER;
            -- Supply price is 50-75% of retail price
            random_supply_price := (product_price * (0.5 + random() * 0.25))::DECIMAL(10,2);

            INSERT INTO product_suppliers (product_id, supplier_id, supply_price, lead_time_days, minimum_order_quantity)
            VALUES (
                i,
                random_supplier,
                random_supply_price,
                floor(random() * 25 + 5)::INTEGER,  -- Lead time: 5-30 days
                CASE
                    WHEN product_price < 50 THEN floor(random() * 100 + 50)::INTEGER  -- Cheap items: 50-150 MOQ
                    WHEN product_price < 200 THEN floor(random() * 30 + 10)::INTEGER  -- Mid-range: 10-40 MOQ
                    ELSE floor(random() * 10 + 1)::INTEGER                           -- Expensive: 1-10 MOQ
                END
            )
            ON CONFLICT DO NOTHING;
        END LOOP;
    END LOOP;
END $$;

-- Insert customers
INSERT INTO customers (first_name, last_name, email, phone, country, city, address, loyalty_points) VALUES
('John', 'Smith', 'john.smith@email.com', '+1-555-1001', 'USA', 'New York', '123 Main St', 450),
('Maria', 'Garcia', 'maria.garcia@email.com', '+34-555-2001', 'Spain', 'Madrid', '456 Plaza Mayor', 280),
('Chen', 'Wei', 'chen.wei@email.com', '+86-555-3001', 'China', 'Beijing', '789 Wangfujing St', 620),
('Emma', 'Johnson', 'emma.j@email.com', '+44-555-4001', 'UK', 'London', '321 Oxford St', 150),
('Michael', 'Brown', 'mbrown@email.com', '+1-555-1002', 'USA', 'Chicago', '654 Michigan Ave', 890),
('Sophie', 'Martin', 'sophie.m@email.com', '+33-555-5001', 'France', 'Paris', '987 Champs-Élysées', 340),
('Hans', 'Mueller', 'h.mueller@email.com', '+49-555-6001', 'Germany', 'Berlin', '147 Alexanderplatz', 520),
('Yuki', 'Tanaka', 'yuki.t@email.com', '+81-555-7001', 'Japan', 'Tokyo', '258 Shibuya', 410),
('Sarah', 'Wilson', 'swilson@email.com', '+61-555-8001', 'Australia', 'Sydney', '369 George St', 200),
('Carlos', 'Rodriguez', 'carlos.r@email.com', '+52-555-9001', 'Mexico', 'Mexico City', '741 Reforma Ave', 95);

-- Insert inventory records (distribute products across warehouses)
INSERT INTO inventory (product_id, warehouse_id, quantity, reserved_quantity, last_restocked) VALUES
(1, 1, 25, 5, NOW() - INTERVAL '10 days'),
(1, 2, 20, 3, NOW() - INTERVAL '5 days'),
(2, 1, 80, 10, NOW() - INTERVAL '15 days'),
(2, 3, 70, 5, NOW() - INTERVAL '8 days'),
(3, 2, 40, 8, NOW() - INTERVAL '12 days'),
(3, 4, 35, 2, NOW() - INTERVAL '6 days'),
(6, 1, 30, 10, NOW() - INTERVAL '3 days'),
(6, 3, 30, 5, NOW() - INTERVAL '4 days'),
(7, 2, 50, 10, NOW() - INTERVAL '7 days'),
(7, 5, 30, 5, NOW() - INTERVAL '9 days'),
(11, 1, 20, 3, NOW() - INTERVAL '20 days'),
(11, 4, 15, 2, NOW() - INTERVAL '18 days'),
(12, 2, 15, 5, NOW() - INTERVAL '25 days'),
(12, 5, 10, 0, NOW() - INTERVAL '22 days'),
(16, 1, 45, 8, NOW() - INTERVAL '14 days'),
(16, 5, 40, 7, NOW() - INTERVAL '11 days');

-- Insert orders
INSERT INTO orders (customer_id, order_date, status, total_amount, shipping_address, shipping_city, shipping_country, warehouse_id, shipped_date, delivered_date) VALUES
(1, NOW() - INTERVAL '30 days', 'delivered', 1349.98, '123 Main St', 'New York', 'USA', 1, NOW() - INTERVAL '28 days', NOW() - INTERVAL '25 days'),
(2, NOW() - INTERVAL '25 days', 'delivered', 539.98, '456 Plaza Mayor', 'Madrid', 'Spain', 2, NOW() - INTERVAL '23 days', NOW() - INTERVAL '18 days'),
(3, NOW() - INTERVAL '20 days', 'delivered', 1799.97, '789 Wangfujing St', 'Beijing', 'China', 3, NOW() - INTERVAL '18 days', NOW() - INTERVAL '14 days'),
(4, NOW() - INTERVAL '15 days', 'shipped', 179.97, '321 Oxford St', 'London', 'UK', 4, NOW() - INTERVAL '13 days', NULL),
(5, NOW() - INTERVAL '12 days', 'delivered', 299.99, '654 Michigan Ave', 'Chicago', 'USA', 1, NOW() - INTERVAL '10 days', NOW() - INTERVAL '7 days'),
(1, NOW() - INTERVAL '10 days', 'delivered', 89.99, '123 Main St', 'New York', 'USA', 1, NOW() - INTERVAL '8 days', NOW() - INTERVAL '5 days'),
(6, NOW() - INTERVAL '8 days', 'processing', 1299.99, '987 Champs-Élysées', 'Paris', 'France', 2, NULL, NULL),
(7, NOW() - INTERVAL '5 days', 'pending', 449.99, '147 Alexanderplatz', 'Berlin', 'Germany', 2, NULL, NULL),
(8, NOW() - INTERVAL '3 days', 'delivered', 679.97, '258 Shibuya', 'Tokyo', 'Japan', 3, NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day'),
(9, NOW() - INTERVAL '2 days', 'shipped', 229.98, '369 George St', 'Sydney', 'Australia', 5, NOW() - INTERVAL '1 day', NULL);

-- Insert order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_percent, subtotal) VALUES
(1, 1, 1, 1299.99, 0, 1299.99),
(1, 2, 1, 29.99, 0, 29.99),
(1, 4, 1, 49.99, 10, 44.99),
(2, 7, 1, 449.99, 0, 449.99),
(2, 3, 1, 89.99, 0, 89.99),
(3, 1, 1, 1299.99, 5, 1234.99),
(3, 6, 1, 899.99, 10, 809.99),
(3, 8, 2, 149.99, 15, 254.99),
(4, 16, 1, 129.99, 0, 129.99),
(4, 2, 1, 29.99, 0, 29.99),
(4, 9, 1, 19.99, 0, 19.99),
(5, 11, 1, 299.99, 0, 299.99),
(6, 3, 1, 89.99, 0, 89.99),
(7, 1, 1, 1299.99, 0, 1299.99),
(8, 7, 1, 449.99, 0, 449.99),
(9, 6, 1, 899.99, 0, 899.99),
(9, 8, 1, 149.99, 0, 149.99),
(10, 16, 1, 129.99, 0, 129.99),
(10, 17, 2, 34.99, 10, 62.98),
(10, 18, 1, 159.99, 20, 127.99);

-- Insert product reviews
INSERT INTO product_reviews (product_id, customer_id, rating, title, comment, review_date, verified_purchase, helpful_count) VALUES
(1, 1, 5, 'Excellent laptop!', 'Best laptop I have ever owned. Fast, reliable, and great build quality.', NOW() - INTERVAL '20 days', TRUE, 12),
(1, 3, 4, 'Good but expensive', 'Great performance but the price is a bit high. Still worth it though.', NOW() - INTERVAL '10 days', TRUE, 8),
(2, 1, 5, 'Perfect mouse', 'Ergonomic and responsive. Highly recommend!', NOW() - INTERVAL '5 days', TRUE, 5),
(3, 2, 5, 'Amazing keyboard', 'The mechanical switches are perfect. Love the RGB lighting.', NOW() - INTERVAL '15 days', TRUE, 15),
(6, 3, 4, 'Great phone', 'Fast processor and excellent camera. Battery life could be better.', NOW() - INTERVAL '12 days', TRUE, 10),
(7, 9, 5, 'Love this tablet', 'Perfect size and the stylus support is fantastic for drawing.', NOW() - INTERVAL '1 day', TRUE, 2),
(8, 3, 5, 'Best earbuds', 'Sound quality is amazing and noise cancellation works perfectly.', NOW() - INTERVAL '8 days', TRUE, 18),
(11, 5, 4, 'Comfortable chair', 'Very comfortable for long work sessions. Assembly took some time.', NOW() - INTERVAL '4 days', TRUE, 6),
(16, 4, 5, 'Professional quality', 'These running shoes are perfect for training. Great support!', NOW() - INTERVAL '10 days', TRUE, 9),
(17, 10, 5, 'Best yoga mat', 'Non-slip surface works great. Very durable.', NOW() - INTERVAL '25 days', TRUE, 14);

-- Insert shipments
INSERT INTO shipments (order_id, carrier, tracking_number, shipped_date, estimated_delivery, actual_delivery, status) VALUES
(1, 'FedEx', 'FDX123456789', NOW() - INTERVAL '28 days', NOW() - INTERVAL '25 days', NOW() - INTERVAL '25 days', 'delivered'),
(2, 'DHL', 'DHL987654321', NOW() - INTERVAL '23 days', NOW() - INTERVAL '18 days', NOW() - INTERVAL '18 days', 'delivered'),
(3, 'UPS', 'UPS456789123', NOW() - INTERVAL '18 days', NOW() - INTERVAL '14 days', NOW() - INTERVAL '14 days', 'delivered'),
(4, 'DHL', 'DHL111222333', NOW() - INTERVAL '13 days', NOW() - INTERVAL '8 days', NULL, 'in_transit'),
(5, 'FedEx', 'FDX999888777', NOW() - INTERVAL '10 days', NOW() - INTERVAL '7 days', NOW() - INTERVAL '7 days', 'delivered'),
(6, 'FedEx', 'FDX777666555', NOW() - INTERVAL '8 days', NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days', 'delivered'),
(9, 'UPS', 'UPS222333444', NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day', 'delivered'),
(10, 'DHL', 'DHL444555666', NOW() - INTERVAL '1 day', NOW() + INTERVAL '3 days', NULL, 'in_transit');

-- Generate inventory records (30% of products distributed across warehouses)
DO $$
DECLARE
    i INTEGER;
    max_product_id INTEGER;
    warehouse_count INTEGER;
    warehouses_per_product INTEGER;
    j INTEGER;
    random_warehouse INTEGER;
    total_stock INTEGER;
    warehouse_qty INTEGER;
BEGIN
    SELECT MAX(product_id) INTO max_product_id FROM products;
    SELECT COUNT(*) INTO warehouse_count FROM warehouses;

    FOR i IN 1..max_product_id BY 3 LOOP
        SELECT stock_quantity INTO total_stock FROM products WHERE product_id = i;
        warehouses_per_product := CASE
            WHEN random() > 0.7 THEN 2  -- 30% in 2 warehouses
            WHEN random() > 0.9 THEN 3  -- 10% in 3 warehouses
            ELSE 1                       -- 60% in 1 warehouse
        END;

        FOR j IN 1..warehouses_per_product LOOP
            random_warehouse := floor(random() * warehouse_count + 1)::INTEGER;
            warehouse_qty := CASE
                WHEN warehouses_per_product = 1 THEN total_stock
                ELSE floor(total_stock / warehouses_per_product)::INTEGER
            END;

            INSERT INTO inventory (product_id, warehouse_id, quantity, reserved_quantity, last_restocked)
            VALUES (
                i,
                random_warehouse,
                warehouse_qty,
                floor(warehouse_qty * random() * 0.2)::INTEGER, -- 0-20% reserved
                NOW() - (floor(random() * 90)::TEXT || ' days')::INTERVAL
            )
            ON CONFLICT (product_id, warehouse_id) DO NOTHING;
        END LOOP;
    END LOOP;
END $$;

-- Generate more customers (2,500 total)
DO $$
DECLARE
    i INTEGER;
    first_names TEXT[] := ARRAY['John', 'Maria', 'Chen', 'Emma', 'Michael', 'Sophie', 'Hans', 'Yuki', 'Sarah', 'Carlos',
                                 'Anna', 'David', 'Laura', 'Ahmed', 'Olivia', 'Pierre', 'Mei', 'Lucas', 'Nina', 'Alex'];
    last_names TEXT[] := ARRAY['Smith', 'Garcia', 'Wei', 'Johnson', 'Brown', 'Martin', 'Mueller', 'Tanaka', 'Wilson', 'Rodriguez',
                               'Lee', 'Kim', 'Patel', 'Nguyen', 'Silva', 'Cohen', 'Ali', 'Jones', 'Anderson', 'Taylor'];
    countries TEXT[] := ARRAY['USA', 'Spain', 'China', 'UK', 'Germany', 'France', 'Japan', 'Australia', 'Canada', 'Brazil'];
    cities TEXT[] := ARRAY['New York', 'Madrid', 'Beijing', 'London', 'Berlin', 'Paris', 'Tokyo', 'Sydney', 'Toronto', 'São Paulo'];
BEGIN
    FOR i IN 11..2500 LOOP
        INSERT INTO customers (first_name, last_name, email, phone, country, city, address, loyalty_points)
        VALUES (
            first_names[1 + floor(random() * array_length(first_names, 1))],
            last_names[1 + floor(random() * array_length(last_names, 1))],
            'customer' || i || '@email.com',
            '+' || (floor(random() * 90 + 10)::TEXT) || '-555-' || LPAD((floor(random() * 9999)::TEXT), 4, '0'),
            countries[1 + floor(random() * array_length(countries, 1))],
            cities[1 + floor(random() * array_length(cities, 1))],
            (floor(random() * 999 + 1)::TEXT) || ' Random St',
            floor(random() * 1000)::INTEGER
        );
    END LOOP;
END $$;

-- Generate more orders (10,000 total)
DO $$
DECLARE
    i INTEGER;
    random_customer INTEGER;
    random_warehouse INTEGER;
    random_status TEXT;
    statuses TEXT[] := ARRAY['pending', 'processing', 'shipped', 'delivered', 'cancelled'];
    random_days INTEGER;
    order_total DECIMAL(12,2);
BEGIN
    FOR i IN 11..10000 LOOP
        random_customer := floor(random() * 2500 + 1)::INTEGER;
        random_warehouse := floor(random() * 5 + 1)::INTEGER;
        random_status := statuses[1 + floor(random() * array_length(statuses, 1))];
        random_days := floor(random() * 90)::INTEGER;
        order_total := (random() * 2000 + 50)::DECIMAL(12,2);

        INSERT INTO orders (customer_id, order_date, status, total_amount, shipping_address, shipping_city, shipping_country, warehouse_id, shipped_date, delivered_date)
        VALUES (
            random_customer,
            NOW() - (random_days || ' days')::INTERVAL,
            random_status,
            order_total,
            (floor(random() * 999 + 1)::TEXT) || ' Customer Address',
            'City' || floor(random() * 100)::TEXT,
            'Country' || floor(random() * 50)::TEXT,
            random_warehouse,
            CASE WHEN random_status IN ('shipped', 'delivered') THEN NOW() - ((random_days - 2) || ' days')::INTERVAL ELSE NULL END,
            CASE WHEN random_status = 'delivered' THEN NOW() - ((random_days - 5) || ' days')::INTERVAL ELSE NULL END
        );
    END LOOP;
END $$;

DO $$
DECLARE
    i INTEGER;
    j INTEGER;
    items_count INTEGER;
    max_product_id INTEGER;
    random_product INTEGER;
    random_quantity INTEGER;
    product_price DECIMAL(10,2);
    random_discount DECIMAL(5,2);
BEGIN
    SELECT MAX(product_id) INTO max_product_id FROM products;

    FOR i IN 11..10000 LOOP
        items_count := floor(random() * 4 + 1)::INTEGER; -- 1 to 5 items per order

        FOR j IN 1..items_count LOOP
            random_product := floor(random() * max_product_id + 1)::INTEGER;
            random_quantity := floor(random() * 3 + 1)::INTEGER; -- 1 to 4 quantity
            SELECT price INTO product_price FROM products WHERE product_id = random_product;
            random_discount := floor(random() * 20)::DECIMAL(5,2); -- 0 to 20% discount

            IF product_price IS NOT NULL THEN
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_percent, subtotal)
                VALUES (
                    i,
                    random_product,
                    random_quantity,
                    product_price,
                    random_discount,
                    (product_price * random_quantity * (1 - random_discount / 100))::DECIMAL(12,2)
                );
            END IF;
        END LOOP;
    END LOOP;
END $$;

-- Generate product reviews (25,000 reviews)
DO $$
DECLARE
    i INTEGER;
    max_product_id INTEGER;
    max_customer_id INTEGER;
    random_product INTEGER;
    random_customer INTEGER;
    random_rating INTEGER;
    random_days INTEGER;
    titles TEXT[] := ARRAY['Great product!', 'Excellent quality', 'Good value', 'Disappointed', 'Amazing!',
                          'Worth the price', 'Not bad', 'Highly recommend', 'Poor quality', 'Just okay'];
    comments TEXT[] := ARRAY['Really happy with this purchase', 'Exceeded my expectations', 'Good for the price',
                            'Not what I expected', 'Best purchase ever', 'Would buy again', 'Could be better',
                            'Exactly as described', 'Waste of money', 'Decent product'];
BEGIN
    SELECT MAX(product_id) INTO max_product_id FROM products;
    SELECT MAX(customer_id) INTO max_customer_id FROM customers;

    FOR i IN 1..25000 LOOP
        random_product := floor(random() * max_product_id + 1)::INTEGER;
        random_customer := floor(random() * max_customer_id + 1)::INTEGER;
        random_rating := floor(random() * 5 + 1)::INTEGER;
        random_days := floor(random() * 180)::INTEGER;

        INSERT INTO product_reviews (product_id, customer_id, rating, title, comment, review_date, verified_purchase, helpful_count)
        VALUES (
            random_product,
            random_customer,
            random_rating,
            titles[1 + floor(random() * array_length(titles, 1))],
            comments[1 + floor(random() * array_length(comments, 1))],
            NOW() - (random_days || ' days')::INTERVAL,
            random() > 0.3, -- 70% verified purchases
            floor(random() * 50)::INTEGER
        )
        ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

-- Create indexes for better query performance
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_manufacturer ON products(manufacturer_id);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_product_attributes_product ON product_attributes(product_id);
CREATE INDEX idx_product_suppliers_product ON product_suppliers(product_id);
CREATE INDEX idx_product_suppliers_supplier ON product_suppliers(supplier_id);
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_reviews_product ON product_reviews(product_id);
CREATE INDEX idx_reviews_customer ON product_reviews(customer_id);
CREATE INDEX idx_reviews_rating ON product_reviews(rating);
CREATE INDEX idx_shipments_order ON shipments(order_id);

-- Add foreign key constraints with proper names for better documentation
ALTER TABLE products ADD CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(category_id);
ALTER TABLE products ADD CONSTRAINT fk_products_manufacturer FOREIGN KEY (manufacturer_id) REFERENCES manufacturers(manufacturer_id);
ALTER TABLE categories ADD CONSTRAINT fk_categories_parent FOREIGN KEY (parent_category_id) REFERENCES categories(category_id);
