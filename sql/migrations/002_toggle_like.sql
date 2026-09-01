-- 좋아요 토글 기능 추가: Supabase SQL Editor에서 한 번 실행하세요.
create or replace function public.toggle_app_like(p_app_id uuid, p_profile_id uuid)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
begin
  delete from app_likes
  where app_id = p_app_id and profile_id = p_profile_id;

  if found then
    update apps set likes = greatest(likes - 1, 0) where id = p_app_id;
    return false;
  end if;

  insert into app_likes (app_id, profile_id) values (p_app_id, p_profile_id);
  update apps set likes = likes + 1 where id = p_app_id;
  return true;
end;
$$;

revoke execute on function public.toggle_app_like(uuid, uuid) from public, anon, authenticated;
grant execute on function public.toggle_app_like(uuid, uuid) to service_role;
