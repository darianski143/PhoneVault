DROP PROCEDURE IF EXISTS create_sale_order;

CREATE PROCEDURE create_sale_order(
    IN p_store_id INT,
    IN p_customer_id INT,
    IN p_sale_date DATE,
    IN p_items_json JSON
)
BEGIN
    DECLARE v_sale_order_id INT;
    DECLARE v_i INT DEFAULT 0;
    DECLARE v_len INT;
    DECLARE v_model_name VARCHAR(100);
    DECLARE v_quantity INT;
    DECLARE v_phone_id INT;
    DECLARE v_unit_price DECIMAL(10,2);
    DECLARE v_stock INT;
    DECLARE v_line_total DECIMAL(10,2);

    INSERT INTO sale_orders (store_id, customer_id, sale_date)
    VALUES (p_store_id, p_customer_id, p_sale_date);

    SET v_sale_order_id = LAST_INSERT_ID();

    SET v_len = JSON_LENGTH(p_items_json);

    WHILE v_i < v_len DO
        SET v_model_name = JSON_UNQUOTE(
            JSON_EXTRACT(p_items_json, CONCAT('$[', v_i, '].model_name'))
        );

        SET v_quantity = JSON_EXTRACT(
            p_items_json, CONCAT('$[', v_i, '].quantity')
        );

        SELECT id, price, stock
        INTO v_phone_id, v_unit_price, v_stock
        FROM phones
        WHERE model_name = v_model_name
        LIMIT 1;

        IF v_phone_id IS NULL THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Telefon inexistent.';
        END IF;

        IF v_quantity <= 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cantitatea trebuie sa fie pozitiva.';
        END IF;

        IF v_stock < v_quantity THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Stoc insuficient pentru telefonul selectat.';
        END IF;

        SET v_line_total = v_unit_price * v_quantity;

        INSERT INTO sale_order_items (
            sale_order_id,
            phone_id,
            quantity,
            unit_price,
            line_total
        )
        VALUES (
            v_sale_order_id,
            v_phone_id,
            v_quantity,
            v_unit_price,
            v_line_total
        );

        UPDATE phones
        SET stock = stock - v_quantity
        WHERE id = v_phone_id;

        SET v_i = v_i + 1;
    END WHILE;

    SELECT v_sale_order_id AS sale_order_id;
END;

-- PROC_END