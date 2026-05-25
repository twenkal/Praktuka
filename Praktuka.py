import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import re

# Налаштування сторінки
st.set_page_config(page_title="Steam Analytics", page_icon="🎮", layout="wide")

class SteamAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.steampowered.com"

    def resolve_steam_id(self, input_data):
        """Перетворює посилання або нікнейм у SteamID64"""
        input_data = input_data.strip().strip('/')
        
        if input_data.isdigit() and len(input_data) == 17:
            return input_data
        
        match = re.search(r"id/([^/]+)", input_data)
        vanity_id = match.group(1) if match else input_data
        
        url = f"{self.base_url}/ISteamUser/ResolveVanityURL/v1/"
        params = {'key': self.api_key, 'vanityurl': vanity_id}
        
        try:
            res = requests.get(url, params=params).json()
            if res.get('response', {}).get('success') == 1:
                return res['response']['steamid']
        except:
            return None
        return None

    def get_games(self, steam_id):
        url = f"{self.base_url}/IPlayerService/GetOwnedGames/v1/"
        params = {
            'key': self.api_key, 'steamid': steam_id,
            'format': 'json', 'include_appinfo': True,
            'include_played_free_games': True
        }
        try:
            res = requests.get(url, params=params).json()
            return res.get('response', {}).get('games', [])
        except: return []

    def get_achievements(self, steam_id, app_id):
        url = f"{self.base_url}/ISteamUserStats/GetPlayerAchievements/v1/"
        params = {'appid': app_id, 'key': self.api_key, 'steamid': steam_id, 'l': 'ukrainian'}
        try:
            res = requests.get(url, params=params).json()
            return res.get('playerstats', {}).get('achievements', [])
        except: return []

# --- UI СЕКЦІЯ ---
st.title("🎮 Аналітична панель стім")

with st.sidebar:
    st.header("Налаштування")
    api_key = st.text_input("Steam API Key", value="02AB858F4ED29A82F1245771958023B3", type="password")
    user_input = st.text_input("Вставте SteamID64 або посилання на профіль", 
                               placeholder="https://steamcommunity.com/id/...")
    st.info("Приклад: https://steamcommunity.com/id/6928469582385/")

if user_input:
    api = SteamAPI(api_key)
    
    # Визначаємо реальний SteamID64
    real_sid = api.resolve_steam_id(user_input)
    
    if not real_sid:
        st.error("Не вдалося знайти користувача. Перевірте посилання або ID.")
    else:
        st.success(f"Знайдено ID: {real_sid}")
        games = api.get_games(real_sid)

        if games:
            # Далі йде той самий код обробки ігор, що був раніше
            df = pd.DataFrame(games)
            df['hours'] = (df['playtime_forever'] / 60).round(1)
            df = df.sort_values(by='hours', ascending=False).head(5)

            st.subheader("🔥 ТОП-5 ігор за часом")
            cols = st.columns(5)
            for i, (index, row) in enumerate(df.iterrows()):
                with cols[i]:
                    img_url = f"http://media.steampowered.com/steamcommunity/public/images/apps/{row['appid']}/{row['img_icon_url']}.jpg"
                    st.image(img_url if row.get('img_icon_url') else "https://via.placeholder.com/150", width=100)
                    st.metric(label=row['name'][:15], value=f"{row['hours']} год")

            st.markdown("---")
            left_col, right_col = st.columns([1, 1])

            with left_col:
                st.subheader("📊 Розподіл часу")
                fig = px.pie(df, values='hours', names='name', hole=0.3)
                st.plotly_chart(fig, use_container_width=True)

            with right_col:
                st.subheader("🏆 Досягнення")
                selected_game_name = st.selectbox("Оберіть гру:", df['name'].tolist())
                selected_game_id = df[df['name'] == selected_game_name]['appid'].values[0]

                if st.button("Показати досягнення"):
                    achs = api.get_achievements(real_sid, selected_game_id)
                    if achs:
                        for a in achs:
                            icon = "✅" if a['achieved'] == 1 else "❌"
                            name = a.get('description') or a.get('name') or a.get('apiname')
                            st.write(f"{icon} {name}")
                    else:
                        st.warning("Досягнення не знайдені або приховані.")
        else:
            st.error("Список ігор порожній. Перевірте налаштування приватності профілю.")