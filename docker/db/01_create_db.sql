create database provider;
use provider;
create table policy (
    data_provider varchar(64) not null,
    data_type varchar(64) not null,
    data_id varchar(64),
    data_consumer varchar(64) not null,
    data_processing varchar(128) not null,
    data_disclosing varchar(64) not null,
    data_counter int null,
    data_location varchar(10) null,
    data_duration int null,
    data_expiration_date varchar(11) null,
    PRIMARY KEY(data_processing, data_id)
);

create table saved_policy (
    consumer_subject varchar(64) not null,
    app_id varchar(64) not null,
    data_id varchar(64) not null,
    data_counter varchar(64) null,
    data_location varchar(10) null,
    data_duration int null,
    data_expiration_date varchar(11) null,
    PRIMARY KEY(app_id, data_id)
);
