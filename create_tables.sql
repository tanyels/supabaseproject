-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Function to create a stock price table
CREATE OR REPLACE FUNCTION create_stock_table(table_name text) 
RETURNS void AS $$
BEGIN
    -- Create the table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
            date date NOT NULL,
            open float8,
            high float8,
            low float8,
            close float8,
            volume float8,
            dividends float8,
            stock_splits float8,
            created_at timestamptz DEFAULT timezone(''utc''::text, now()) NOT NULL,
            UNIQUE(date)
        )', table_name);
    
    -- Enable RLS
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
    
    -- Create policies
    EXECUTE format('
        CREATE POLICY "Allow public read access" ON %I
            FOR SELECT USING (true)
    ', table_name);
    
    EXECUTE format('
        CREATE POLICY "Allow authenticated insert" ON %I
            FOR INSERT WITH CHECK (auth.role() = ''authenticated'')
    ', table_name);
END;
$$ LANGUAGE plpgsql;

-- Create tables for all BIST 30 stocks
SELECT create_stock_table('akbnk');
SELECT create_stock_table('arclk');
SELECT create_stock_table('asels');
SELECT create_stock_table('bimas');
SELECT create_stock_table('dohol');
SELECT create_stock_table('ekgyo');
SELECT create_stock_table('enkai');
SELECT create_stock_table('eregl');
SELECT create_stock_table('froto');
SELECT create_stock_table('garan');
SELECT create_stock_table('halkb');
SELECT create_stock_table('isctr');
SELECT create_stock_table('kchol');
SELECT create_stock_table('kozaa');
SELECT create_stock_table('kozal');
SELECT create_stock_table('krdmd');
SELECT create_stock_table('petkm');
SELECT create_stock_table('pgsus');
SELECT create_stock_table('sahol');
SELECT create_stock_table('sasa');
SELECT create_stock_table('sise');
SELECT create_stock_table('tavhl');
SELECT create_stock_table('tcell');
SELECT create_stock_table('thyao');
SELECT create_stock_table('tkfen');
SELECT create_stock_table('toaso');
SELECT create_stock_table('ttkom');
SELECT create_stock_table('tuprs');
SELECT create_stock_table('vakbn');
SELECT create_stock_table('ykbnk');