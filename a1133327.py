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
file_exp_claim = "exp_claim.json" # 吐納領取記錄檔

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

#===讀取story.json的函數===
def load_story():
    if not os.path.exists(file_story):
        return {}
    with open(file_story, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

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
@tree.command(name="blackjack", description="遊玩21點")
async def blackjack(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    # 讀取並初始化玩家的黑傑克統計
    with open("game.json", "r", encoding="utf-8") as f:
        game_data = json.load(f)

    if user_id not in game_data:
        game_data[user_id] = {}

    if "blackjack_wins" not in game_data[user_id]:
        game_data[user_id]["blackjack_wins"] = 0
    if "blackjack_losses" not in game_data[user_id]:
        game_data[user_id]["blackjack_losses"] = 0

    def save_game():
        with open("game.json", "w", encoding="utf-8") as f:
            json.dump(game_data, f, ensure_ascii=False, indent=2)

    def get_stats():
        wins = game_data[user_id]["blackjack_wins"]
        losses = game_data[user_id]["blackjack_losses"]
        total = wins + losses
        rate = f"{(wins / total * 100):.1f}%" if total > 0 else "N/A"
        return wins, losses, total, rate

    SUIT_MAP = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}

    def create_deck():
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = [f"{rank}{suit}" for suit in suits for rank in ranks]
        random.shuffle(deck)
        return deck

    def card_value(card):
        rank = card[:-1]
        if rank in ['J', 'Q', 'K']:
            return 10
        elif rank == 'A':
            return 11
        else:
            return int(rank)

    def hand_value(hand):
        value = sum(card_value(c) for c in hand)
        aces = sum(1 for c in hand if c[:-1] == 'A')
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def hand_str(hand):
        return ' '.join(hand)

    deck = create_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]

    class BlackjackView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.ended = False

        def get_embed(self):
            pv = hand_value(player_hand)
            wins, losses, total, rate = get_stats()

            embed = discord.Embed(title="🃏 21點 Blackjack", color=discord.Color.green())
            embed.add_field(
                name=f"你的手牌（{pv}點）",
                value=hand_str(player_hand),
                inline=False
            )
            embed.add_field(
                name="莊家手牌（?點）",
                value=f"{dealer_hand[0]} 🂠",
                inline=False
            )
            embed.set_footer(text=f"勝 {wins} | 負 {losses} | 總場次 {total} | 勝率 {rate}")
            return embed

        def end_embed(self, result: str):
            pv = hand_value(player_hand)
            dv = hand_value(dealer_hand)
            wins, losses, total, rate = get_stats()

            if result == "win":
                color = discord.Color.gold()
                title = "🎉 你贏了！"
            elif result == "lose":
                color = discord.Color.red()
                title = "💀 你輸了！"
            elif result == "bust":
                color = discord.Color.red()
                title = "💥 爆牌！你輸了！"
            elif result == "dealer_bust":
                color = discord.Color.gold()
                title = "🎉 莊家爆牌！你贏了！"
            else:
                color = discord.Color.blue()
                title = "🤝 平局！"

            embed = discord.Embed(title=title, color=color)
            embed.add_field(
                name=f"你的手牌（{pv}點）",
                value=hand_str(player_hand),
                inline=False
            )
            embed.add_field(
                name=f"莊家手牌（{dv}點）",
                value=hand_str(dealer_hand),
                inline=False
            )
            embed.set_footer(text=f"勝 {wins} | 負 {losses} | 總場次 {total} | 勝率 {rate}")
            return embed

        def record_result(self, result: str):
            if result in ("win", "dealer_bust"):
                game_data[user_id]["blackjack_wins"] += 1
            elif result in ("lose", "bust"):
                game_data[user_id]["blackjack_losses"] += 1
            # 平局不計
            save_game()

        @discord.ui.button(label="要牌 Hit", style=discord.ButtonStyle.primary, emoji="➕")
        async def hit(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
            if interaction_btn.user.id != interaction.user.id:
                await interaction_btn.response.send_message("這不是你的遊戲！", ephemeral=True)
                return
            if self.ended:
                return

            player_hand.append(deck.pop())
            pv = hand_value(player_hand)

            if pv > 21:
                self.ended = True
                self.disable_game_buttons()
                self.record_result("bust")
                self.add_item(self.replay_button())
                await interaction_btn.response.edit_message(
                    embed=self.end_embed("bust"), view=self
                )
            elif pv == 21:
                await self.resolve(interaction_btn)
            else:
                await interaction_btn.response.edit_message(
                    embed=self.get_embed(), view=self
                )

        @discord.ui.button(label="停牌 Stand", style=discord.ButtonStyle.danger, emoji="✋")
        async def stand(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
            if interaction_btn.user.id != interaction.user.id:
                await interaction_btn.response.send_message("這不是你的遊戲！", ephemeral=True)
                return
            if self.ended:
                return

            await self.resolve(interaction_btn)

        async def resolve(self, interaction_btn: discord.Interaction):
            self.ended = True
            self.disable_game_buttons()

            while hand_value(dealer_hand) < 17:
                dealer_hand.append(deck.pop())

            pv = hand_value(player_hand)
            dv = hand_value(dealer_hand)

            if dv > 21:
                result = "dealer_bust"
            elif pv > dv:
                result = "win"
            elif pv < dv:
                result = "lose"
            else:
                result = "draw"

            self.record_result(result)
            self.add_item(self.replay_button())

            await interaction_btn.response.edit_message(
                embed=self.end_embed(result), view=self
            )

        def replay_button(self):
            btn = discord.ui.Button(
                label="再來一局", 
                style=discord.ButtonStyle.success, 
                emoji="🔄"
            )
            async def replay_callback(interaction_btn: discord.Interaction):
                if interaction_btn.user.id != interaction.user.id:
                    await interaction_btn.response.send_message("這不是你的遊戲！", ephemeral=True)
                    return

                # 重新開始遊戲
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
                        embed=new_view.end_embed(result), view=new_view
                    )
                else:
                    await interaction_btn.response.edit_message(
                        embed=new_view.get_embed(), view=new_view
                    )

            btn.callback = replay_callback
            return btn

        def disable_game_buttons(self):
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label in ("要牌 Hit", "停牌 Stand"):
                    item.disabled = True

        def disable_all(self):
            for item in self.children:
                item.disabled = True

        async def on_timeout(self):
            self.disable_all()

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
            embed=view.end_embed(result), view=view
        )
    else:
        await interaction.response.send_message(
            embed=view.get_embed(), view=view
        )
#========================================================

# === 查詢玩家資料 (卡片) ===
@tree.command(name="card", description="查詢玩家基本資料")
async def card(interaction: discord.Interaction):
    user = interaction.user
    user_id = str(user.id)

    # 讀取現有資料庫
    data = load_game()
    level_data = load_level_data()

    # 檢查玩家是否已經在資料庫中 [3]
    if user_id not in data:
        data[user_id] = {
            "name": user.name,
            "level": 1,
            "exp": 0
        }
        save_game(data)
    else:
        # 防呆機制：幫舊玩家補上 exp 欄位 [3]
        if "exp" not in data[user_id]:
            data[user_id]["exp"] = 0
            save_game(data)
    
    player_level = data[user_id]["level"]
    player_exp = data[user_id]["exp"]
    
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
    #embed.add_field(name="等級⭐", value=str(player_level), inline=True)
    embed.add_field(name="⭐經驗值", value=exp_display, inline=False)
    
    # 寄出/輸出這張卡片 [1]
    await interaction.response.send_message(embed=embed)

# === 吐納指令 ===
@tree.command(name="exp", description="吐納：獲得少量經驗值（每整點可領取一次）")
async def exp(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    # --- 取得當前小時標識（例如 "2025-01-15-14"）---
    now = datetime.now()
    current_hour_key = now.strftime("%Y-%m-%d-%H")
    
    # --- 讀取領取記錄 ---
    claim_data = load_exp_claim()
    
    if claim_data.get(user_id) == current_hour_key:
        # 本小時已領取
        await interaction.response.send_message(
            f"你這個小時已經吐納過了，下個整點再來吧！\n"
            f"（每小時整點刷新，現在是 **{now.strftime('%H')} 點**）"
        )
        return
    
    # --- 讀取玩家資料 ---
    data = load_game()
    
    if user_id not in data:
        data[user_id] = {
            "name": interaction.user.name,
            "level": 1,
            "exp": 0,
            "exp_multiplier": 1.00
        }
    
    player = data[user_id]
    
    # 防呆：補上缺少的欄位
    if "exp_multiplier" not in player:
        player["exp_multiplier"] = 1.00
    
    level = player.get("level", 1)
    multiplier = player.get("exp_multiplier", 1.00)
    
    # --- 計算經驗值 ---
    gained_exp = int(level * 50 * multiplier)
    player["exp"] = player.get("exp", 0) + gained_exp
    
    # --- 儲存 ---
    save_game(data)
    claim_data[user_id] = current_hour_key
    save_exp_claim(claim_data)
    
    await interaction.response.send_message(
        f"🧘 吐納成功！\n"
        f"獲得 **{gained_exp}** 點經驗值（等級 {level} × 50 × {multiplier:.2f}）\n"
        f"目前總經驗：**{player['exp']}**"
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
        "午安!",
        "午安，要找本體的話他估計還沒醒喔",
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