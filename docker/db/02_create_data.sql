SET @APP_ID = '281d9646110a7a04dab0d6c01600c91ae73fe40bac7c57d';

use provider;

insert into policy(data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date)
values ("provider.example.com", "person", "https://192.168.220.7:443/data/person/personal-001", "consumer.example.com", @APP_ID, "person.age", 5, "JP", "90", "2026-12-01");

insert into policy(data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date)
values ("provider.example.com", "person", "https://192.168.220.7:443/data/person/personal-002", "consumer.example.com", @APP_ID, "person.age", 5, "JP", "90", "2026-12-01");

insert into policy(data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date)
values ("provider.example.com", "person", "https://192.168.220.7:443/data/person/personal-003", "consumer.example.com", @APP_ID, "person.age", 5, "JP", "90", "2026-12-01");

insert into policy(data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date)
values ("provider.example.com", "person", "https://192.168.220.7:443/data/person/personal-004", "consumer.example.com", @APP_ID, "person.age", 5, "JP", "90", "2026-12-01");

insert into policy(data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date)
values ("provider.example.com", "person", "https://192.168.220.7:443/data/person/personal-005", "consumer.example.com", @APP_ID, "person.age", 5, "JP", "90", "2026-12-01");
