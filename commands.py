import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional

from db import DB
from mmr import team_mmr_from_members

db = DB()

def mmr_to_tier(mmr: int) -> str:
    # Simple tier mapping; adjust ranges as needed
    if mmr >= 1600:
        return 'SS'
    if mmr >= 1400:
        return 'S'
    if mmr >= 1200:
        return 'A'
    if mmr >= 1000:
        return 'B'
    return 'C'

def parse_member_input(member_str: str) -> List[str]:
    """Parse a space-separated member input which may contain mentions like <@!123> or raw IDs."""
    out = []
    for token in member_str.split():
        t = token.strip()
        # mention formats: <@123...> or <@!123...>
        if t.startswith('<@') and t.endswith('>'):
            t = t.lstrip('<@!').rstrip('>')
        out.append(t)
    return out

def setup_commands(bot: commands.Bot):
    # prefix command
    @bot.command(name='랭킹')
    async def ranking_prefix(ctx: commands.Context):
        await ranking(ctx)

    @bot.command(name='팀등록')
    async def register_prefix(ctx: commands.Context, team_name: str, *member_ids: str):
        # 서버 채널 + 호출자 권한 확인 (관리자 또는 서버관리)
        if ctx.guild is None:
            await ctx.send('이 명령은 서버 채널에서만 사용할 수 있습니다.')
            return
        perms = getattr(ctx.author, 'guild_permissions', None)
        if not perms or not (perms.administrator or perms.manage_guild):
            await ctx.send('관리자 또는 서버 관리 권한이 있어야 사용할 수 있습니다.')
            return
        # member_ids expected to be discord IDs or mentions; store raw strings for now
        await register_team(ctx, team_name, list(member_ids))

    # slash commands
    @bot.tree.command(name='랭킹', description='MMR 랭킹 확인')
    async def ranking(interaction: discord.Interaction):
        await interaction.response.defer()
        # Simple ranking: list top players by mmr_general
        await db.ensure()
        tops = await db.list_top_players(10, use_regular=False)
        if not tops:
            await interaction.followup.send('랭킹 데이터가 없습니다. 플레이어를 추가하세요.')
            return
        # Build an embed similar to the screenshot: emoji, name, mmr, wins/losses, winrate, max mmr
        embed = discord.Embed(title='🏅 MMR Top 10', color=0xf1c40f)
        for i, p in enumerate(tops):
            win = p.get('wins', 0) or 0
            loss = p.get('losses', 0) or 0
            gp = p.get('games_played', 0) or 0
            winrate = f"{(win/gp*100):.1f}%" if gp > 0 else '0%'
            name = p.get('name')
            mmr = p.get('mmr')
            max_mmr = p.get('max_mmr')
            emoji = '🥇' if i == 0 else ('🥈' if i == 1 else ('🥉' if i == 2 else '🔹'))
            tier = mmr_to_tier(mmr if mmr is not None else 1200)
            embed.add_field(name=f"{emoji} {i+1}. {name} ({tier})", value=f"MMR: {mmr} · 전적: {win}승 {loss}패 · 승률: {winrate} · 최고 MMR: {max_mmr}", inline=False)
        await interaction.followup.send(embed=embed)

    # Slash command version: accept up to 6 Member options for better UX
    @bot.tree.command(name='팀등록', description='팀 등록: 팀명 + 멤버(최대 6명) + (선택)시드MMR')
    @app_commands.guild_only()
    @app_commands.describe(team_name='팀 이름', seed='선택 시드 MMR')
    async def register_team(
        interaction: discord.Interaction,
        team_name: str,
        member1: Optional[discord.Member] = None,
        member2: Optional[discord.Member] = None,
        member3: Optional[discord.Member] = None,
        member4: Optional[discord.Member] = None,
        member5: Optional[discord.Member] = None,
        member6: Optional[discord.Member] = None,
        seed: int = 0,
    ):
        # 서버 채널 + 호출자 권한 확인 (관리자 또는 서버관리)
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message('이 명령은 서버 채널에서만 사용할 수 있습니다.', ephemeral=True)
            return
        user_perms = interaction.user.guild_permissions
        if not (user_perms.administrator or user_perms.manage_guild):
            await interaction.response.send_message('관리자 또는 서버 관리 권한이 있어야 사용할 수 있습니다.', ephemeral=True)
            return
        await interaction.response.defer()
        members = [m for m in (member1, member2, member3, member4, member5, member6) if m is not None]
        ids = [str(m.id) for m in members]
        # validation
        if not ids:
            await interaction.followup.send('적어도 한 명 이상의 멤버를 멘션으로 선택해야 합니다.')
            return
        if len(ids) > 6:
            await interaction.followup.send('최대 6명까지 등록할 수 있습니다.')
            return
        if len(set(ids)) != len(ids):
            await interaction.followup.send('중복된 멤버가 있습니다. 동일한 유저는 한 번만 선택하세요.')
            return
        await db.ensure()
        # upsert players with seed mmr if provided
        for pid in ids:
            await db.upsert_player(pid, str(pid), regular=seed if seed else 1200, general=seed if seed else 1200)
        await db.register_team(team_name, ids, seed)
        await interaction.followup.send(f'팀 **{team_name}** 이(가) 등록되었습니다. 시드: {seed} 멤버: {len(ids)}')

    @bot.tree.command(name='기록', description='경기 기록: /기록 teamA_ids | teamB_ids | winner(A/B)')
    async def record(interaction: discord.Interaction, team_a: str, team_b: str, winner: str):
        await interaction.response.defer()
        a_ids = [x.strip() for x in team_a.split()] if team_a else []
        b_ids = [x.strip() for x in team_b.split()] if team_b else []
        # basic validation
        if winner not in ('A', 'B'):
            await interaction.followup.send('승자에는 A 또는 B만 입력하세요.')
            return
        if not a_ids or not b_ids:
            await interaction.followup.send('양 팀 모두 최소 1명 이상이어야 합니다.')
            return
        if len(a_ids) > 6 or len(b_ids) > 6:
            await interaction.followup.send('각 팀은 최대 6명까지 허용됩니다.')
            return
        # no overlapping players
        if set(a_ids) & set(b_ids):
            await interaction.followup.send('같은 유저가 양 팀에 중복으로 포함될 수 없습니다.')
            return
        await db.ensure()
        await db.record_match(a_ids, b_ids, winner, use_regular=False)
        await interaction.followup.send(f'기록 완료: {len(a_ids)} vs {len(b_ids)} 승자: {winner}')

    @bot.tree.command(name='디버그', description='봇 상태 진단 (관리자 전용)')
    @app_commands.guild_only()
    async def debug(interaction: discord.Interaction):
        # 서버 채널에서만 허용 + 안전한 권한 체크 (DM에서는 Member 타입이 아님)
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message('이 명령은 서버 채널에서만 사용할 수 있습니다.', ephemeral=True)
            return
        user_perms = interaction.user.guild_permissions
        if not (user_perms.administrator or user_perms.manage_guild):
            await interaction.response.send_message('관리자 또는 서버 관리 권한이 있어야 사용할 수 있습니다.', ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        bot = interaction.client
        guild = interaction.guild
        lines = []
        lines.append(f'Bot user: {bot.user} (id={bot.user.id})')
        if guild:
            lines.append(f'Guild: {guild.name} (id={guild.id})')
        else:
            lines.append('Guild: (None)')
        intents = getattr(bot, 'intents', None)
        if intents is not None:
            lines.append(f'Intents: message_content={getattr(intents, "message_content", False)}, members={getattr(intents, "members", False)}')
        # bot permissions in this guild (attempt)
        try:
            me = guild.get_member(bot.user.id) if guild else None
            if me is None and guild:
                me = await guild.fetch_member(bot.user.id)
            if me:
                perms = me.guild_permissions
                lines.append(f'Bot perms (guild): administrator={perms.administrator}, send_messages={perms.send_messages}, manage_guild={perms.manage_guild}')
        except Exception as e:
            lines.append(f'Bot perms: could not fetch ({e})')

        # DB summary
        try:
            import sqlite3
            conn = sqlite3.connect('mmr_bot.db')
            cur = conn.cursor()
            for t in ('players','teams','matches'):
                try:
                    cur.execute(f'SELECT COUNT(*) FROM {t}')
                    cnt = cur.fetchone()[0]
                    lines.append(f'{t}: {cnt} rows')
                except Exception:
                    lines.append(f'{t}: (table missing)')
            conn.close()
        except Exception as e:
            lines.append(f'DB check failed: {e}')

        # Send result
        await interaction.followup.send('\n'.join(lines), ephemeral=True)

    async def register_team(ctx_or_interaction, team_name: str, member_ids: List[str]):
        # fallback for prefix command
        if isinstance(ctx_or_interaction, commands.Context):
            ctx = ctx_or_interaction
            await db.ensure()
            await db.register_team(team_name, member_ids, 0)
            await ctx.send(f'팀 **{team_name}** 등록 완료. 멤버 수: {len(member_ids)}')

    @bot.command(name='기록')
    async def record_prefix(ctx: commands.Context, team_a: str, team_b: str, winner: str):
        # usage: !기록 "id1 id2" "id3 id4" A
        a_ids = [x.strip() for x in team_a.split()]
        b_ids = [x.strip() for x in team_b.split()]
        # validation (same rules as slash)
        if winner not in ('A', 'B'):
            await ctx.send('승자에는 A 또는 B만 입력하세요.')
            return
        if not a_ids or not b_ids:
            await ctx.send('양 팀 모두 최소 1명 이상이어야 합니다.')
            return
        if len(a_ids) > 6 or len(b_ids) > 6:
            await ctx.send('각 팀은 최대 6명까지 허용됩니다.')
            return
        if set(a_ids) & set(b_ids):
            await ctx.send('같은 유저가 양 팀에 중복으로 포함될 수 없습니다.')
            return
        await db.ensure()
        await db.record_match(a_ids, b_ids, winner, use_regular=False)
        await ctx.send(f'기록 완료: {len(a_ids)} vs {len(b_ids)} 승자: {winner}')
