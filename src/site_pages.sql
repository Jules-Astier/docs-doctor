-- Enable the pgvector extension
create extension if not exists vector;

-- Create the documentation chunks table
create table site_pages (
    id bigserial primary key,
    url varchar not null,
    chunk_number integer not null,
    title varchar not null,
    summary varchar not null,
    content text not null,  -- Added content column
    metadata jsonb not null default '{}'::jsonb,  -- Added metadata column
    embedding vector(1536),  -- OpenAI embeddings are 1536 dimensions
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Add a unique constraint to prevent duplicate chunks for the same URL
    unique(url, chunk_number)
);

-- Create the packages table
create table packages (
    id serial primary key,
    package varchar unique not null,
    package_name varchar unique not null,
    description varchar not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- First, drop the rule if it already exists
DROP RULE IF EXISTS packages_upsert_rule ON packages;

-- Create the rule
CREATE RULE packages_upsert_rule AS
    ON INSERT TO packages
    DO INSTEAD
        SELECT CASE WHEN EXISTS (
            SELECT 1 FROM packages WHERE package_name = NEW.package_name
        )
        THEN 
            (
                UPDATE packages SET
                    package = NEW.package,
                    description = NEW.description,
                    created_at = timezone('utc'::text, now())
                WHERE package_name = NEW.package_name
                RETURNING *
            )
        ELSE 
            (
                INSERT INTO packages (package, package_name, description)
                VALUES (NEW.package, NEW.package_name, NEW.description)
                RETURNING *
            )
        END;

-- Create an index for better vector similarity search performance
create index on site_pages using ivfflat (embedding vector_cosine_ops);

-- Create an index on metadata for faster filtering
create index idx_site_pages_metadata on site_pages using gin (metadata);

-- Create a function to search for documentation chunks
create function match_site_pages (
  query_embedding vector(1536),
  match_count int default 10,
  filter jsonb DEFAULT '{}'::jsonb
) returns table (
  id bigint,
  url varchar,
  chunk_number integer,
  title varchar,
  summary varchar,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
#variable_conflict use_column
begin
  return query
  select
    id,
    url,
    chunk_number,
    title,
    summary,
    content,
    metadata,
    1 - (site_pages.embedding <=> query_embedding) as similarity
  from site_pages
  where metadata @> filter
  order by site_pages.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- Everything above will work for any PostgreSQL database. The below commands are for Supabase security

-- Enable RLS on the table
alter table site_pages enable row level security;

-- Create a policy that allows anyone to read
create policy "Allow public read access"
  on site_pages
  for select
  to public
  using (true);