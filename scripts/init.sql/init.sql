-- ETL System Database Initialization Script
-- This script creates all tables for the microservices system

-- Enable UUID extension for potential future use
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- AUTH SERVICE TABLES
-- =============================================================================

-- Users table - centralized user management
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- =============================================================================
-- FILE MANAGER SERVICE TABLES
-- =============================================================================

-- File metadata table - tracks uploaded files
CREATE TABLE IF NOT EXISTS file_metadata (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    user_id INTEGER NOT NULL,
    is_processed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key constraint
    CONSTRAINT fk_file_metadata_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for file_metadata table
CREATE INDEX IF NOT EXISTS idx_file_metadata_user_id ON file_metadata(user_id);
CREATE INDEX IF NOT EXISTS idx_file_metadata_is_processed ON file_metadata(is_processed);
CREATE INDEX IF NOT EXISTS idx_file_metadata_created_at ON file_metadata(created_at);

-- =============================================================================
-- DATA PROCESSOR SERVICE TABLES
-- =============================================================================

-- Processed file data - stores valid CSV records
CREATE TABLE IF NOT EXISTS file_processed_data (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    documento VARCHAR(50) UNIQUE NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    endereco VARCHAR(500) NOT NULL,
    file_id INTEGER NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key constraint
    CONSTRAINT fk_file_processed_data_file_id FOREIGN KEY (file_id) REFERENCES file_metadata(id) ON DELETE CASCADE
);

-- Create indexes for file_processed_data table
CREATE INDEX IF NOT EXISTS idx_file_processed_data_file_id ON file_processed_data(file_id);
CREATE INDEX IF NOT EXISTS idx_file_processed_data_documento ON file_processed_data(documento);
CREATE INDEX IF NOT EXISTS idx_file_processed_data_processed_at ON file_processed_data(processed_at);

-- File inconsistencies table - tracks validation errors
CREATE TABLE IF NOT EXISTS file_inconsistencies (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL,
    line_number INTEGER,
    field_name VARCHAR(100),
    invalid_value TEXT,
    error_message TEXT NOT NULL,
    error_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key constraint
    CONSTRAINT fk_file_inconsistencies_file_id FOREIGN KEY (file_id) REFERENCES file_metadata(id) ON DELETE CASCADE
);

-- Create indexes for file_inconsistencies table
CREATE INDEX IF NOT EXISTS idx_file_inconsistencies_file_id ON file_inconsistencies(file_id);
CREATE INDEX IF NOT EXISTS idx_file_inconsistencies_error_type ON file_inconsistencies(error_type);
CREATE INDEX IF NOT EXISTS idx_file_inconsistencies_created_at ON file_inconsistencies(created_at);

-- =============================================================================
-- SAMPLE DATA (Optional - for development/testing)
-- =============================================================================

-- Insert sample user for testing
INSERT INTO users (email, password, full_name)
VALUES ('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVMBYXOPVNqmBZ.e', 'Administrator')
ON CONFLICT (email) DO NOTHING;

-- Note: Password is 'admin123' hashed with bcrypt

-- =============================================================================
-- FINAL SETUP
-- =============================================================================

-- Update timestamps function for automatic updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers for updated_at columns
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_file_metadata_updated_at ON file_metadata;
CREATE TRIGGER update_file_metadata_updated_at
    BEFORE UPDATE ON file_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO etl_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO etl_user;

-- Success message
SELECT 'ETL System database initialization completed successfully!' as status;