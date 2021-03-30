# concept of sending discord message from back ground task >> https://stackoverflow.com/a/64370097
import discord
from discord.ext import commands, tasks
import logging
import asyncio
import threading

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

import time
import json
from datetime import datetime
import os
import sys
from dotenv import load_dotenv

# from time import time, time.sleep





class ConsoleApp:
    def __init__(self, evt_loop, channel):
        self.evt_loop = evt_loop
        self.channel = channel
        
        self.bot_log('Running selenium background task...')
        self.bot_log('Loading user information...')
        with open('usr_creds.json', 'r') as f:
            usr_creds = json.load(f)
            self.full_name = usr_creds['full_name']
            self.usrnm = usr_creds['usrnm']
            self.pwd = usr_creds['pwd']
            self.usr_mail = usr_creds['usr_mail']
            self.mob_nmbr = usr_creds['mob_nmbr']
            self.addr = usr_creds['addr']
            self.zip = usr_creds['zip']
            self.city = usr_creds['city']
            self.color = usr_creds['color'] # keep it blank if product doesn't have a color
            self.product_link = usr_creds['product_link']
            self.bike_name = usr_creds['bike_name']
       

        self.bot_log('Running webdriver...')
        op = webdriver.ChromeOptions()
        op.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
        op.add_argument('--headless')
        op.add_argument('--no-sandbox')
        op.add_argument('--disable-dev-sh-usage')
        self.driver = webdriver.Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), chrome_options=op)
    
        self.login()

    def bot_log(self, msg):
        # await channel.send('Test') # We can't do this because of the above comment
        asyncio.run_coroutine_threadsafe(send_log(msg, self.channel), self.evt_loop)

    def login(self):
        self.bot_log('Trying to login into www.eorange.shop...')
        self.driver.get("https://eorange.shop/user/login")

        sel_usrnm = self.driver.find_element_by_xpath('//input[@id="username"]')
        sel_pwd = self.driver.find_element_by_xpath('//input[@id="password"]')
        sel_btn_login = self.driver.find_element_by_xpath('//button[@id="register"]')

        self.bot_log('Typing in username and password')
        sel_usrnm.clear()
        sel_usrnm.send_keys(self.usrnm)
        sel_pwd.clear()
        sel_pwd.send_keys(self.pwd)
        # time.sleep(3)
        self.bot_log('Submitting user login info')
        sel_btn_login.click()
        self.bot_log('Login successful')
        self.check_availability()

    def check_availability(self):
        self.bot_log('Checking product availability')
        self.refresh_count = 0
        # start_time = time()
        start_time = datetime.now()
        self.driver.get(self.product_link)
        while True:
            try:
                self.driver.find_element_by_xpath('//span[contains(text(),"Add To Cart")]')
            except:
                
                self.bot_log(self.show_stats(start_time, 'Product is not Available'))
                self.refresh_count +=1
                time.sleep(3)
                self.driver.refresh()
            else:
                self.bot_log(self.show_stats(start_time, 'Product is Available!'))
                self.order_now()
                
                while True:
                    self.bot_log('Order Placement Successful!!!')
                    sys.exit()
                    time.sleep(3)
                    # winsound.PlaySound('psiren.wav',winsound.SND_FILENAME)
                    #winsound.Beep(100, 1000) 


    def show_stats(self, start_time, msg):
        end_time = datetime.now()
        time_elapsed = end_time - start_time
        hours, rest = divmod(time_elapsed.seconds, 3600)
        minutes, seconds = divmod(rest, 60)
        hr = int(hours)
        mnt = int(minutes)
        sec = int(seconds)

        retn = f"""-----------------------------------------------------
--> Product >> {self.bike_name}
--> Time elapsed >> {hr} hours {mnt} minutes {sec} seconds.
--> Refreshed    >> {self.refresh_count} times
--> {msg}\n\n
-----------------------------------------------------
"""
        return retn

    def order_now(self):
        if self.color:
            self.bot_log('Selecting product color')
            btn_select_color = self.driver.find_element_by_xpath(f"//span[contains(text(), '{self.color}')]")
            btn_select_color.click()

        btn_order_now = self.driver.find_element_by_xpath('//a[@id="buy_now"]')

        self.bot_log('Clicking order now button...')
        btn_order_now.click()
     
        time.sleep(4)
        frm_name = self.driver.find_element_by_xpath('//input[@name="name"]')
        frm_phone = self.driver.find_element_by_xpath('//input[@name="phone"]')
        frm_email = self.driver.find_element_by_xpath('//input[@name="email"]')
        frm_address = self.driver.find_element_by_xpath('//textarea[@name="address"]')
        frm_zip = self.driver.find_element_by_xpath('//input[@name="zip"]')
        frm_select_city = Select(self.driver.find_element_by_xpath('//select[@name="city"]'))
        frm_agree = self.driver.find_element_by_xpath('//input[@name="agree"]')
        frm_btn_submit = self.driver.find_element_by_xpath('//input[@type="submit"]')

        self.bot_log('Typing in user details in order form...')
        frm_name.clear()
        frm_name.send_keys(self.full_name)
        frm_phone.clear()
        frm_phone.send_keys(self.mob_nmbr)
        frm_email.clear()
        frm_email.send_keys(self.usr_mail)
        frm_address.clear()
        frm_address.send_keys(self.addr)
        frm_select_city.select_by_visible_text(self.city)
        frm_zip.clear()
        frm_zip.send_keys(self.zip)
        frm_agree.click()
        # time.sleep(1)
        self.bot_log('Submitting Order Placement Form...')
        frm_btn_submit.click()
        start_time = datetime.now()
        self.bot_log(self.show_stats(start_time, 'Order has been Placed Successfully!!!'))

def blocker_background_task(evt_loop, channel):
    ConsoleApp(evt_loop, channel)


load_dotenv()

TOKEN = os.environ['DISCORD_TOKEN']
bot = commands.Bot(command_prefix='..')

CH_ID_aa = 825418226161680385

@bot.event
async def on_ready():
    chn_aa = bot.get_channel(CH_ID_aa)
    await send_log('Bot is ready.', chn_aa)

    threading.Thread(
        target=blocker_background_task,
        args=(asyncio.get_event_loop(), chn_aa)
    ).start()

async def send_log(msg, channel):
    print(msg, datetime.now().isoformat(), '\n\n')
    msg_ext = msg + '\n\n'
    await channel.send(msg_ext)


bot.run(TOKEN)