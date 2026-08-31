create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key default gen_random_uuid(),
  google_sub text not null unique,
  email text not null unique,
  display_name varchar(20) not null,
  role text not null default 'student' check (role in ('student', 'teacher')),
  created_at timestamptz not null default now()
);

create table if not exists public.assignments (
  id uuid primary key default gen_random_uuid(),
  title varchar(60) not null check (char_length(trim(title)) > 0),
  description varchar(300),
  due_at timestamptz,
  status text not null default 'draft' check (status in ('draft', 'open', 'closed')),
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.apps (
  id uuid primary key default gen_random_uuid(),
  assignment_id uuid not null references public.assignments(id) on delete restrict,
  profile_id uuid not null references public.profiles(id) on delete restrict,
  nickname varchar(20) not null check (char_length(trim(nickname)) > 0),
  url text not null check (url ~ '^https://'),
  description varchar(80) not null check (char_length(trim(description)) > 0),
  likes integer not null default 0 check (likes >= 0),
  created_at timestamptz not null default now()
);

create table if not exists public.feedback (
  id uuid primary key default gen_random_uuid(),
  app_id uuid not null references public.apps(id) on delete cascade,
  profile_id uuid not null references public.profiles(id) on delete restrict,
  nickname varchar(16) not null check (char_length(trim(nickname)) > 0),
  content varchar(60) not null check (char_length(trim(content)) > 0),
  created_at timestamptz not null default now()
);

create table if not exists public.app_likes (
  app_id uuid not null references public.apps(id) on delete cascade,
  profile_id uuid not null references public.profiles(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (app_id, profile_id)
);

create index if not exists apps_assignment_created_idx on public.apps(assignment_id, created_at desc);
create index if not exists feedback_app_created_idx on public.feedback(app_id, created_at);

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists assignments_set_updated_at on public.assignments;
create trigger assignments_set_updated_at
before update on public.assignments
for each row execute function public.set_updated_at();

create or replace function public.add_app_like(p_app_id uuid, p_profile_id uuid)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into app_likes (app_id, profile_id) values (p_app_id, p_profile_id)
  on conflict do nothing;
  if not found then return false; end if;
  update apps set likes = likes + 1 where id = p_app_id;
  return true;
end;
$$;

-- Streamlit 서버만 secret key로 DB에 접근한다. 공개 API 경로는 차단한다.
alter table public.profiles enable row level security;
alter table public.assignments enable row level security;
alter table public.apps enable row level security;
alter table public.feedback enable row level security;
alter table public.app_likes enable row level security;
revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke execute on function public.add_app_like(uuid, uuid) from public, anon, authenticated;
grant execute on function public.add_app_like(uuid, uuid) to service_role;

-- 교사 승격 예시: Google 로그인 후 한 번 실행
-- update public.profiles set role = 'teacher' where email = 'teacher@school.example';
