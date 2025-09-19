import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import random
import asyncio
from dotenv import load_dotenv

load_dotenv() 
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


#load coin 
COIN_FILE =  "coins.json"

def load_coins():
    if os.path.exists(COIN_FILE):
        with open (COIN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

#luu coin
def save_coins (data):
    with open (COIN_FILE, "w", encoding="utf-8 ") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

coins = load_coins()

@bot.event
async def on_ready():
    print(f"Đàn em đã đăng nhập thành công dưới tên {bot.user}")

#xem so coin dang co
@bot.command()
async def check(ctx):
    user_id = str(ctx.author.id)
    user_coin = coins.get(user_id, {}).get("coin", 0)
    await ctx.send(f"💰 Bé {ctx.author.mention} giàu ghê, bé đang có **{user_coin} coin**")

#diem danh nhan coin
@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if user_id not in coins:
        coins[user_id] = {"coin": 0, "last_daily": ""}

    # kiem tra xem da diem danh chua
    if coins[user_id]["last_daily"] == today:
        await ctx.send(f"📅 Bé {ctx.author.mention} đã điểm danh rồi!")
    else:
        coins[user_id]["coin"] += 50
        coins[user_id]["last_daily"] = today
        save_coins(coins)
        await ctx.send(f"✅ Bé {ctx.author.mention} đã điểm danh và nhận được **50 coin**!")

#tang coin cho nguoi khac
@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    giver_id = str(ctx.author.id)
    receiver_id = str(member.id)

    if amount <= 0:
        await ctx.send("💢 Tặng 0 coin tặng chi má!!!")
        return

    if giver_id not in coins:
        coins[giver_id] = {"coin": 0, "last_daily": ""}
    if receiver_id not in coins:
        coins[receiver_id] = {"coin": 0, "last_daily": ""}

    if coins[giver_id]["coin"] < amount:
        await ctx.send("💸 Mi nghèo quá, không đủ coin để tặng!")
        return

    coins[giver_id]["coin"] -= amount
    coins[receiver_id]["coin"] += amount
    save_coins(coins)

    await ctx.send(f"🤝 Bé {ctx.author.mention} đã tặng **{amount} coin** cho bé {member.mention}!")

#che do an xin
class DonateModal(discord.ui.Modal, title="Nhập số coin để bố thí"):
    amount = discord.ui.TextInput(label="Số coin", placeholder="Nhập số coin muốn bố thí", required=True)

    def __init__(self, giver, beggar, donations, coins):
        super().__init__()
        self.giver = giver
        self.beggar = beggar
        self.donations = donations
        self.coins = coins

    async def on_submit(self, interaction: discord.Interaction):
        giver_id = str(self.giver.id)
        beggar_id = str(self.beggar.id)

        # Dữ liệu user
        if giver_id not in self.coins:
            self.coins[giver_id] = {"coin": 0, "last_daily": ""}
        if beggar_id not in self.coins:
            self.coins[beggar_id] = {"coin": 0, "last_daily": ""}

        try:
            amount = int(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ Có biết nhập số không?!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("💢 Bố thí 0 coin bố thí chi má!!!", ephemeral=True)
            return

        if self.coins[giver_id]["coin"] < amount:
            await interaction.response.send_message("😏 Không đủ coin cũng học đòi đi bố thí! 😏", ephemeral=True)
            return

        # Cập nhật coin
        self.coins[giver_id]["coin"] -= amount
        self.coins[beggar_id]["coin"] += amount
        save_coins(self.coins)

        # Ghi nhận đóng góp
        if giver_id not in self.donations:
            self.donations[giver_id] = 0
        self.donations[giver_id] += amount

        await interaction.response.send_message(
            f"🤲 Thật hào phóng, nhà ngươi đã cho ả tiện tì {self.beggar.mention} **{amount} coin**!", ephemeral=True
        )


class BegView(discord.ui.View):
    def __init__(self, beggar, coins):
        super().__init__(timeout=60)  # 1p
        self.beggar = beggar
        self.coins = coins
        self.donations = {}

    @discord.ui.button(label="Bố thí", style=discord.ButtonStyle.green)
    async def donate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = DonateModal(interaction.user, self.beggar, self.donations, self.coins)
        await interaction.response.send_modal(modal)

    async def on_timeout(self):
        if not self.donations:
            await self.message.channel.send(f"⏰ Thật khó nói! Không ai thèm bố thí cho {self.beggar.mention} luôn ạ...")
        else:
            lines = [f"⏰ Tuyệt vời! Kẻ ăn xin {self.beggar.mention} bội thu được:"]
            for uid, amount in self.donations.items():
                user = await self.message.guild.fetch_member(int(uid))
                lines.append(f"- Bé {user.display_name} đã bố thí cho cưng **{amount} coin**")
            await self.message.channel.send("\n".join(lines))


@bot.command()
async def beg(ctx):
    view = BegView(ctx.author, coins)
    embed = discord.Embed(
        title="🪙 Phiên ăn xin bắt đầu!",
        description=f"{ctx.author.mention} vì đam mê đỏ đen nên đã rơi vào hoàn cảnh nghèo đói, ông bà cô dì chú bác hảo tâm bấm nút bên dưới để bố thí!",
        color=discord.Color.gold()
    )
    msg = await ctx.send(embed=embed, view=view)
    view.message = msg


# ====== NỐI CHỮ ======
game_active = False
current_word = None
used_words = []
last_player = None

# Load từ điển tiếng Việt (1 từ mỗi dòng trong file)
with open("bigrams.txt", "r", encoding="utf-8") as f:
    valid_phrases = set(line.strip().lower() for line in f if line.strip())


@bot.command()
async def noichu(ctx):
    global game_active, current_word, used_words, last_player
    if game_active:
        await ctx.send("⚠️ Trò chơi nối chữ đã bắt đầu rồi!")
        return
    game_active = True
    current_word = None
    used_words = []
    last_player = None
    await ctx.send("🎮 Trò chơi **nối chữ** đã bắt đầu! Ai đó hãy xổ chữ đầu tiên đi")

@bot.command()
async def stopnoichu(ctx):
    global game_active, current_word, used_words, last_player
    if not game_active:
        await ctx.send("✘ Hiện không có trò nối chữ nào đang diễn ra.")
        return
    
    game_active = False
    if last_player:
        user_id = str(last_player.id)
        if user_id not in coins:
            coins[user_id] = {"coin": 0, "last_daily": ""}
        coins[user_id]["coin"] += 1000
        save_coins(coins)
        await ctx.send(f"🏆 Không nối được nữa, {last_player.mention} chiến thắng và nhận **1000 coin**!")
    else:
        await ctx.send("⏹ Trò chơi nối chữ đã kết thúc mà không có người chơi nào.")

@bot.event
async def on_message(message):
    global game_active, current_word, used_words, last_player

    if message.author.bot:
        return  

    if game_active and not message.content.startswith("!"):
        text = message.content.strip().lower()
        words = text.split()  # tách thành list từ

        # Check người chơi liên tiếp
        if last_player and message.author == last_player:
            await message.channel.send("👊 Mi vừa mới nối rồi, lượt người khác!")
            return

        # Check số từ
        if len(words) != 2:
            await message.channel.send("✘ Cụm từ phải chứa đúng 2 từ!")
            return

        # Check cụm từ có hợp lệ không
        if text not in valid_phrases:
            await message.add_reaction("❌")
            await message.channel.send(f"Cụm từ **{text}** không tồn tại trong từ điển!")
            return

        if current_word is None:
            # từ/cụm đầu tiên
            current_word = words[-1]  # lấy từ cuối
            used_words.append(text)
            last_player = message.author
            user_id = str(message.author.id)
            coins.setdefault(user_id, {"coin": 0, "last_daily": ""})
            coins[user_id]["coin"] += 100
            save_coins(coins)
            await message.add_reaction("✅")

        else:
            if text in used_words:
                await message.add_reaction("❌")
                await message.channel.send(f"Cụm từ **{text}** đã được dùng rồi!")
            elif words[0] != current_word:
                await message.add_reaction("❌")
                await message.channel.send(f"Cụm từ phải bắt đầu bằng từ **{current_word}**!")
            else:
                current_word = words[-1]  # cập nhật từ cuối
                used_words.append(text)
                last_player = message.author
                user_id = str(message.author.id)
                coins.setdefault(user_id, {"coin": 0, "last_daily": ""})
                coins[user_id]["coin"] += 100
                save_coins(coins)
                await message.add_reaction("✅")               

                # Check còn nối tiếp được không
                possible_next = any(
                    p.startswith(current_word + " ") for p in valid_phrases
                )
                if not possible_next:
                    coins[user_id]["coin"] += 1000
                    save_coins(coins)
                    await message.channel.send(
                        f"🏆 {message.author.mention} đã chặn đường! "
                        f"🥳 Không còn cụm nào nối tiếp được → nhận thêm **1000 coin**! 🥳"
                    )
                    game_active = False  # kết thúc trò chơi

    await bot.process_commands(message)




#test hello
@bot.command()
async def hello(ctx):
    await ctx.send("Hê lô người đẹp -.-")



#dung co matday voi dan em xitin
@bot.event
async def on_message(message):
    global game_active, current_word, used_words, last_player

    if message.author.bot:
        return  

    if "bot ngu" in message.content.lower():
        await message.channel.send(f"{message.author.mention} mày ngu 😇")

bot.run(TOKEN)
