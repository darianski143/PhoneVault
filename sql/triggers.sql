DROP TRIGGER IF EXISTS trg_sales_before_insert;
-- TRIGGER_END

CREATE TRIGGER trg_sales_before_insert
BEFORE INSERT ON sales
FOR EACH ROW
BEGIN
    DECLARE current_stock INT;

    IF NEW.quantity_sold <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cantitatea vanduta trebuie sa fie mai mare decat 0';
    END IF;

    SELECT stock INTO current_stock
    FROM phones
    WHERE id = NEW.phone_id;

    IF NEW.quantity_sold > current_stock THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Stoc insuficient pentru aceasta vanzare';
    END IF;
END
-- TRIGGER_END

DROP TRIGGER IF EXISTS trg_customers_after_update;
-- TRIGGER_END

CREATE TRIGGER trg_customers_after_update
AFTER UPDATE ON customers
FOR EACH ROW
BEGIN
    INSERT INTO customer_log (customer_id, action)
    VALUES (OLD.id, CONCAT('UPDATE CUSTOMER ', OLD.first_name, ' ', OLD.last_name));
END
-- TRIGGER_END