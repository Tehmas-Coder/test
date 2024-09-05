import mysql.connector

# Database configuration
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "psychometricdb"
DB_USERNAME = "root"
DB_PASSWORD = "root"

# Connect to the database
cnx = mysql.connector.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD)

# Create a cursor object
cursor = cnx.cursor()


# Function to update fields and change their data type
def update_fields_and_change_data_type(cnx, cursor):
    try:
        # Fetch all table names from the database
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (DB_NAME,))
        tables = cursor.fetchall()

        # Loop through all the tables and perform the operations
        for (table_name,) in tables:
            try:

                # Step 2: Alter the table to allow NULL in created_by and updated_by
                alter_query = f"""
                    ALTER TABLE `{table_name}`
                    MODIFY COLUMN `created_by` VARCHAR(255) NULL,
                    MODIFY COLUMN `updated_by` VARCHAR(255) NULL;
                """
                cursor.execute(alter_query)

                # Step 1: Set any invalid values in created_by and updated_by to NULL
                update_query = f"""
                    UPDATE `{table_name}`
                    SET created_by = NULL
                    WHERE created_by IS NOT NULL AND created_by NOT REGEXP '^[0-9]+$';
                """
                cursor.execute(update_query)

                update_query = f"""
                    UPDATE `{table_name}`
                    SET updated_by = NULL
                    WHERE updated_by IS NOT NULL AND updated_by NOT REGEXP '^[0-9]+$';
                """
                cursor.execute(update_query)

                # Step 3: Now change the data type of created_by and updated_by to INT UNSIGNED
                alter_to_int_query = f"""
                    ALTER TABLE `{table_name}`
                    MODIFY COLUMN `created_by` INT NULL,
                    MODIFY COLUMN `updated_by` INT NULL;
                """
                cursor.execute(alter_to_int_query)

                print(f"Successfully updated and modified table: {table_name}")
            except mysql.connector.Error as err:
                print(f"Error updating table {table_name}: {err}")

        # Commit the changes after processing all tables
        cnx.commit()
        print("All tables updated and modified successfully!")
    except mysql.connector.Error as err:
        print("Error:", err)
    finally:
        cnx.close()


# Execute the function to perform the operations
update_fields_and_change_data_type(cnx, cursor)
