CREATE SCHEMA IF NOT EXISTS clickstream;

ALTER DATABASE ClickstreamDB SET search_path TO clickstream;


CREATE TABLE clickstream.shopper_data (
    administrative INT,
    administrative_duration FLOAT,
    informational INT,
    informational_duration FLOAT,
    productrelated INT,
    productrelated_duration FLOAT,
    bouncerates FLOAT,
    exitrates FLOAT,
    pagevalues FLOAT,
    specialday FLOAT,
    month VARCHAR(20),
    operatingsystems INT,
    browser INT,
    region INT,
    traffictype INT,
    visitortype VARCHAR(50),
    weekend BOOLEAN,
    revenue BOOLEAN
);

