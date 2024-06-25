from posgres_manager import Client
from private import database_detail


a = Client(**database_detail)


list_of_commands = [

{'query': """
    CREATE TABLE IF NOT EXISTS UserDetail (
    id SERIAL PRIMARY KEY,
    userID BIGINT NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    username VARCHAR(50),
    language VARCHAR(10),
    email VARCHAR(255) DEFAULT NULL,
    phone_number VARCHAR(15) DEFAULT NULL,
    credit BIGINT DEFAULT 0,
    entered_with_refral_link BIGINT DEFAULT NULL,
    number_of_invitations SMALLINT DEFAULT 0,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    referral_link VARCHAR(50),
    membership_status VARCHAR(50),
    discount_code VARCHAR(50),
    CONSTRAINT fk_referral FOREIGN KEY (entered_with_refral_link) REFERENCES UserDetail(userID) ON DELETE CASCADE
);
"""},


{'query': """
    CREATE TABLE IF NOT EXISTS Address (
    addressID SERIAL PRIMARY KEY,
    userID BIGINT NOT NULL,
    address VARCHAR(100) NOT NULL,
    address_name VARCHAR(100),
    score_percent SMALLINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (userID) REFERENCES UserDetail(userID) ON DELETE CASCADE,
    CONSTRAINT unique_user_address UNIQUE (userID, address)
);"""
 },


{'query': """
    CREATE TABLE IF NOT EXISTS Invoice (
    invoiceID SERIAL PRIMARY KEY,
    userID BIGINT NOT NULL,
    course_ID BIGINT,
    discountID SMALLINT DEFAULT NULL,
    amount BIGINT NOT NULL,
    discount BIGINT DEFAULT 0,
    payment_status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50),
    payment_for VARCHAR(50),
    CONSTRAINT fk_user FOREIGN KEY (userID) REFERENCES UserDetail(userID) ON DELETE CASCADE,
    CONSTRAINT fk_course FOREIGN KEY (course_ID) REFERENCES Course(courseID) ON DELETE CASCADE,
    CONSTRAINT fk_discount FOREIGN KEY (discountID) REFERENCES DiscountCode(discountID) ON DELETE CASCADE
);"""},

]

def create():
    a.execute('transaction', list_of_commands)
    # print(result)

# create()
# print(a.execute('transaction', [{'query': 'drop table Address', 'params': None}]))
#