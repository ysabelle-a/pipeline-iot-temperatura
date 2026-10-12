
CREATE TABLE temperature_readings (
    id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL,
    reading_time TIMESTAMP NOT NULL,
    temperature INTEGER NOT NULL,
    location_type VARCHAR(3) CHECK (location_type IN ('In', 'Out'))
);
