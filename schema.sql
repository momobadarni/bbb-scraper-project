create table public.businesses (
  id serial not null,
  name text not null,
  phone text null,
  address text null,
  url text null,
  accreditation_status boolean null,
  principal_contact text null,
  scraped_at timestamp without time zone null default now(),
  source text null default 'stagehand'::text,
  constraint businesses_pkey primary key (id)
) TABLESPACE pg_default;