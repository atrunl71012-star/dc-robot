import discord
from discord import app_commands
import json
import os
import random
from datetime import datetime
from dotenv import load_dotenv
load_dotenv("token.env") #從 token.env 檔案讀取環境變數

# --- 設定 JSON 檔案名稱 ---
file_game = "game.json"
file_story = "story.json"
file_level = "level_data.json" # 新增等級資料檔
file_exp_claim = "exp_claim.json" # 領取記錄檔

#===讀取game.json的函數===
def load_game():
    if not os.path.exists(file_game):
        return {}
    with open(file_game, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

#===儲存game.json的函數===
def save_game(data):
    with open(file_game, "w", encoding="utf-8") as f:
        # indent=4 可以讓 JSON 檔案自動排版,比較好閱讀
        json.dump(data, f, indent=4, ensure_ascii=False)

#===讀取level_data.json的函數===
def load_level_data():
    if not os.path.exists(file_level):
        return {}
    with open(file_level, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

#===讀取exp_claim.json的函數===
def load_exp_claim():
    if not os.path.exists(file_exp_claim):
        return {}
    with open(file_exp_claim, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

#===儲存exp_claim.json的函數===
def save_exp_claim(data):
    with open(file_exp_claim, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

#===防呆===
def Nfool(user_id,user):
    data = load_game()
    if user_id not in data:
        data[user_id] = {
            "name": user.name,
            "level": 1,
            "exp": 0,
            "money": 0,
            "exp_multiplier": 1.00
        }

    player = data[user_id]
    # --- 防呆：幫舊玩家補欄位 ---
    if "name" not in player:
        player["name"] = user.name
    if "level" not in player:
        player["level"] = 1
    if "exp" not in player:
        player["exp"] = 0
    if "money" not in player:
        player["money"] = 0
    if "exp_multiplier" not in player:
        player["exp_multiplier"] = 1.00

    return data, player #回傳整個資料庫和這個玩家的資料

intents = discord.Intents.default()
intents.message_content = True #開啟訊息內容意圖 記得機器人也要開
intents.guild_messages = True 

client = discord.Client(intents=intents) #預設意圖
tree = app_commands.CommandTree(client) #指令樹

@client.event #事件
async def on_ready():
    await tree.sync() #同步指令
    print("機器人已啟動")
    print("機器人身分:"+str(client.user))

@tree.command(name="ping", description="回覆 Pong!") #指令
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@tree.command(name="hi",description="打招呼")
async def hi(interaction: discord.Interaction):
    await interaction.response.send_message("你好啊!")

# === 21點指令 ===
@tree.command(name="21", description="遊玩21點")
@app_commands.describe(bet="賭注金額，最高 128000")
async def blackjack(interaction: discord.Interaction, bet: int):
    user = interaction.user
    user_id = str(user.id)
    MAX_BET = 128000

    def load_game():
        try:
            with open("game.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_game_data(data):
        with open("game.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def ensure_player(data):
        if user_id not in data:
            data[user_id] = {
                "name": user.name,
                "level": 1,
                "exp": 0,
                "exp_multiplier": 1.0,
                "blackjack_wins": 0,
                "blackjack_losses": 0,
                "money": 0
            }

        player = data[user_id]
        player.setdefault("name", user.name)
        player.setdefault("level", 1)
        player.setdefault("exp", 0)
        player.setdefault("exp_multiplier", 1.0)
        player.setdefault("blackjack_wins", 0)
        player.setdefault("blackjack_losses", 0)
        player.setdefault("money", 0)

        return player

    def pay_bet():
        data = load_game()
        player = ensure_player(data)

        if bet <= 0:
            return False, "賭注金額必須大於 0。"

        if bet > MAX_BET:
            return False, f"賭注上限是 **{MAX_BET}** 金幣。"

        if player["money"] < bet:
            return False, (
                f"你的金幣不足。\n"
                f"目前金幣：**{player['money']}**\n"
                f"下注金額：**{bet}**"
            )

        player["money"] -= bet
        save_game_data(data)
        return True, None

    ok, error_message = pay_bet()
    if not ok:
        await interaction.response.send_message(error_message, ephemeral=True)
        return

    suits = ["♠", "♥", "♦", "♣"]
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

    def create_deck():
        deck = [(rank, suit) for suit in suits for rank in ranks]
        random.shuffle(deck)
        return deck

    def card_value(card):
        rank = card[0]
        if rank in ["J", "Q", "K"]:
            return 10
        if rank == "A":
            return 11
        return int(rank)

    def hand_value(hand):
        total = sum(card_value(card) for card in hand)
        aces = sum(1 for card in hand if card[0] == "A")

        while total > 21 and aces > 0:
            total -= 10
            aces -= 1

        return total

    def hand_text(hand, hide_first=False):
        if hide_first:
            return "?? " + " ".join(f"{rank}{suit}" for rank, suit in hand[1:])
        return " ".join(f"{rank}{suit}" for rank, suit in hand)

    deck = create_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]

    class BlackjackView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
            self.ended = False

        def stats_text(self):
            data = load_game()
            player = ensure_player(data)

            wins = player["blackjack_wins"]
            losses = player["blackjack_losses"]
            total = wins + losses
            rate = "0%" if total == 0 else f"{wins / total * 100:.1f}%"

            return f"勝 {wins} | 負 {losses} | 總場次 {total} | 勝率 {rate}"

        def get_embed(self):
            player_points = hand_value(player_hand)

            embed = discord.Embed(
                title="🃏 21點 Blackjack",
                description=(
                    f"**你的手牌（{player_points}點）**\n"
                    f"{hand_text(player_hand)}\n\n"
                    f"**莊家手牌**\n"
                    f"{hand_text(dealer_hand, hide_first=True)}\n\n"
                    f"{self.stats_text()}"
                ),
                color=discord.Color.gold()
            )
            return embed

        def end_embed(self, result):
            player_points = hand_value(player_hand)
            dealer_points = hand_value(dealer_hand)

            if result in ("win", "dealer_bust"):
                title = f"🎉 你贏了！獲得 {bet} 金幣"
                color = discord.Color.green()
            elif result in ("lose", "bust"):
                title = f"😢 你輸了！損失 {bet} 金幣"
                color = discord.Color.red()
            else:
                title = f"🤝 平局！退回 {bet} 金幣"
                color = discord.Color.light_grey()

            embed = discord.Embed(
                title=title,
                description=(
                    f"**你的手牌（{player_points}點）**\n"
                    f"{hand_text(player_hand)}\n\n"
                    f"**莊家手牌（{dealer_points}點）**\n"
                    f"{hand_text(dealer_hand)}\n\n"
                    f"{self.stats_text()}"
                ),
                color=color
            )
            return embed

        def disable_game_buttons(self):
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label in ("要牌 Hit", "停牌 Stand"):
                    item.disabled = True

        def record_result(self, result):
            data = load_game()
            player = ensure_player(data)

            if result in ("win", "dealer_bust"):
                player["blackjack_wins"] += 1
                player["money"] += bet * 2
            elif result in ("lose", "bust"):
                player["blackjack_losses"] += 1
            elif result == "draw":
                player["money"] += bet

            save_game_data(data)

        async def resolve(self, interaction_btn: discord.Interaction):
            while hand_value(dealer_hand) < 17:
                dealer_hand.append(deck.pop())

            player_points = hand_value(player_hand)
            dealer_points = hand_value(dealer_hand)

            if dealer_points > 21:
                result = "dealer_bust"
            elif player_points > dealer_points:
                result = "win"
            elif player_points < dealer_points:
                result = "lose"
            else:
                result = "draw"

            self.ended = True
            self.disable_game_buttons()
            self.record_result(result)
            self.add_item(self.replay_button())

            await interaction_btn.response.edit_message(
                embed=self.end_embed(result),
                view=self
            )

        def replay_button(self):
            btn = discord.ui.Button(
                label="再來一局",
                style=discord.ButtonStyle.success,
                emoji="🔄"
            )

            async def replay_callback(interaction_btn: discord.Interaction):
                if interaction_btn.user.id != interaction.user.id:
                    await interaction_btn.response.send_message("這不是你的遊戲!", ephemeral=True)
                    return

                ok, error_message = pay_bet()
                if not ok:
                    await interaction_btn.response.send_message(error_message, ephemeral=True)
                    return

                nonlocal deck, player_hand, dealer_hand
                deck = create_deck()
                player_hand = [deck.pop(), deck.pop()]
                dealer_hand = [deck.pop(), deck.pop()]

                new_view = BlackjackView()

                if hand_value(player_hand) == 21:
                    while hand_value(dealer_hand) < 17:
                        dealer_hand.append(deck.pop())

                    if hand_value(dealer_hand) == 21:
                        result = "draw"
                    else:
                        result = "win"

                    new_view.ended = True
                    new_view.disable_game_buttons()
                    new_view.record_result(result)
                    new_view.add_item(new_view.replay_button())

                    await interaction_btn.response.edit_message(
                        embed=new_view.end_embed(result),
                        view=new_view
                    )
                else:
                    await interaction_btn.response.edit_message(
                        embed=new_view.get_embed(),
                        view=new_view
                    )

            btn.callback = replay_callback
            return btn

        @discord.ui.button(label="要牌 Hit", style=discord.ButtonStyle.primary, emoji="➕")
        async def hit(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
            if interaction_btn.user.id != interaction.user.id:
                await interaction_btn.response.send_message("這不是你的遊戲!", ephemeral=True)
                return

            if self.ended:
                return

            player_hand.append(deck.pop())
            player_points = hand_value(player_hand)

            if player_points > 21:
                self.ended = True
                self.disable_game_buttons()
                self.record_result("bust")
                self.add_item(self.replay_button())

                await interaction_btn.response.edit_message(
                    embed=self.end_embed("bust"),
                    view=self
                )
            elif player_points == 21:
                await self.resolve(interaction_btn)
            else:
                await interaction_btn.response.edit_message(
                    embed=self.get_embed(),
                    view=self
                )

        @discord.ui.button(label="停牌 Stand", style=discord.ButtonStyle.danger, emoji="✋")
        async def stand(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
            if interaction_btn.user.id != interaction.user.id:
                await interaction_btn.response.send_message("這不是你的遊戲!", ephemeral=True)
                return

            if self.ended:
                return

            await self.resolve(interaction_btn)

    view = BlackjackView()

    if hand_value(player_hand) == 21:
        while hand_value(dealer_hand) < 17:
            dealer_hand.append(deck.pop())

        if hand_value(dealer_hand) == 21:
            result = "draw"
        else:
            result = "win"

        view.ended = True
        view.disable_game_buttons()
        view.record_result(result)
        view.add_item(view.replay_button())

        await interaction.response.send_message(
            embed=view.end_embed(result),
            view=view
        )
    else:
        await interaction.response.send_message(
            embed=view.get_embed(),
            view=view
        )
#========================================================

# === 查詢玩家資料 (卡片) ===
@tree.command(name="card", description="查詢玩家基本資料")
async def card(interaction: discord.Interaction):
    user = interaction.user
    user_id = str(user.id)

    data, player = Nfool(user_id, user)
    level_data = load_level_data()

    save_game(data)
    
    player_level = data[user_id]["level"]
    player_exp = data[user_id]["exp"]
    player_money = data[user_id]["money"]
    
    # 從 level_data.json 取得該等級的境界名稱與所需經驗，如果找不到就給預設值
    level_info = level_data.get(str(player_level), {"name": "未知等級", "max_exp": 99999})
    realm_name = level_info["name"]
    max_exp = level_info["max_exp"]

    # --- 計算經驗條與百分比 ---
    if max_exp > 0:
        percent = (player_exp / max_exp) * 100
        filled_blocks = int((player_exp / max_exp) * 10)
    else:
        percent = 100.0
        filled_blocks = 10
        
    filled_blocks = min(filled_blocks, 10) # 確保最多10格
    empty_blocks = 10 - filled_blocks
    progress_bar = "■" * filled_blocks + "□" * empty_blocks
    
    # 組合排版：進度條 百分比 換行 具體數值
    # 組合排版：在 progress_bar 前後加上 ` (反引號)
    exp_display = f"`{progress_bar}` **{percent:.1f}%**\n{player_exp} / {max_exp}"
    # ------------------------

    embed = discord.Embed(title="📜 玩家資料卡", color=discord.Color.blue())
    
    if user.display_avatar:
        embed.set_thumbnail(url=user.display_avatar.url)
    
    #embed.add_field(name="帳號名稱", value=user.name, inline=True)
    embed.add_field(name="伺服器暱稱", value=user.display_name, inline=True) 
    #embed.add_field(name="帳號數字 ID", value=user_id, inline=False)
    
    # 顯示境界、等級與經驗條
    embed.add_field(name="境界", value=realm_name, inline=True)
    embed.add_field(name="⭐經驗值", value=exp_display, inline=False)
    embed.add_field(name="💰金幣", value=str(player_money), inline=True)
    
    # 寄出/輸出這張卡片 [1]
    await interaction.response.send_message(embed=embed)

#領錢錢
@tree.command(name="money", description="領錢錢")
async def money(interaction: discord.Interaction):
    user = interaction.user
    user_id = str(user.id)
    # --- 讀取玩家資料 ---
    data, player = Nfool(user_id, user)
    # --- 取得當前小時標識 ---
    now = datetime.now()
    current_hour_key = now.strftime("%Y-%m-%d-%H")

    # --- 讀取領取記錄 ---
    claim_data = load_exp_claim()
    money_key = f"money_{user_id}"

    if claim_data.get(money_key) == current_hour_key:
        next_time = int(now.strftime("%H")) + 1
        if next_time == 24:
            next_time = 0

        await interaction.response.send_message(
            f"你這個小時已經領過錢了，下個整點再來吧！\n"
            f"（下次刷新時間 **{next_time} 點**）"
        )
        return

    # --- 計算領取金幣 ---
    level = player.get("level", 1)
    player["money"] += level * 100

    # --- 儲存 ---
    save_game(data)
    claim_data[money_key] = current_hour_key
    save_exp_claim(claim_data)

    await interaction.response.send_message(
        f"💰 領錢成功！\n"
        f"你領取了 **{level * 100}** 金幣！\n"
        f"目前金幣：**{player['money']}**"
    )

# === 吐納指令 ===
@tree.command(name="exp", description="吐納：獲得少量經驗值（每整點可領取一次）")
async def exp(interaction: discord.Interaction):
    user = interaction.user
    user_id = str(interaction.user.id)
    # --- 讀取玩家資料 ---
    data, player = Nfool(user_id, user)   
    
    # --- 取得當前小時標識（例如 "2025-01-15-14"）---
    now = datetime.now()
    current_hour_key = now.strftime("%Y-%m-%d-%H")
    
    # --- 讀取領取記錄 ---
    claim_data = load_exp_claim()
    
    if claim_data.get(user_id) == current_hour_key:
        next_time = int(now.strftime('%H')) + 1
        if next_time == 24: #新的一天
            next_time = 0
        # 本小時已領取
        await interaction.response.send_message(
            f"你這個小時已經吐納過了，下個整點再來吧！\n"
            f"（下次刷新時間** {next_time} 點**）"
        )
        return
    
    level = player.get("level", 1) # 玩家當前等級，如果沒有就預設為1
    multiplier = player.get("exp_multiplier", 1.00) # 經驗值倍率，如果沒有就預設為1.00
    level_data = load_level_data() # 讀取等級資料
    level_info = level_data.get(str(player["level"]), {"name": "已滿級", "max_exp": 99999}) # 取得當前等級的資料，如果沒有那就是超出等級上限
    
    # --- 計算經驗值 ---
    gained_exp = int(level * 50 * multiplier)
    player["exp"] = player.get("exp", 0) + gained_exp

    # 升級
    while player.get("exp", 0) >= level_info["max_exp"]:
        player["exp"] -= level_info["max_exp"]
        player["level"] = player["level"] + 1
        level_info = level_data.get(str(player["level"]), {"name": "已滿級", "max_exp": 99999}) # 更新等級資料
    
    # --- 儲存 ---
    save_game(data)
    claim_data[user_id] = current_hour_key
    save_exp_claim(claim_data)
    
    await interaction.response.send_message(
        f"🧘 吐納成功！\n"
        f"獲得 **{gained_exp}** 點經驗值（基礎經驗 {level*50} × {multiplier:.2f}）\n"
    )

#===============================
@client.event
async def on_message(message):
    if message.author.bot: #如果收到的訊息是機器人發的,就直接跳過 [1]
        return
        
    print("收到訊息:", message.content)
    
    if message.content.strip() == "開始":
        await message.channel.send("遊戲開始!"+str(message.author.mention)) #message.author 輸出用戶id [1]

    if "早安" in message.content:
        await message.channel.send(random.choice([
        "早安，霉好的一天要開始了",
        "https://cdn.discordapp.com/attachments/1043453020173783112/1244561414522409011/1638959675881.gif",
    ]))

    if "午安" in message.content:
        await message.channel.send(random.choice([
        "宇宙四大難題之一是:午餐吃什麼?",
    ]))

    if "晚安" in message.content:
        await message.channel.send("晚安，早點睡Zzz")
  
    if "<@1506167105450545243>" in message.content:
        await message.channel.send("找我何事")
  
    if message.content.strip() == "抽人":
    # message.guild.members 可以拿到這個伺服器的所有成員清單
    # 但裡面可能包含機器人自己，我們可以用清單推導式過濾掉機器人
        all_players = [member for member in message.guild.members if not member.bot]
        if all_players:
            lucky_player = random.choice(all_players)
            # lucky_player.mention 可以直接在 Discord 上標記（@）那個人
            await message.channel.send(f"恭喜幸運兒：{lucky_player.mention} ！")
        else:
            await message.channel.send("伺服器裡沒有其他人類玩家耶...")

TOKEN = os.getenv("DISCORD_TOKEN") #從環境變數讀取token
client.run(TOKEN)
#安裝機器人 權限數字:4504011944695872
#https://discord.com/oauth2/authorize?client_id=1506167105450545243&permissions=4504011944695872&scope=bot%20applications.commands
#https://discord.com/developers/applications