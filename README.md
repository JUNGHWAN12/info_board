# 정보 수업 작품 게시판

Google 계정으로 로그인한 학생이 작품을 제출하고, 교사가 과제를 만들고 관리하는 Streamlit 게시판입니다. 데이터는 Supabase PostgreSQL에 저장합니다.

## 처음 한 번 설정

1. Supabase Dashboard의 SQL Editor에서 [`sql/schema.sql`](sql/schema.sql)을 실행합니다.
2. Google Cloud Console에서 웹 애플리케이션 OAuth Client를 만듭니다.
   - 승인된 JavaScript 원본: 앱 주소 (예: `https://my-board.streamlit.app`)
   - 승인된 리디렉션 URI: Streamlit `redirect_uri` (예: `https://my-board.streamlit.app/oauth2callback`)
3. `.streamlit/secrets.toml.example`을 복사해 `.streamlit/secrets.toml`을 만들고 Google Client ID/Secret, Supabase URL/secret key를 입력합니다.
4. 가상환경에서 의존성을 설치하고 실행합니다.

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\streamlit.exe run app.py
```

로컬 주소가 `http://localhost:8501`이면 Google Cloud Console과 `redirect_uri` 모두 `http://localhost:8501/oauth2callback`로 맞춰야 합니다.

## 교사 계정 지정

교사가 Google 로그인을 한 번 완료하면 `profiles` 테이블에 학생 역할로 생성됩니다. Supabase SQL Editor에서 아래 SQL의 이메일을 바꾸어 한 번 실행합니다.

```sql
update public.profiles
set role = 'teacher'
where email = 'teacher@school.example';
```

그 다음 로그인부터 해당 계정에만 **과제 관리** 탭이 표시됩니다.

## 보안 메모

`SUPABASE_SERVICE_KEY`는 Streamlit Secrets에만 두고 저장소에 추가하지 않습니다. 이 앱은 서버에서 Google 로그인과 역할을 확인한 후에만 DB 쓰기를 수행합니다. Supabase SQL은 익명/일반 인증 API 접근을 차단합니다.
