from discord.ext import commands, tasks
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta, timezone
from discord import app_commands
import asyncio
import discord
import json
import logging
import requests

# load config
with open("config.json", "r", encoding="utf8") as jfile:
    jdata = json.load(jfile)

# set up logging
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_file = "earthquake_report.log"

file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=3)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

logger = logging.getLogger("earthquake_report")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)


def str_to_time(time_str):
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

def intensity_to_color(intensity, suffix):
    if intensity == 1:
        return 0xe0ffe0
    elif intensity == 2:
        return 0x33ff34
    elif intensity == 3:
        return 0xfffe2f
    elif intensity == 4:
        return 0xfe842e
    elif intensity == 5 and suffix == "弱":
        return 0xfe5231
    elif intensity == 5 and suffix == "強":
        return 0xc43c3c
    elif intensity == 6 and suffix == "弱":
        return 0x9a4644
    elif intensity == 6 and suffix == "強":
        return 0x9a4c86
    elif intensity == 7:
        return 0xb61eeb

def time_to_stamp(time_str):
    tz = timezone(timedelta(hours=8))
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz).timestamp()

class EarthquakeReport(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.earthquake_warning.start()
        self.eq_channel_id = int(jdata["guilds"]["eqReportChannelID"])
        self.eq_report_role_id = int(jdata["roles"]["eqReportID"])
        self.cwa_api_key = str(jdata["CWA_API_KEY"])
        self.iconURL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSqn2zzgCgO91yRfyCEbvCOZmR8OZzOhOe-1w&s"
        self.max_retries = 3
        self.retry_delay = 5  # 秒

        self.last_eq_No_Time = self._load_last_message()
        self.eq_data = self.get_eq_data()

        # Initialize earthquake data
        self.eq_No = str(self.eq_data["records"]["Earthquake"][0]["EarthquakeNo"])
        self.eq_Time = str(self.eq_data["records"]["Earthquake"][0]["EarthquakeInfo"]["OriginTime"])
        self.eq_Timestamp = time_to_stamp(self.eq_Time)  # float
        self.eq_MaxIntensity, self.eq_MaxIntensity_suffix = self.get_max_intensity()  # int, str
        self.eq_Intensity_color = intensity_to_color(self.eq_MaxIntensity, self.eq_MaxIntensity_suffix)
        self.eq_ReportImage = self.eq_data["records"]["Earthquake"][0]["ReportImageURI"]
        self.eq_Web = self.eq_data["records"]["Earthquake"][0]["Web"]
        self.eq_Source = self.eq_data["records"]["Earthquake"][0]["EarthquakeInfo"]["Source"]
        self.eq_Epicenter = self.eq_data["records"]["Earthquake"][0]["EarthquakeInfo"]["Epicenter"]["Location"]
        self.eq_Mag = self.eq_data["records"]["Earthquake"][0]["EarthquakeInfo"]["EarthquakeMagnitude"]["MagnitudeValue"]

    def cog_unload(self):
        self.earthquake_warning.cancel()

    def _load_last_message(self):
        try:
            with open("last_message.json", "r", encoding="utf8") as jfile:
                last_message = json.load(jfile)
                return last_message.get("lastMessage", None)
        except FileNotFoundError:
            return None

    def record_message(self, message):
        try:
            self.last_eq_No_Time = message
            with open("last_message.json", 'w') as file:
                json.dump({'lastMessage': message}, file)
            return message
        except Exception as e:
            logger.error(f"Error recording last message: {e}")
            return None

    def get_max_intensity(self):
        try:
            max_intensity = None
            suffix = None
            for shacking_area in self.eq_data["records"]["Earthquake"][0]["Intensity"]["ShakingArea"]:
                intensity = shacking_area['AreaIntensity']
                if max_intensity is None or int(intensity[0]) > max_intensity:
                    max_intensity = int(intensity[0])
                    suffix = intensity[1]
            return max_intensity, suffix
        except KeyError as e:
            logger.error(f"Error processing earthquake data: missing key {e}")
            return None, None

    def make_embed(self):
        try:
            # embed message
            embed = discord.Embed(title="地震報告", color=self.eq_Intensity_color)
            embed.set_author(name=f"{self.eq_Source}", url=f"{self.eq_Web}", icon_url=self.iconURL)
            embed.set_thumbnail(url=f"{self.eq_ReportImage}")
            embed.add_field(name="編號", value=f"{self.eq_No}", inline=True)
            embed.add_field(name="時間", value=f"{self.eq_Time} (<t:{int(self.eq_Timestamp)}:R>)", inline=True)
            embed.add_field(name="震央", value=f"{self.eq_Epicenter}", inline=False)
            embed.add_field(name="芮氏規模", value=f"{self.eq_Mag}", inline=True)
            embed.add_field(name="最大震度", value=f"{self.eq_MaxIntensity} {self.eq_MaxIntensity_suffix}", inline=True)

            return embed
        except KeyError as e:
            logger.error(f"Error processing earthquake data: missing key {e}")
            return None

    def fetch_data_with_retry(self, url):
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.get(url)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logger.error(f"Error fetching earthquake data (retry {retries+1}): {e}")
                retries += 1
                time.sleep(self.retry_delay)
        
        logger.error("Failed to fetch earthquake data after retries.")
        return None


    def get_eq_data(self):
        # https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001?Authorization=CWA-A9240309-46AD-4C33-9E1F-8F577BE9E831&limit=1&format=JSON&AreaName=
        # https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization=CWA-A9240309-46AD-4C33-9E1F-8F577BE9E831&limit=1&format=JSON&AreaName=
        # 顯著有感地震報告
        bigEQurl = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001?Authorization={self.cwa_api_key}&limit=1&format=JSON&AreaName="
        bigEQdata = self.fetch_data_with_retry(bigEQurl)
        if bigEQdata is None:
            return  # Handle the error or exit gracefully

        # 小區域有感地震報告
        smallEQurl = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={self.cwa_api_key}&limit=1&format=JSON&AreaName="
        smallEQdata = self.fetch_data_with_retry(smallEQurl)
        if smallEQdata is None:
            return

        try:
            # 判斷哪個地震資料較新
            bigeqTime = str(bigEQdata["records"]["Earthquake"][0]["EarthquakeInfo"]["OriginTime"])
            smalleqTime = str(smallEQdata["records"]["Earthquake"][0]["EarthquakeInfo"]["OriginTime"])
            if str_to_time(bigeqTime) > str_to_time(smalleqTime):
                eqdata = bigEQdata
            else:
                eqdata = smallEQdata
        except KeyError as e:
            logger.error(f"Error processing earthquake data: missing key {e}")
            return

        return eqdata

    # Set up eq report channel
    @app_commands.command(name="設置地震報告頻道", description="設置地震報告頻道")
    async def set_eq_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # 僅有能管理頻道的人員可以設定
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("你沒有權限設定地震報告頻道", ephemeral=True)
            return

        self.eq_channel_id = channel.id
        # Save to config
        with open("config.json", "w") as jfile:
            jdata["guilds"]["eqReportChannelID"] = str(self.eq_channel_id)
            json.dump(jdata, jfile, indent=2, ensure_ascii=False)
        await interaction.response.send_message(f"地震報告頻道已設定為 {channel.mention}")

    # For testing
    @app_commands.command(name="測試地震報告", description="測試地震報告")
    async def test_eq_report(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.make_embed(), content="以下是測試地震報告")

    @tasks.loop(minutes=1)
    async def earthquake_warning(self):
        channel = self.bot.get_channel(self.eq_channel_id)

        # Update earthquake data
        self.eq_data = self.get_eq_data()

        self.eq_No = str(self.eq_data["records"]["Earthquake"][0]["EarthquakeNo"])
        self.eq_Time = str(self.eq_data["records"]["Earthquake"][0]["EarthquakeInfo"]["OriginTime"])
        self.eq_Timestamp = time_to_stamp(self.eq_Time)  # float
        self.eq_MaxIntensity, self.eq_MaxIntensity_suffix = self.get_max_intensity()  # int, str
        self.eq_Intensity_color = intensity_to_color(self.eq_MaxIntensity, self.eq_MaxIntensity_suffix)
        self.eq_ReportImage = self.eq_data["records"]["Earthquake"][0]["ReportImageURI"]
        self.eq_Web = self.eq_data["records"]["Earthquake"][0]["Web"]
        self.eq_Source = self.eq_data["records"]["Earthquake"][0]["EarthquakeInfo"]["Source"]
        self.eq_Epicenter = self.eq_data["records"]["Earthquake"][0]["EarthquakeInfo"]["Epicenter"]["Location"]
        self.eq_Mag = self.eq_data["records"]["Earthquake"][0]["EarthquakeInfo"]["EarthquakeMagnitude"]["MagnitudeValue"]

        # Check if new earthquake data
        try:
            eq_identifier = f"{self.eq_No}_{self.eq_Time}"
            if self.last_eq_No_Time == eq_identifier:
                logger.info("No new earthquake data")
                return
        except KeyError as e:
            logger.error(f"Error processing earthquake data: missing key {e}")
            return

        try:
            # embed message
            embed = self.make_embed()
            # send message if last message is None or the time is different
            # if (last_message_embed is None or last_message_embed.fields[1].value[:19] != eqTime):
            # 如果是顯著有感地震，就 @地震報告，否則不 @
            if self.eq_No[3:] != "000":
                await channel.send(embed=embed, content=f"<@&{self.eq_report_role_id}>")
            else:
                await channel.send(embed=embed)
            logger.info("Sent earthquake report")
            self.last_eq_No_Time = self.record_message(eq_identifier)

        except KeyError as e:
            logger.error(f"Error processing earthquake data: missing key {e}")

    @earthquake_warning.before_loop
    async def before_earthquake_warning(self):
        logger.info("Waiting for bot to be ready...")
        await self.bot.wait_until_ready()
        logger.info("Bot is ready. Starting earthquake warning loop...")

    @earthquake_warning.after_loop
    async def after_earthquake_warning(self):
        logger.info("Earthquake warning loop has stopped")


async def setup(bot: commands.Bot):
    await bot.add_cog(EarthquakeReport(bot))
