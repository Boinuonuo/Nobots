import discord
from discord.ext import commands
import uuid
import os
import secrets
import string

# 1. 从 Railway 的 Variables 读取配置
TOKEN = os.getenv('DISCORD_TOKEN')
ROLE_ID = int(os.getenv('ROLE_ID')) if os.getenv('ROLE_ID') else None
ROLE_ID2 = int(os.getenv('ROLE_ID2')) if os.getenv('ROLE_ID2') else None 
ADMIN_ID = int(os.getenv('ADMIN_ID')) if os.getenv('ADMIN_ID') else None
GUILD_ID = int(os.getenv('GUILD_ID')) if os.getenv('GUILD_ID') else None
MASTER_KEY = os.getenv('MASTER_KEY')


# 设置机器人指令前缀和意图
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot is online as {bot.user.name}")

# --- gen生成 Key 的指令 ---
@bot.command()
async def gen(ctx, amount: int):
    if ctx.author.id != ADMIN_ID: return
    # 只有你能运行这个指令（简单判断，防止粉丝乱刷）
    # if str(ctx.author.id) != os.getenv('ADMIN_ID'): return
    
    keys = []
    # 确保文件存在，防止读取报错
    if not os.path.exists("keys.txt"): open("keys.txt", "w").close()
    
    chars = string.ascii_uppercase + string.digits # 包含大写字母和数字
    
    with open("keys.txt", "a") as f:
        for _ in range(amount):
            key = ''.join(secrets.choice(chars) for _ in range(8))
            keys.append(key)
            f.write(key + "\n")
    
    keys_str = "\n".join(keys)
    await ctx.send(f"🔑 **Generated {amount} Keys:**\n```\n{keys_str}\n```")

# --- rd兑换 Key 的指令 ---
@bot.command(aliases=['rdm', 'rd'])
async def redeem(ctx, key: str):
    # 无论在不在频道，都通过 GUILD_ID 找到你的服务器
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return await ctx.send("❌ Bot configuration error: Guild not found.")

    # 在该服务器中找到这个发指令的人
    member = guild.get_member(ctx.author.id)
    if not member:
        return await ctx.send("❌ You are not a member of the server!")

    # 获取身分组（注意这里用 guild.get_role）
    role = guild.get_role(ROLE_ID)
    role2 = guild.get_role(ROLE_ID2)
    # --- 新增：Master Key 逻辑 ---
    if key == MASTER_KEY:
        if role:
            # 准备发放列表
            to_add = [role]
            if role2: to_add.append(role2)
            await ctx.author.add_roles(*to_add)
            # 1. 先删除消息
            if ctx.guild:
                try:
                    await ctx.message.delete()
                except:
                    pass 
            # 2. 创建金色的 Embed 卡片
            em = discord.Embed(
                title="👑 Key Accepted", 
                description=f"Welcome, {ctx.author.mention}! \n\nThank you for being such an important part of my journey. \n\nYour support means the world to me! ✨ \n\nYou now have the **{role.name}** role. Enjoy!", 
                color=0xffd700
            )
            em.set_footer(text="Special Access Granted")
            # 3. 发送卡片并结束函数
            return await ctx.send(embed=em)
    # ---------------------------
    # 1. 检查是否已经用过
    if os.path.exists("used_keys.txt"):
        with open("used_keys.txt", "r") as f:
            if key in f.read():
                em = discord.Embed(title="❌ Invalid", description="This key has already been used!", color=0xff0000)
                return await ctx.send(embed=em)

    # 2. 检查是否存在于生成的 Key 列表中
    if os.path.exists("keys.txt"):
        with open("keys.txt", "r") as f:
            all_keys = f.read().splitlines()
        
        if key in all_keys:
            # 找到对应的身分组
            if role:
                # 1. 准备发放列表
                to_add = [role]
                if role2: 
                    to_add.append(role2)
                
                # 2. 一次性发放身分组
                await ctx.author.add_roles(*to_add)

                # 3. 记录到已使用列表
                with open("used_keys.txt", "a") as f:
                    f.write(key + "\n")
                    
                if ctx.guild:
                    try:
                        await ctx.message.delete()
                    except:
                        pass
                em = discord.Embed(title="✅ Success", description=f"Key redeemed! \n\nA big thank-you for all the love and support!🌷 \n\nYou now have the **{role.name}** role. Enjoy!", color=0x00ff00)
                em.set_footer(text="Special Access Granted")
                await ctx.send(embed=em)
            else:
                await ctx.send("❌ Error: Role ID not found. Check Railway Variables.")
        else:
            await ctx.send("❌ Invalid Key: This key does not exist.")
    else:
        await ctx.send("❌ No keys have been generated yet.")

# 3. 运行机器人
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN not found in environment variables!")
