-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create USD/TRY exchange rate table
CREATE TABLE IF NOT EXISTS usdtry (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    date date NOT NULL,
    open float8,
    high float8,
    low float8,
    close float8,
    volume float8,
    created_at timestamptz DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(date)
);

-- Enable RLS
ALTER TABLE usdtry ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Allow public read access" ON usdtry
    FOR SELECT USING (true);

CREATE POLICY "Allow authenticated insert" ON usdtry
    FOR INSERT WITH CHECK (auth.role() = 'authenticated'); 