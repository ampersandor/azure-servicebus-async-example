-- Create result status enum type
CREATE TYPE resultstatus AS ENUM (
    'PENDING',
    'RUNNING', 
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

-- Create requests table
CREATE TABLE IF NOT EXISTS requests (
    request_id VARCHAR PRIMARY KEY,
    command VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create results table
CREATE TABLE IF NOT EXISTS results (
    result_id VARCHAR PRIMARY KEY,
    result_path VARCHAR,
    status resultstatus NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create request_result relation table
CREATE TABLE IF NOT EXISTS request_result (
    request_id VARCHAR,
    result_id VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (request_id, result_id),
    FOREIGN KEY (request_id) REFERENCES requests(request_id),
    FOREIGN KEY (result_id) REFERENCES results(result_id)
); 