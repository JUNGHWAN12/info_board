# Google OAuth (`auth.google`) 설정 가이드

Streamlit 앱에서 **Google 계정으로 로그인**하려면 Google Cloud Console에서 OAuth 클라이언트를 만들고, 발급받은 값을 Streamlit Secrets에 등록해야 한다.

## 준비물

- 배포할 Streamlit 앱 주소. 예: `https://info-class-board.streamlit.app`
- Google 계정
- Streamlit Community Cloud 앱의 관리자 권한

## 1. Google Cloud 프로젝트 만들기

1. [Google Cloud Console](https://console.cloud.google.com/)에 로그인한다.
2. 상단 프로젝트 선택 메뉴 → **새 프로젝트**를 누른다.
3. 프로젝트 이름을 입력한다. 예: `정보수업-작품게시판`
4. **만들기**를 누르고 새 프로젝트를 선택한다.

## 2. OAuth 동의 화면 설정

1. 왼쪽 메뉴 **Google Auth Platform** → **Branding**을 연다.
2. 앱 이름, 사용자 지원 이메일, 개발자 연락처 이메일을 입력하고 저장한다.
3. **Audience**에서 대상 사용자를 선택한다.
   - 학교 Google Workspace 구성원만 쓰면 **Internal(내부)**를 선택한다.
   - 개인 Gmail 계정도 쓰게 하려면 **External(외부)**을 선택한다.
4. External이고 앱이 테스트 상태라면 **Test users**에 교사와 테스트할 학생 Google 이메일을 추가한다.
5. **Data Access**에서 기본 로그인 권한인 `openid`, `email`, `profile`이 사용되는지 확인한다. 추가 Google 서비스 권한은 필요 없다.

## 3. OAuth 클라이언트 ID 만들기

1. **Google Auth Platform** → **Clients**를 연다.
2. **Create client**를 누른다.
3. Application type은 **Web application**을 선택한다.
4. 이름을 입력한다. 예: `정보수업 게시판 - Streamlit`
5. **Authorized JavaScript origins**에 앱의 기본 주소를 입력한다.

```text
https://info-class-board.streamlit.app
```

6. **Authorized redirect URIs**에 앱 주소 뒤에 `/oauth2callback`을 붙여 입력한다.

```text
https://info-class-board.streamlit.app/oauth2callback
```

7. **Create**를 누른다.
8. 표시되는 **Client ID**와 **Client secret**을 복사한다.

앱 주소를 바꾸면 위의 두 주소도 새 앱 주소로 변경해야 한다. 로컬 테스트도 할 경우 아래 두 값을 추가한다.

```text
http://localhost:8501
http://localhost:8501/oauth2callback
```

## 4. Streamlit Secrets에 등록

Streamlit Community Cloud에서 앱을 열고 **Manage app → Settings → Secrets**로 이동한다. 기존 내용에 아래 값을 추가하거나 교체한다.

```toml
[auth]
redirect_uri = "https://info-class-board.streamlit.app/oauth2callback"
cookie_secret = "무작위_긴_문자열"

[auth.google]
client_id = "2...apps.googleusercontent.com"
client_secret = "GOCSPX-..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

`server_metadata_url`은 Google의 표준 OpenID Connect 설정 주소이므로 바꾸지 않는다. **Save**를 누른 뒤 앱을 새로고침해 로그인 버튼을 확인한다.

## 5. 정상 동작 확인

1. 앱을 시크릿/프라이빗 창에서 연다.
2. **Google 계정으로 로그인**을 누른다.
3. 로그인할 Google 계정을 선택한다.
4. 앱으로 돌아오면 사이드바에 이메일과 이름이 표시되는지 확인한다.
5. Supabase `profiles` 테이블에 해당 이메일이 `student` 역할로 생성되는지 확인한다.

## 자주 발생하는 오류

| 메시지/현상 | 확인할 사항 |
| --- | --- |
| `redirect_uri_mismatch` | Google Console의 redirect URI와 Secrets의 `redirect_uri`가 한 글자까지 같은지 확인 |
| 로그인 버튼을 눌러도 오류 | Client ID·Secret을 실제 값으로 교체했는지, Secrets를 저장했는지 확인 |
| 테스트 사용자만 로그인 가능 | External 앱이 테스트 상태면 Google Auth Platform → Audience → Test users에 이메일 추가 |
| `AttributeError: st.user...` | 최신 코드로 push한 뒤, Secrets에 `[auth]`와 `[auth.google]` 전체가 있는지 확인 |
| 로그인 후 앱으로 돌아오지 않음 | 앱 주소가 변경되지 않았는지와 `/oauth2callback` 경로를 확인 |

## 보안 주의사항

- Client secret과 `cookie_secret`은 GitHub, 화면, 채팅에 올리지 않는다.
- Secrets는 Streamlit Community Cloud의 Settings에만 저장한다.
- Google Cloud Console에서 더 이상 쓰지 않는 OAuth 클라이언트는 삭제한다.
