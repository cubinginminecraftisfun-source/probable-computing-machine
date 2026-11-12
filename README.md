# KakaoTalk Notifier (Streamlit prototype)

This is a prototype that lets a logged-in Kakao user retrieve eligible KakaoTalk
friends and send a text message to one selected friend.

## Files

```text
kakao-notifier/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
└── .streamlit/
    └── secrets.toml.example
```

## 1. Configure Kakao Developers

1. Create an application at https://developers.kakao.com/.
2. Find the application's **REST API key**.
3. Configure Kakao Login and the required consent scopes/API permissions.
4. Register the exact redirect URI you will use.
5. Check Kakao's current Friends API eligibility and approval requirements.

The app requests the `friends` and `talk_message` scopes. Adding these scope names
to the OAuth URL does not itself grant access. Kakao must make the relevant
permissions available to your app, and the recipient must meet Kakao's
eligibility rules. In development, friend messaging is generally restricted to
eligible app team members.

Official documentation:
- https://developers.kakao.com/docs/latest/en/kakaologin/common
- https://developers.kakao.com/docs/latest/en/kakaotalk-message/common

## 2. Set up secrets locally

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, then replace
the placeholder values.

`KAKAO_REDIRECT_URI` must exactly match the URI registered in Kakao Developers.
For a local Streamlit run, you can register and use a local callback URI if
Kakao's current configuration permits it. For deployment, use your actual
Streamlit app URL.

Do not commit `.streamlit/secrets.toml` to GitHub. It is excluded by `.gitignore`.

## 3. Run locally

```bash
python -m venv .venv
```

Windows:
```powershell
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install and run:
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 4. Deploy to Streamlit Community Cloud

1. Push the project to GitHub without the real `secrets.toml`.
2. Create an app at https://share.streamlit.io/.
3. Select the repository and `app.py`.
4. Open the app's Settings → Secrets.
5. Paste the same TOML key/value entries from your local secrets file.
6. Ensure the deployed app URL exactly matches the redirect URI registered in
   Kakao Developers.

## Important limitations

- This is a manual-send prototype. It does not schedule or automatically send
  messages in the background.
- Kakao's Friends Message API does not allow sending to arbitrary KakaoTalk IDs
  or phone numbers. Recipient eligibility, consent, and app approval rules apply.
- Kakao API access and feature approval can change. Follow the current official
  documentation and the permissions shown in your developer console.
- The code stores the access token only in the current Streamlit session and
  does not implement refresh-token handling. It is not production-ready.
- Do not expose API keys, client secrets, access tokens, or friend UUIDs in
  public logs, screenshots, or a public repository.
