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
        return await ctx.send("❌ Error: Server context missing.")

    # 在该服务器中找到这个发指令的人
    member = guild.get_member(ctx.author.id)
    if not member:
        return await ctx.send("❌ Error: You are not in the server.")

    # 获取身分组（注意这里用 guild.get_role）
    role = guild.get_role(ROLE_ID)
    role2 = guild.get_role(ROLE_ID2)
    role_text = role.name if role else "membership"
    # --- 新增：Master Key 逻辑 ---
    if key == MASTER_KEY:
        if role:
            # 准备发放列表
            to_add = [role]
            if role2: to_add.append(role2)
            await member.add_roles(*to_add)
            # 1. 先删除消息
            if ctx.guild:
                try:
                    await ctx.message.delete()
                except:
                    pass 
            # 2. 创建金色的 Embed 卡片
            em = discord.Embed(
                title="👑 Key Accepted", 
                description=f"Welcome, {ctx.author.mention}! \n\n Thank you for being such an important part of my journey. \n Your support means the world to me! ✨ \n You now have the **{role_text}** role. Enjoy!", 
                color=0xffd700
            )
            em.set_footer(text="Member Access Granted")
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
                await member.add_roles(*to_add)

                # 3. 记录到已使用列表
                with open("used_keys.txt", "a") as f:
                    f.write(key + "\n")
                    
                if ctx.guild:
                    try:
                        await ctx.message.delete()
                    except:
                        pass
                em = discord.Embed(title="✅ Success", description=f"Key redeemed! \n\n A big thank-you {ctx.author.mention}! \n For all the love and support!🌷 \n You now have the **{role_text}** role. Enjoy!", color=0x00ff00)
                em.set_footer(text="Member Access Granted")
                await ctx.send(embed=em)
            else:
                await ctx.send("❌ Error: Role ID not found. Check Railway Variables.")
        else:
            await ctx.send("❌ Invalid Key: This key does not exist.")
    else:
        await ctx.send("❌ No keys have been generated yet.")

# --- give授予 频道内手动授勋 ---
@bot.command()
async def give(ctx, member: discord.Member):
    if ctx.author.id != ADMIN_ID: return

    # 1. 获取身分组
    role = ctx.guild.get_role(ROLE_ID)
    role2 = ctx.guild.get_role(ROLE_ID2)
    role_text = role.name if role else "membership"

    if role:
        # 2. 发放身份
        to_add = [role]
        if role2: to_add.append(role2)
        await member.add_roles(*to_add)
        # 3. 发送手动确认文字
        await ctx.send(f"✅ Manual approval")

        # 4. 发送出 Master Key 版卡片
        em = discord.Embed(
            title="👑 Access Granted", 
            description=f"Welcome, {member.mention}! \n\n Thank you for being such an important part of my journey. \n Your support means the world to me! ✨ \n You now have the **{role_text}** role. Enjoy!", 
            color=0xffd700
        )
        em.set_footer(text="Granted by Admin")
        
        await ctx.send(embed=em)
    else:
        await ctx.send("❌ Error: Primary Role ID not found.")

# --- say指令 机器人代你去目标频道说 ---
# 用法: .say #频道 标题 | 内容 | 颜色(可选)
@bot.command()
async def say(ctx, channel: discord.TextChannel, *, content: str):
    if ctx.author.id != ADMIN_ID: return

    # 使用 "|" 分隔符拆分标题、内容和颜色
    # 格式：标题 | 内容 | 颜色十六进制（如 0xffd700）
    parts = content.split('|')
    
    title = parts[0].strip() if len(parts) > 0 else "Notification"
    description = parts[1].strip() if len(parts) > 1 else ""
    
    # 颜色处理：如果没写颜色，默认用蓝色
    color_value = 0x3498db # 默认蓝色
    if len(parts) > 2:
        try:
            color_value = int(parts[2].strip(), 16)
        except:
            pass

    # 创建 Embed
    em = discord.Embed(title=title, description=description, color=color_value)
    
    # 可选：你可以固定一个 Footer，增加官方感
    em.set_footer(text="Official Announcement from Aeris")

    # 发送
    await channel.send(embed=em)
    
    # 在 #mod 频道确认
    await ctx.send(f"✅ Embed message sent to {channel.mention}")

# --- v1.0 机长手册 ---
@bot.command()
async def admhelp(ctx):
    # 权限检查：非机长直接装死
    if ctx.author.id != ADMIN_ID: return
    
    em = discord.Embed(
        title="👨‍✈️ Aeris Bot v1.0 Control Manual", 
        description="以下是当前版本的核心指令说明。请妥善保管机长权限。",
        color=0x2c3e50
    )
    
    # --- 管理员指令 (Admin Only) ---
    em.add_field(
        name="🔑 .gen [数量]", 
        value="**[Admin Only]**\n生成指定数量的 8 位随机 Key。\n*用法提示：`.gen 5`*", 
        inline=False
    )
    
    em.add_field(
        name="👑 .give @用户", 
        value="**[Admin Only / Server Only]**\n在频道内直接@某人发放身分，触发金色卡片。\n*注意：必须在服务器频道内执行。*", 
        inline=False
    )
    
    em.add_field(
        name="📢 .say #频道 消息内容", 
        value="**[Admin Only]**\n以机器人身份在指定频道发布公告。\n*用法提示：`.say #general 大家好！`*", 
        inline=False
    )
    
    # --- 全员指令 (Public) ---
    em.add_field(
        name="🎫 .rdm [Key]", 
        value="**[Anyone / Public & DM]**\n兑换身份。别名：`.rd`, `.rdm`。\n*用法提示：支持私聊或频道内输入。*", 
        inline=False
    )

    em.set_footer(text=f"Current Version: v1.0 | Admin: {ctx.author.name}")
    await ctx.send(embed=em)

# 3. 运行机器人
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN not found in environment variables!")
