# Persistent Authentication Plan

When you hit the "Refresh" button (or press F5) in your browser, the connection to the Streamlit server is momentarily broken. Because Streamlit stores its `session_state` entirely in memory for that specific connection, a refresh completely destroys the session, erasing your `jwt_token` and forcefully logging you out.

To fix this, we need to implement **Persistent Authentication using Browser Cookies**.

## User Review Required
> [!IMPORTANT]
> This plan will modify how the Streamlit frontend stores your login token, shifting from temporary memory to persistent browser cookies. Please review the changes below and approve to proceed!

## Proposed Changes

### 1. Install Dependencies
I will install `streamlit-cookies-controller` into your environment. This library allows Streamlit to securely read and write cookies in the user's browser.

### 2. Update Home Page (`streamlit_app/home.py`)
#### [MODIFY] [home.py](file:///c:/Users/hg232/OneDrive/Desktop/adaptive/streamlit_app/home.py)
- **Cookie Initialization**: When the page loads, the app will check your browser cookies for a `jwt_token`.
- **Auto-Login**: If a valid token is found in your cookies, it will automatically pull it into memory and show you the Dashboard—no need to log in again!
- **Saving on Login**: When you manually log in via the form, the app will save the generated JWT token into a secure cookie so it survives refreshes.

### 3. Update Chat Page (`streamlit_app/pages/chat.py`)
#### [MODIFY] [chat.py](file:///c:/Users/hg232/OneDrive/Desktop/adaptive/streamlit_app/pages/chat.py)
- **Hydration**: If you refresh while on the Chat page, the app will instantly grab your token from the cookie to verify you are still logged in, preventing the "Please login from the Home page first" error.
- **Secure Logout**: When you click the "Logout" button, the code will now explicitly delete the cookies from your browser, ensuring you are permanently logged out.

## Verification Plan
1. I will log the changes and install the new library.
2. You can log into the app, go to the Chat page, and hit Refresh (F5).
3. The page will reload perfectly without kicking you out to the login screen!
