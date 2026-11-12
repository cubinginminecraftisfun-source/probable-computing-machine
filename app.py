import json
import secrets
from urllib.parse import urlencode

import requests
import streamlit as st

st.set_page_config(page_title="Kakao Notifier", page_icon="💬")

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
try:
    CLIENT_ID = st.secrets["KAKAO_REST_API_KEY"]
    CLIENT_SECRET = st.secrets["KAKAO_CLIENT_SECRET"]
    REDIRECT_URI = st.secrets["KAKAO_REDIRECT_URI"]
except Exception:
    st.error(
        "Missing configuration. Add KAKAO_REST_API_KEY, "
        "KAKAO_CLIENT_SECRET, and KAKAO_REDIRECT_URI to "
        ".streamlit/secrets.toml (locally) or Streamlit Cloud Secrets."
    )
    st.stop()

AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"
FRIENDS_URL = "https://kapi.kakao.com/v1/api/talk/friends"
SEND_URL = "https://kapi.kakao.com/v1/api/talk/friends/message/default/send"

# Keep an OAuth state value in this Streamlit session.
if "oauth_state" not in st.session_state:
    st.session_state.oauth_state = secrets.token_urlsafe(32)


def api_error_message(response: requests.Response) -> str:
    """Return a useful Kakao API error without exposing credentials."""
    try:
        payload = response.json()
        return json.dumps(payload, ensure_ascii=False)
    except ValueError:
        return response.text[:1000]


def exchange_code_for_token(code: str) -> dict:
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(
            f"Kakao token request failed ({response.status_code}): "
            f"{api_error_message(response)}"
        )
    return response.json()


def get_friends(access_token: str) -> list[dict]:
    response = requests.get(
        FRIENDS_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        params={"limit": 100},
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(
            f"Could not retrieve friends ({response.status_code}): "
            f"{api_error_message(response)}"
        )
    return response.json().get("elements", [])


def send_message(access_token: str, friend_uuid: str, message: str) -> dict:
    template = {
        "object_type": "text",
        "text": message,
        "link": {
            "web_url": "https://developers.kakao.com",
            "mobile_web_url": "https://developers.kakao.com",
        },
    }

    response = requests.post(
        SEND_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={
            "receiver_uuids": json.dumps([friend_uuid]),
            "template_object": json.dumps(template, ensure_ascii=False),
        },
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(
            f"Kakao message request failed ({response.status_code}): "
            f"{api_error_message(response)}"
        )
    return response.json()


# ---------------------------------------------------------------------
# OAuth callback
# ---------------------------------------------------------------------
authorization_code = st.query_params.get("code")
returned_state = st.query_params.get("state")
oauth_error = st.query_params.get("error")

if oauth_error:
    st.error(f"Kakao login was not completed: {oauth_error}")
    st.query_params.clear()
    st.stop()

if authorization_code:
    if returned_state != st.session_state.oauth_state:
        st.error("OAuth state did not match. Please start login again.")
        st.query_params.clear()
        st.stop()

    try:
        token_data = exchange_code_for_token(authorization_code)
        st.session_state.access_token = token_data["access_token"]
        st.query_params.clear()
        st.rerun()
    except Exception as exc:
        st.error(str(exc))
        st.stop()


# ---------------------------------------------------------------------
# User interface
# ---------------------------------------------------------------------
st.title("KakaoTalk Notifier")
st.caption("A small prototype for sending a message to an eligible KakaoTalk friend.")

if "access_token" not in st.session_state:
    query = urlencode(
        {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "friends,talk_message",
            "state": st.session_state.oauth_state,
        }
    )
    login_url = f"{AUTH_URL}?{query}"

    st.write("Connect your Kakao account to continue.")
    st.link_button("Log in with Kakao", login_url)
    st.info(
        "The Kakao app must have the required Kakao Login consent scopes "
        "and API permissions. Friend messaging is restricted by Kakao; "
        "the recipient must be eligible under Kakao's service/team-member rules."
    )
    st.stop()

if st.button("Log out"):
    st.session_state.pop("access_token", None)
    st.rerun()

try:
    friends = get_friends(st.session_state.access_token)
except Exception as exc:
    st.error(str(exc))
    st.info("If the access token expired, log out and sign in again.")
    st.stop()

eligible_friends = {
    friend.get("profile_nickname", "Unnamed friend"): friend["uuid"]
    for friend in friends
    if friend.get("uuid")
}

if not eligible_friends:
    st.warning(
        "Kakao returned no eligible friends. Check that the recipient has "
        "linked your app, granted the required consent, and meets Kakao's "
        "friend-message eligibility requirements."
    )
    st.stop()

selected_name = st.selectbox("Recipient", list(eligible_friends.keys()))
message = st.text_area(
    "Message",
    placeholder="Type your KakaoTalk message here...",
    max_chars=1000,
)

if st.button("Send KakaoTalk message", type="primary"):
    if not message.strip():
        st.warning("Enter a message first.")
    else:
        try:
            result = send_message(
                st.session_state.access_token,
                eligible_friends[selected_name],
                message.strip(),
            )
            successful = result.get("successful_receiver_uuids", [])
            if eligible_friends[selected_name] in successful:
                st.success(f"Kakao accepted the message for {selected_name}.")
            else:
                st.warning(f"Kakao returned this response: {result}")
        except Exception as exc:
            st.error(str(exc))

st.divider()
st.caption(
    "Prototype only: add token refresh, persistent secure token storage, "
    "pagination, and production-grade error handling before wider deployment."
)
