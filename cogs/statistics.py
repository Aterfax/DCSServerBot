# statistics.py
import discord
import matplotlib.pyplot as plt
import numpy as np
import string
import os
from contextlib import closing, suppress
from datetime import timedelta
from discord.ext import commands
from matplotlib.patches import ConnectionPatch
from sqlite3 import Error


class Statistics(commands.Cog):

    WEEKDAYS = {
        0: 'Sun',
        1: 'Mon',
        2: 'Tue',
        3: 'Wed',
        4: 'Thu',
        5: 'Fri',
        6: 'Sat'
    }

    def __init__(self, bot):
        self.bot = bot

    @commands.command(description='Links a member to a DCS user', usage='<member> <ucid>')
    @commands.has_any_role('Admin', 'Moderator')
    @commands.guild_only()
    async def link(self, ctx, member: discord.Member, ucid):
        try:
            with closing(self.bot.conn.cursor()) as cursor:
                cursor.execute('UPDATE players SET discord_id = ? WHERE ucid = ?', (member.id, ucid))
                self.bot.conn.commit()
                await ctx.send('Member {} linked to ucid {}'.format(member.display_name, ucid))
        except (Exception, Error) as error:
            self.bot.conn.rollback()
            self.bot.log.exception(error)

    def draw_playtime_planes(self, member, axis):
        SQL_PLAYTIME = 'SELECT s.slot, ROUND(SUM(JULIANDAY(s.hop_off) - JULIANDAY(s.hop_on))*86400) AS playtime FROM statistics s, players p WHERE s.player_ucid = p.ucid AND p.discord_id = ? AND s.hop_off IS NOT NULL GROUP BY s.slot ORDER BY 2'
        with closing(self.bot.conn.cursor()) as cursor:
            result = cursor.execute(SQL_PLAYTIME, (member.id, )).fetchall()
            if (result is not None):
                labels = []
                values = []
                for row in result:
                    labels.insert(0, row['slot'])
                    values.insert(0, row['playtime'] / 3600.0)
                axis.bar(labels, values, width=0.5, color='mediumaquamarine')
                # axis.set_xticklabels(axis.get_xticklabels(), rotation=45, ha='right')
                for label in axis.get_xticklabels():
                    label.set_rotation(30)
                    label.set_ha('right')
                axis.set_title('Overall Flighttimes per Plane', color='white', fontsize=25)
                # axis.set_yscale('log')
                axis.set_yticks([])
                for i in range(0, len(values)):
                    axis.annotate('{:.1f} h'.format(values[i]), xy=(
                        labels[i], values[i]), ha='center', va='bottom', weight='bold')
            else:
                axis.axis('off')

    def draw_server_time(self, member, axis):
        SQL_STATISTICS = 'SELECT trim(m.server_name) as server_name, ROUND(SUM(JULIANDAY(s.hop_off) - JULIANDAY(s.hop_on))*86400) AS playtime FROM statistics s, players p, missions m WHERE s.player_ucid = p.ucid AND p.discord_id = ? AND m.id = s.mission_id AND s.hop_off IS NOT NULL GROUP BY trim(m.server_name)'
        with closing(self.bot.conn.cursor()) as cursor:
            result = cursor.execute(SQL_STATISTICS, (member.id, )).fetchall()
            if (result is not None):
                def func(pct, allvals):
                    absolute = int(round(pct/100.*np.sum(allvals)))
                    return '{:.1f}%\n({:s}h)'.format(pct, str(timedelta(seconds=absolute)))

                labels = []
                values = []
                for row in result:
                    labels.insert(0, row['server_name'][17:])
                    values.insert(0, row['playtime'])
                patches, texts, pcts = axis.pie(values, labels=labels, autopct=lambda pct: func(pct, values),
                                                wedgeprops={'linewidth': 3.0, 'edgecolor': 'black'}, normalize=True)
                plt.setp(pcts, color='black', fontweight='bold')
                axis.set_title('Server Time', color='white', fontsize=25)
                axis.axis('equal')
            else:
                axis.set_visible(False)

    def draw_recent(self, member, axis):
        SQL_STATISTICS = 'SELECT strftime(\'%m/%d\', s.hop_on) as day, ROUND(SUM(JULIANDAY(s.hop_off) - JULIANDAY(s.hop_on))*86400) AS playtime ' \
            'FROM statistics s, players p WHERE s.player_ucid = p.ucid AND p.discord_id = ? AND date(s.hop_on) > date(\'now\', \'-7 days\') GROUP BY day'
        with closing(self.bot.conn.cursor()) as cursor:
            result = cursor.execute(SQL_STATISTICS, (member.id, )).fetchall()
            labels = []
            values = []
            for row in result:
                labels.append(row['day'])
                values.append(row['playtime'] / 3600.0)
            axis.bar(labels, values, width=0.5, color='mediumaquamarine')
            axis.set_title('Recent Activities', color='white', fontsize=25)
            # axis.set_yscale('log')
            axis.set_yticks([])
            for i in range(0, len(values)):
                axis.annotate('{:.1f} h'.format(values[i]), xy=(
                    labels[i], values[i]), ha='center', va='bottom', weight='bold')
            if (len(values) == 0):
                axis.set_xticks([])
                axis.text(0, 0, 'No data available.', ha='center', va='center', rotation=45, size=15)

    def draw_flight_performance(self, member, axis):
        SQL_STATISTICS = 'SELECT SUM(ejections) as ejections, SUM(crashes) as crashes, ' \
            'SUM(takeoffs) as takeoffs, SUM(landings) as landings FROM statistics s, ' \
            'players p WHERE s.player_ucid = p.ucid AND p.discord_id = ?'
        with closing(self.bot.conn.cursor()) as cursor:
            result = cursor.execute(SQL_STATISTICS, (member.id, )).fetchone()
            if (result[0] is not None):
                def func(pct, allvals):
                    absolute = int(round(pct/100.*np.sum(allvals)))
                    return '{:.1f}%\n({:d})'.format(pct, absolute)

                labels = []
                values = []
                for item in dict(result).items():
                    if(item[1] is not None and item[1] > 0):
                        labels.append(string.capwords(item[0]))
                        values.append(item[1])
                patches, texts, pcts = axis.pie(values, labels=labels, autopct=lambda pct: func(pct, values),
                                                wedgeprops={'linewidth': 3.0, 'edgecolor': 'black'}, normalize=True)
                plt.setp(pcts, color='black', fontweight='bold')
                axis.set_title('Flying', color='white', fontsize=25)
                axis.axis('equal')
            else:
                axis.set_visible(False)

    def draw_kill_performance(self, member, axis):
        SQL_STATISTICS = 'SELECT SUM(kills) as kills, SUM(deaths) as deaths, SUM(teamkills) as teamkills FROM statistics s, ' \
            'players p WHERE s.player_ucid = p.ucid AND p.discord_id = ?'
        with closing(self.bot.conn.cursor()) as cursor:
            result = cursor.execute(SQL_STATISTICS, (member.id, )).fetchone()
            retval = []
            if (result[0] is not None):
                def func(pct, allvals):
                    absolute = int(round(pct/100.*np.sum(allvals)))
                    return '{:.1f}%\n({:d})'.format(pct, absolute)

                labels = []
                values = []
                explode = []
                for item in dict(result).items():
                    if(item[1] is not None and item[1] > 0):
                        labels.append(string.capwords(item[0]))
                        values.append(item[1])
                        if (item[0] in ['deaths', 'kills']):
                            retval.append(item[0])
                            explode.append(0.1)
                        else:
                            explode.append(0.0)
                angle1 = -180 * result[0]/np.sum(values)
                angle2 = 180 - 180*result[1]/np.sum(values)
                if (angle1 == 0):
                    angle = angle2
                elif (angle2 == 180):
                    angle = angle1
                else:
                    angle = angle1 + (angle2 + angle1) / 2

                patches, texts, pcts = axis.pie(values, labels=labels, startangle=angle, explode=explode,
                                                autopct=lambda pct: func(pct, values), colors=['lightgreen', 'darkorange', 'lightblue'],
                                                wedgeprops={'linewidth': 3.0, 'edgecolor': 'black'}, normalize=True)
                plt.setp(pcts, color='black', fontweight='bold')
                axis.set_title('Kill/Death-Ratio', color='white', fontsize=25)
                axis.axis('equal')
            else:
                axis.set_visible(False)
            return retval

    def draw_kill_types(self, member, axis):
        SQL_STATISTICS = 'SELECT SUM(kills_planes) as planes, SUM(kills_helicopters) helicopters, SUM(kills_ships) as ships, ' \
            'SUM(kills_sams) as air_defence, SUM(kills_ground) as ground FROM statistics s, ' \
            'players p WHERE s.player_ucid = p.ucid AND p.discord_id = ?'
        with closing(self.bot.conn.cursor()) as cursor:
            result = cursor.execute(SQL_STATISTICS, (member.id, )).fetchone()
            # if no data was found, return False as no chart was drawn
            if (result[0] is None):
                return False

            labels = []
            values = []
            for item in dict(result).items():
                labels.append(string.capwords(item[0], sep='_').replace('_', ' '))
                values.append(item[1])
            xpos = 0
            bottom = 0
            width = 0.2
            # there is nothing to be drawn
            if (np.sum(values) == 0):
                return False
            for i in range(len(values)):
                height = values[i]/np.sum(values)
                axis.bar(xpos, height, width, bottom=bottom)
                ypos = bottom + axis.patches[i].get_height() / 2
                bottom += height
                if (int(values[i]) > 0):
                    axis.text(xpos, ypos, "%d%%" % (axis.patches[i].get_height() * 100), ha='center', color='black')

            axis.set_title('Killed by\nPlayer', color='white', fontsize=15)
            axis.axis('off')
            axis.set_xlim(- 2.5 * width, 2.5 * width)
            axis.legend(labels, fontsize=15, loc=3, ncol=5, mode='expand',
                        bbox_to_anchor=(-1.8, -0.2, 2.2, 0.4), columnspacing=1, frameon=False)
            # Chart was drawn, return True
            return True

    def draw_death_types(self, member, axis, legend):
        SQL_STATISTICS = 'SELECT SUM(deaths_planes) as planes, SUM(deaths_helicopters) helicopters, SUM(deaths_ships) as ships, ' \
            'SUM(deaths_sams) as air_defence, SUM(deaths_ground) as ground FROM statistics s, ' \
            'players p WHERE s.player_ucid = p.ucid AND p.discord_id = ?'
        with closing(self.bot.conn.cursor()) as cursor:
            result = cursor.execute(SQL_STATISTICS, (member.id, )).fetchone()
            # if no data was found, return False as no chart was drawn
            if (result[0] is None):
                return False

            labels = []
            values = []
            for item in dict(result).items():
                labels.append(string.capwords(item[0], sep='_').replace('_', ' '))
                values.append(item[1])
            xpos = 0
            bottom = 0
            width = 0.2
            # there is nothing to be drawn
            if (np.sum(values) == 0):
                return False
            for i in range(len(values)):
                height = values[i]/np.sum(values)
                axis.bar(xpos, height, width, bottom=bottom)
                ypos = bottom + axis.patches[i].get_height() / 2
                bottom += height
                if (int(values[i]) > 0):
                    axis.text(xpos, ypos, "%d%%" % (axis.patches[i].get_height() * 100), ha='center', color='black')

            axis.set_title('Player\nkilled by', color='white', fontsize=15)
            axis.axis('off')
            axis.set_xlim(- 2.5 * width, 2.5 * width)
            if (legend is True):
                axis.legend(labels, fontsize=15, loc=3, ncol=5, mode='expand',
                            bbox_to_anchor=(0.6, -0.2, 2.2, 0.4), columnspacing=1, frameon=False)
            # Chart was drawn, return True
            return True

    @commands.command(description='Shows player statistics', usage='[member]', aliases=['stats'])
    @commands.has_role('DCS')
    @commands.guild_only()
    async def statistics(self, ctx, member: discord.Member = None):
        try:
            if (member is None):
                member = ctx.message.author
            plt.style.use('dark_background')
            figure = plt.figure(figsize=(20, 20))
            self.draw_playtime_planes(member, plt.subplot2grid((3, 3), (0, 0), colspan=2, fig=figure))
            self.draw_server_time(member, plt.subplot2grid((3, 3), (1, 0), colspan=1, fig=figure))
            self.draw_recent(member, plt.subplot2grid((3, 3), (0, 2), colspan=1, fig=figure))
            self.draw_flight_performance(member, plt.subplot2grid((3, 3), (1, 2), colspan=1, fig=figure))
            ax1 = plt.subplot2grid((3, 3), (2, 0), colspan=1, fig=figure)
            ax2 = plt.subplot2grid((3, 3), (2, 1), colspan=1, fig=figure)
            ax3 = plt.subplot2grid((3, 3), (2, 2), colspan=1, fig=figure)
            retval = self.draw_kill_performance(member, ax2)
            i = 0
            if (('kills' in retval) and (self.draw_kill_types(member, ax3) is True)):
                # use ConnectionPatch to draw lines between the two plots
                # get the wedge data
                theta1, theta2 = ax2.patches[i].theta1, ax2.patches[i].theta2
                center, r = ax2.patches[i].center, ax2.patches[i].r
                bar_height = sum([item.get_height() for item in ax3.patches])

                # draw top connecting line
                x = r * np.cos(np.pi / 180 * theta2) + center[0]
                y = r * np.sin(np.pi / 180 * theta2) + center[1]
                con = ConnectionPatch(xyA=(-0.2 / 2, bar_height), coordsA=ax3.transData,
                                      xyB=(x, y), coordsB=ax2.transData)
                con.set_color('lightgray')
                con.set_linewidth(2)
                con.set_linestyle('dashed')
                ax3.add_artist(con)

                # draw bottom connecting line
                x = r * np.cos(np.pi / 180 * theta1) + center[0]
                y = r * np.sin(np.pi / 180 * theta1) + center[1]
                con = ConnectionPatch(xyA=(-0.2 / 2, 0), coordsA=ax3.transData,
                                      xyB=(x, y), coordsB=ax2.transData)
                con.set_color('lightgray')
                con.set_linewidth(2)
                con.set_linestyle('dashed')
                ax3.add_artist(con)
                i += 1
            else:
                ax3.set_visible(False)
            if (('deaths' in retval) and (self.draw_death_types(member, ax1, (i == 0)) is True)):

                # use ConnectionPatch to draw lines between the two plots
                # get the wedge data
                theta1, theta2 = ax2.patches[i].theta1, ax2.patches[i].theta2
                center, r = ax2.patches[i].center, ax2.patches[i].r
                bar_height = sum([item.get_height() for item in ax1.patches])

                # draw top connecting line
                x = r * np.cos(np.pi / 180 * theta2) + center[0]
                y = r * np.sin(np.pi / 180 * theta2) + center[1]
                con = ConnectionPatch(xyA=(0.2 / 2, 0), coordsA=ax1.transData,
                                      xyB=(x, y), coordsB=ax2.transData)
                con.set_color('lightgray')
                con.set_linewidth(2)
                con.set_linestyle('dashed')
                ax1.add_artist(con)

                # draw bottom connecting line
                x = r * np.cos(np.pi / 180 * theta1) + center[0]
                y = r * np.sin(np.pi / 180 * theta1) + center[1]
                con = ConnectionPatch(xyA=(0.2 / 2, bar_height), coordsA=ax1.transData,
                                      xyB=(x, y), coordsB=ax2.transData)
                con.set_color('lightgray')
                con.set_linewidth(2)
                con.set_linestyle('dashed')
                ax1.add_artist(con)
            else:
                ax1.set_visible(False)

            plt.subplots_adjust(hspace=0.5, wspace=0.5)
            embed = discord.Embed(title='Statistics for {}'.format(member.display_name), color=discord.Color.blue())
            filename = '{}.png'.format(member.id)
            figure.savefig(filename, bbox_inches='tight', transparent=True)
            plt.close(figure)
            file = discord.File(filename)
            embed.set_image(url='attachment://' + filename)
            embed.set_footer(text='Click on the image to zoom in.')
            with suppress(Exception):
                await ctx.send(file=file, embed=embed)
            os.remove(filename)
        except (Exception, Error) as error:
            self.bot.log.exception(error)

    def draw_highscore_playtime(self, ctx, axis, period=None):
        SQL_HIGHSCORE_PLAYTIME = 'SELECT p.discord_id, ROUND(SUM(JULIANDAY(s.hop_off) - JULIANDAY(s.hop_on))*86400) AS playtime FROM statistics s, players p WHERE p.ucid = s.player_ucid AND s.hop_off IS NOT NULL'
        if (period == 'day'):
            SQL_HIGHSCORE_PLAYTIME += ' AND date(s.hop_on) > date(\'now\', \'-1 day\')'
        elif (period == 'week'):
            SQL_HIGHSCORE_PLAYTIME += ' AND date(s.hop_on) > date(\'now\', \'-7 days\')'
        elif (period == 'month'):
            SQL_HIGHSCORE_PLAYTIME += ' AND date(s.hop_on) > date(\'now\', \'-1 month\')'
        SQL_HIGHSCORE_PLAYTIME += ' GROUP BY p.discord_id ORDER BY 2 DESC LIMIT 3'
        with closing(self.bot.conn.cursor()) as cursor:
            result = cursor.execute(SQL_HIGHSCORE_PLAYTIME).fetchall()
            labels = []
            values = []
            for row in result:
                member = ctx.message.guild.get_member(row[0])
                name = member.display_name if (member is not None) else str(row[0])
                labels.insert(0, name)
                values.insert(0, row[1] / 3600)
            axis.barh(labels, values, color=['#CD7F32', 'silver', 'gold'], height=0.75)
            # axis.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: str(timedelta(seconds=x))))
            axis.set_xlabel('hours')
            axis.set_title('Players with longes playtimes', color='white', fontsize=25)
            if (len(values) == 0):
                axis.set_xticks([])
                axis.set_yticks([])
                axis.text(0, 0, 'No data available.', ha='center', va='center', size=15)

    def draw_highscore_kills(self, ctx, figure, period=None):
        SQL_PARTS = {
            'Air Targets': 'SUM(s.kills_planes+s.kills_helicopters)',
            'Ships': 'SUM(s.kills_ships)',
            'Air Defence': 'SUM(s.kills_sams)',
            'Ground Targets': 'SUM(s.kills_ground)'
        }
        COLORS = ['#CD7F32', 'silver', 'gold']
        SQL_HIGHSCORE = {}
        for key in SQL_PARTS.keys():
            SQL_HIGHSCORE[key] = 'SELECT p.discord_id, {} FROM players p, statistics s WHERE s.player_ucid = p.ucid AND p.discord_id <> -1'.format(
                SQL_PARTS[key])
            if (period == 'day'):
                SQL_HIGHSCORE[key] += ' AND date(s.hop_on) > date(\'now\', \'-1 day\')'
            elif (period == 'week'):
                SQL_HIGHSCORE[key] += ' AND date(s.hop_on) > date(\'now\', \'-7 days\')'
            elif (period == 'month'):
                SQL_HIGHSCORE[key] += ' AND date(s.hop_on) > date(\'now\', \'-1 month\')'
            SQL_HIGHSCORE[key] += ' GROUP BY p.discord_id HAVING {} > 0 ORDER BY 2 DESC LIMIT 3'.format(SQL_PARTS[key])

        with closing(self.bot.conn.cursor()) as cursor:
            keys = list(SQL_PARTS.keys())
            for j in range(0, len(keys)):
                type = keys[j]
                result = cursor.execute(SQL_HIGHSCORE[type]).fetchall()
                axis = plt.subplot2grid((3, 2), (1+int(j/2), j % 2), colspan=1, fig=figure)
                labels = []
                values = []
                for i in range(0, 3):
                    if (len(result) > i):
                        member = ctx.message.guild.get_member(result[i][0])
                        name = member.display_name if (member is not None) else str(result[i][0])
                        labels.insert(0, name)
                        values.insert(0, result[i][1])
                axis.barh(labels, values, color=COLORS, label=type, height=0.75)
                axis.set_title(type, color='white', fontsize=25)
                if (len(values) == 0):
                    axis.set_xticks([])
                    axis.set_yticks([])
                    axis.text(0, 0, 'No data available.', ha='center', va='center', rotation=45, size=15)

    @commands.command(description='Shows actual highscores', usage='[period]', aliases=['hs'])
    @commands.has_role('DCS')
    @commands.guild_only()
    async def highscore(self, ctx, period=None):
        if (period and period not in ['day', 'week', 'month']):
            await ctx.send('Period must be one of day/week/month!')
            return
        try:
            plt.style.use('dark_background')
            figure = plt.figure(figsize=(15, 15))
            self.draw_highscore_playtime(ctx, plt.subplot2grid((3, 2), (0, 0), colspan=2, fig=figure), period)
            self.draw_highscore_kills(ctx, figure, period)
            plt.subplots_adjust(hspace=0.5, wspace=0.5)
            title = 'Highscores'
            if (period):
                title += ' of the ' + string.capwords(period)
            embed = discord.Embed(title=title, color=discord.Color.blue())
            filename = 'highscore.png'
            figure.savefig(filename, bbox_inches='tight', transparent=True)
            plt.close(figure)
            file = discord.File(filename)
            embed.set_image(url='attachment://' + filename)
            embed.set_footer(text='Click on the image to zoom in.')
            with suppress(Exception):
                await ctx.send(file=file, embed=embed)
            os.remove(filename)
        except (Exception, Error) as error:
            self.bot.log.exception(error)


def setup(bot):
    bot.add_cog(Statistics(bot))
