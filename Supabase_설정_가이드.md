# Supabase 설정 가이드

이 앱은 Streamlit 서버가 Supabase에 연결하는 구조입니다. Supabase secret key는 서버에서만 사용하며 GitHub·브라우저·수업 자료에 공개하면 안 됩니다.

## 1. 프로젝트 생성

1. [Supabase Dashboard](https://supabase.com/dashboard)에 로그인한다.
2. **New project**를 누른다.
3. Organization을 선택하고 Project name(예: `info-class-board`), Database Password, Region을 설정한다.
4. **Create new project**를 누르고 프로젝트가 준비될 때까지 기다린다.

## 2. 데이터베이스 만들기

1. 왼쪽 메뉴 **SQL Editor**를 연다.
2. **New query**를 누른다.
3. 이 프로젝트의 [`sql/schema.sql`](sql/schema.sql) 전체를 붙여 넣는다.
4. **Run**을 누른다.
5. 왼쪽 메뉴 **Table Editor**에서 `profiles`, `assignments`, `apps`, `feedback`, `app_likes` 테이블이 생성됐는지 확인한다.

이 SQL은 작품·피드백·과제·사용자 역할·사용자별 좋아요 테이블, 인덱스, 좋아요 처리 함수, RLS와 공개 API 차단 설정을 한 번에 만듭니다.

## 3. URL과 서버용 키 확인

1. 왼쪽 아래 **Project Settings → API Keys**로 이동한다. (프로젝트 화면의 **Connect** 대화상자에서도 확인 가능)
2. **Project URL**을 복사한다. 형식은 `https://<project-ref>.supabase.co`이다.
3. **Secret key** 중 새 키를 만들거나 기존 `sb_secret_...` 키를 복사한다.
4. 아래 두 값은 Streamlit Secrets에만 입력한다.

```toml
SUPABASE_URL = "https://<project-ref>.supabase.co"
SUPABASE_SERVICE_KEY = "sb_secret_..."
```

`sb_publishable_...` 키는 브라우저에 공개해도 되는 용도이고, 이 앱처럼 Streamlit 서버가 DB를 관리하는 구성에는 사용하지 않습니다. 반대로 `sb_secret_...`는 RLS를 우회할 수 있으므로 절대 GitHub에 커밋하면 안 됩니다.

## 4. Streamlit Secrets 연결

로컬 실행 때는 `.streamlit/secrets.toml.example`을 복사해 `.streamlit/secrets.toml`을 만들고 위 값을 채운다. Community Cloud 배포 때는 파일을 올리지 말고 앱의 **Settings → Secrets**에 같은 내용을 붙여 넣는다.

Google 로그인 설정까지 포함한 전체 Secrets 예시는 [`배포_가이드.md`](배포_가이드.md)의 3단계에 있다.

## 5. 교사 권한 부여

1. 교사가 배포된 앱에서 Google 로그인을 한 번 한다.
2. Supabase **Table Editor → profiles**에서 교사 이메일이 생겼는지 확인한다.
3. 또는 SQL Editor에서 다음 SQL을 실행한다.

```sql
update public.profiles
set role = 'teacher'
where email = '교사_Google_이메일';
```

4. 교사가 앱을 새로고침하면 **과제 관리** 탭이 나타난다.

## 6. 연결 확인 순서

1. 앱에서 Google 로그인한다.
2. Supabase `profiles`에 로그인 계정이 `student`로 생성되는지 확인한다.
3. 교사 역할로 변경하고 앱에서 과제를 하나 만든다.
4. 학생 계정으로 다시 로그인해 과제가 보이고 작품을 제출할 수 있는지 확인한다.
5. Supabase `apps`, `feedback`, `app_likes` 테이블에 데이터가 저장되는지 확인한다.

## 문제 해결

- `Supabase 설정이 필요합니다` 오류: Community Cloud Secrets에 `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`가 모두 있는지 확인한다.
- `Invalid API key` 오류: Project URL과 키를 같은 Supabase 프로젝트에서 복사했는지 확인하고, secret key 앞뒤 공백을 제거한다.
- 테이블 없음 오류: `sql/schema.sql` 전체를 SQL Editor에서 다시 실행한다.
- 교사 탭이 없음: `profiles.role` 값이 정확히 `teacher`인지 확인하고 앱을 새로고침한다.
- secret key가 노출됨: 즉시 **Project Settings → API Keys**에서 키를 교체하고, GitHub 커밋 이력에서 해당 키를 제거한다.
