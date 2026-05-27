-- Enable pgvector extension on the ticdss database.
-- Runs once when the Postgres container is first initialized.
CREATE EXTENSION IF NOT EXISTS vector;
