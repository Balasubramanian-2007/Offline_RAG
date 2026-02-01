-- DB NAME in postgres : OWN_RAG
CREATE TABLE chunks(
    chunk_id SERIAL PRIMARY KEY,
    source_name TEXT,
    heading TEXT,
    content TEXT,
    pg_start INT,
    pg_end INT,
    created_at TIMESTAMP DEFAULT NOW()
)

CREATE TABLE chunks(
    chunk_id SERIAL PRIMARY KEY,
    source_name TEXT,
    heading TEXT,
    content TEXT,
    pg_start INT,
    pg_end INT,
    created_at TIMESTAMP DEFAULT NOW(),
	deleted_at TIMESTAMP NULL
)