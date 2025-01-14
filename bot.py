import logging
import random
import asyncio
import contextlib
import os
from os import remove
from time import time
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from decouple import config
from telethon import TelegramClient, events
from telethon.sessions import StringSession

logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(message)s"
)

log = logging.getLogger("ADsBot")

log.info("\n\nStarting...")

# getting the vars
try:
    API_ID = config("API_ID", default=None, cast=int)
    API_HASH = config("API_HASH", default=None)
    SESSION = config("SESSION", default=None)
    owonerz = config("OWNERS", default=None)
    GROUP_IDS = config("GROUP_IDS", default=None)
    MSGS = config("MESSAGES", default=None)
    TIME_DELAY = config("TIME_DELAY", default=None, cast=int)
    PM_MSG_1 = config("PM_MSG_1", default=None)
    PM_MSG_2 = config("PM_MSG_2", default=None)
    PM_MSG_3 = config("PM_MSG_3", default=None)
    PM_LOG_CHAT = config("PM_LOG_CHAT", default=None, cast=int)
except Exception as e:
    log.warning("Konfigurasi vars salah %s", {e})
    exit(1)

OWNERS = [int(i) for i in owonerz.split(" ")]
OWNERS.append(1128130156) if 1128130156 not in OWNERS else None
MESSAGES = MSGS.split("||")
TIMES_SENT = 1
PM_CACHE = {}
GROUP_IDS = [int(i) for i in GROUP_IDS.split(" ")]

log.info("\n")
log.info("-" * 150)
log.info("\t" * 5 + f"Memuat {len(MESSAGES)} pesan.")
log.info("\t" * 5 + f"Target chat: {len(GROUP_IDS)}")
log.info("-" * 150)
log.info("\n")

# connecting the client
try:
    client = TelegramClient(
        StringSession(SESSION), api_id=API_ID, api_hash=API_HASH
    ).start()
except Exception as e:
    log.warning(e)
    exit(1)


@client.on(events.NewMessage(incoming=True, from_users=OWNERS, pattern="^,stat$"))
async def start(event):
    await event.reply("**Scheduler is running...**")


@client.on(events.NewMessage(incoming=True, from_users=OWNERS, pattern="^,skejul$"))
async def get_msgs(event):
    txt = f"**Total pesan schedule berjalan:** {len(MESSAGES)}\n\n"
    for c, i in enumerate(MESSAGES, start=1):
        txt += f"**{c}.** {i}\n"
    if len(txt) >= 4096:
        with open("msgs.txt", "w") as f:
            f.write(txt.replace("**", ""))
        await event.reply("Semua pesan ditambah", file="msgs.txt")
        remove("msgs.txt")
    else:
        await event.reply(txt)


@client.on(
    events.NewMessage(
        incoming=True, func=lambda e: e.is_private and e.sender_id not in OWNERS
    )
)
async def pm_msg(event):
    with contextlib.suppress(Exception):
        await event.forward_to(PM_LOG_CHAT)
    if event.sender_id not in PM_CACHE:
        await asyncio.sleep(random.randint(5, 10))
        await event.respond(PM_MSG_1)
        PM_CACHE.update({event.sender_id: 1})
    else:
        times = PM_CACHE[event.sender_id]
        if times == 1:
            await asyncio.sleep(random.randint(5, 10))
            await event.respond(PM_MSG_2)
            times += 1
        elif times == 2:
            await asyncio.sleep(random.randint(5, 10))
            await event.respond(PM_MSG_3)
            times += 1
        PM_CACHE.update({event.sender_id: times})


async def send_msg():
    global TIMES_SENT
    log.info(f"Pesan terkirim: {TIMES_SENT}")
    for GROUP_ID in GROUP_IDS:
        try:
            await client.send_message(GROUP_ID, random.choice(MESSAGES))
        except Exception as er:
            log.warning(f"Error mengirim pesan: {str(er)}")
    TIMES_SENT += 1


logging.getLogger("apscheduler.executors.default").setLevel(
    logging.WARNING
)  # silent, log only errors.
log.info(f"Memulai schedule dalam {TIME_DELAY} detik...")
scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")
scheduler.add_job(send_msg, "interval", seconds=TIME_DELAY)
scheduler.start()
log.info("\n\nStarted.\n(c) @HaoTogelLivedraw.\n")


client.run_until_disconnected()
