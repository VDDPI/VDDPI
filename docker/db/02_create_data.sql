use provider;

insert into policy(data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date)
values ("provider.example.com", "person", "https://192.168.220.7:443/data/person/personal-001", "consumer.example.com", "803bfe1abeceaa7521a0ca61ffa70a14a80f4c836172b9e80a39643c64608512", "person.age", 5, "JP", "90", "2025-12-01");

insert into policy(data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date)
values ("provider.example.com", "person", "https://192.168.220.7:443/data/person/personal-002", "consumer.example.com", "803bfe1abeceaa7521a0ca61ffa70a14a80f4c836172b9e80a39643c64608512", "person.age", 5, "JP", "90", "2025-12-01");

insert into policy(data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date)
values ("provider.example.com", "person", "https://192.168.220.7:443/data/person/personal-003", "consumer.example.com", "803bfe1abeceaa7521a0ca61ffa70a14a80f4c836172b9e80a39643c64608512", "", 5, "JP", "90", "2025-12-01");

insert into policy(data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date)
values ("provider.example.com", "person", "https://192.168.220.7:443/data/person/personal-004", "consumer.example.com", "803bfe1abeceaa7521a0ca61ffa70a14a80f4c836172b9e80a39643c64608512", "", 5, "JP", "90", "2025-12-01");

insert into policy(data_provider, data_type, data_id, data_consumer, data_processing, data_disclosing, data_counter, data_location, data_duration, data_expiration_date)
values ("provider.example.com", "person", "https://192.168.220.7:443/data/person/personal-005", "consumer.example.com", "803bfe1abeceaa7521a0ca61ffa70a14a80f4c836172b9e80a39643c64608512", "", 5, "JP", "90", "2025-12-01");
