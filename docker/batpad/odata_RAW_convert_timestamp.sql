-- Whoops forgot some commands here to change the name of the timestamp column and change its type to timetsamptz but that's what I did

CREATE INDEX idx_delivery_time ON odata_raw(delivery_time);
