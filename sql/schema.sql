CREATE TABLE IF NOT EXISTS brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(100) NOT NULL
);
CREATE TABLE IF NOT EXISTS stores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL
);
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(20) NOT NULL
);
CREATE TABLE IF NOT EXISTS phones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    launch_year INT NOT NULL,
    stock INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);
CREATE TABLE IF NOT EXISTS specifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone_id INT NOT NULL UNIQUE,
    os VARCHAR(100) NOT NULL,
    processor VARCHAR(100) NOT NULL,
    ram_gb INT NOT NULL,
    storage_gb INT NOT NULL,
    camera_mp DECIMAL(5,2) NOT NULL,
    battery_mah INT NOT NULL,
    screen_size DECIMAL(4,2) NOT NULL,
    FOREIGN KEY (phone_id) REFERENCES phones(id)
);
CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone_id INT NOT NULL,
    store_id INT NOT NULL,
    customer_id INT NOT NULL,
    sale_date DATE NOT NULL,
    quantity_sold INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (phone_id) REFERENCES phones(id),
    FOREIGN KEY (store_id) REFERENCES stores(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
CREATE TABLE IF NOT EXISTS customer_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);