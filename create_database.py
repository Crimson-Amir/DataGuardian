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
    entered_with_referral_link BIGINT DEFAULT NULL,
    number_of_invitations SMALLINT DEFAULT 0,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    referral_link VARCHAR(50),
    membership_status VARCHAR(50),
    discount_code VARCHAR(50),
    CONSTRAINT fk_referral FOREIGN KEY (entered_with_referral_link) REFERENCES UserDetail(userID) ON DELETE CASCADE
);
"""},

{'query': """
    CREATE TABLE IF NOT EXISTS Rank (
    rankID SERIAL PRIMARY KEY,
    rank_name VARCHAR(50) NOT NULL,
    rank_score INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""},

{'query': """
    CREATE TABLE IF NOT EXISTS UserRank (
    userID BIGINT PRIMARY KEY REFERENCES UserDetail(userID) ON DELETE CASCADE,
    rankID SMALLINT REFERENCES Rank(rankID) ON DELETE CASCADE,
    max_allow_ip_register SMALLINT NOT NULL CHECK (max_allow_ip_register >= 0),
    max_country_per_address SMALLINT NOT NULL CHECK (max_allow_ip_register >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""},

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
);"""},

# ------------------------------------------------------------------------------------------

{'query': """
    CREATE TABLE IF NOT EXISTS AddressNotification (
    notifID SERIAL PRIMARY KEY,
    addressID INTEGER NOT NULL,
    userID BIGINT NOT NULL,
    score_percent_notification SMALLINT DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_address FOREIGN KEY (addressID) REFERENCES Address(addressID) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (userID) REFERENCES UserDetail(userID) ON DELETE CASCADE,
    CONSTRAINT score_notif_min_max CHECK (score_percent_notification >= 0 AND score_percent_notification <= 100)
);"""},

{'query': """
    CREATE TABLE IF NOT EXISTS Country (
    countryID SERIAL PRIMARY KEY,
    country_name VARCHAR(50) NOT NULL,
    country_short_name VARCHAR(10),
    city VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""},

{'query': """
    CREATE TABLE IF NOT EXISTS AddressNotification_Country_Relation (
    status BOOLEAN DEFAULT FALSE,
    countryID SMALLINT REFERENCES Country(countryID),
    notifID SMALLINT REFERENCES AddressNotification(notifID),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT country_notif PRIMARY KEY (countryID, notifID)
);"""},

# ------------------------------------------------------------------------------------------

]


init_country = [
    {'query': """
    INSERT INTO Country (country_name, country_short_name, city) VALUES
    ('United Arab Emirates', 'AE', 'Dubai'),
    ('Bulgaria', 'BG', 'Sofia'),
    ('Brazil', 'BR', 'Sao Paulo'),
    ('Switzerland', 'CH', 'Zurich'),
    ('Czechia', 'CZ', 'C.Budejovice'),
    ('Germany', 'DE', 'Nuremberg'),
    ('Germany', 'DE', 'Frankfurt'),
    ('Spain', 'ES', 'Barcelona'),
    ('Finland', 'FI', 'Helsinki'),
    ('France', 'FR', 'Paris'),
    ('Hong Kong', 'HK', 'Hong Kong'),
    ('Croatia', 'HR', 'Sisak'),
    ('Israel', 'IL', 'Tel Aviv'),
    ('Israel', 'IL', 'Netanya'),
    ('India', 'IN', 'Mumbai'),
    ('Iran', 'IR', 'Tehran'),
    ('Iran', 'IR', 'Shiraz'),
    ('Iran', 'IR', 'Esfahan'),
    ('Iran', 'IR', 'Karaj'),
    ('Italy', 'IT', 'Milan'),
    ('Japan', 'JP', 'Tokyo'),
    ('Kazakhstan', 'KZ', 'Karaganda'),
    ('Lithuania', 'LT', 'Vilnius'),
    ('Moldova', 'MD', 'Chisinau'),
    ('Netherlands', 'NL', 'Amsterdam'),
    ('Netherlands', 'NL', 'Meppel'),
    ('Poland', 'PL', 'Poznan'),
    ('Poland', 'PL', 'Warsaw'),
    ('Portugal', 'PT', 'Viana'),
    ('Serbia', 'RS', 'Belgrade'),
    ('Russia', 'RU', 'Moscow'),
    ('Russia', 'RU', 'Saint Petersburg'),
    ('Russia', 'RU', 'Ekaterinburg'),
    ('Sweden', 'SE', 'Tallberg'),
    ('Turkey', 'TR', 'Istanbul'),
    ('Turkey', 'TR', 'Gebze'),
    ('Ukraine', 'UA', 'Khmelnytskyi'),
    ('Ukraine', 'UA', 'Kyiv'),
    ('Ukraine', 'UA', 'SpaceX Starlink'),
    ('United Kingdom', 'GB', 'Coventry'),
    ('United States', 'US', 'Chicago'),
    ('United States', 'US', 'Dallas'),
    ('United States', 'US', 'Atlanta');
    """}
]

init_rank = [
    {'query': """
    INSERT INTO Rank (rank_name,rank_score) VALUES 
    ('ROOKIE', 10)
    """}
]

def create():
    a.execute('transaction', list_of_commands)
    # print(result)

def init():
    a.execute('transaction', init_country)
    # a.execute('transaction', init_rank)

# init()
# create()
# print(a.execute('transaction', [{'query': 'drop table Country', 'params': None}]))
#

# {'query': """
#     CREATE TABLE IF NOT EXISTS Invoice (
#     invoiceID SERIAL PRIMARY KEY,
#     userID BIGINT NOT NULL,
#     course_ID BIGINT,
#     discountID SMALLINT DEFAULT NULL,
#     amount BIGINT NOT NULL,
#     discount BIGINT DEFAULT 0,
#     payment_status VARCHAR(50) NOT NULL,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     payment_method VARCHAR(50),
#     payment_for VARCHAR(50),
#     CONSTRAINT fk_user FOREIGN KEY (userID) REFERENCES UserDetail(userID) ON DELETE CASCADE,
#     -- CONSTRAINT fk_course FOREIGN KEY (course_ID) REFERENCES Course(courseID) ON DELETE CASCADE
#     -- CONSTRAINT fk_discount FOREIGN KEY (discountID) REFERENCES DiscountCode(discountID) ON DELETE CASCADE
# );"""}