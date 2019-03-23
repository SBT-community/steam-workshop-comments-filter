import os
import re
import time
import json
import webbrowser
from typing import Tuple
import steam.webauth as wa
from bs4 import BeautifulSoup as bs


def log(text: str, printdate: bool = True, printmessage: bool = True, writetofile: bool = True) -> str:
    """

    :param text: The text itself
    :param printdate: Do print date in message?
    :param printmessage: Do print message in console or not?
    :param writetofile: Do write message in file or not?
    :return: The modified text
    """

    if printdate:
        localtime = time.strftime("%d.%m.%YT%H:%M:%S", time.localtime(time.time()))
        message = "[AntiGay] {} ({})".format(text, localtime)
    else:
        message = "[AntiGay] {}".format(text)

    if printmessage:
        print(message)

    if writetofile:
        f = open(os.path.dirname(__file__) + "py-antigay.log", "a")
        f.write(message + "\n")
        f.close()

    return message


class Handler:
    def __init__(self, login, password, content_id, author_id, words_blacklist, users_blacklist=(), users_whitelist=()):
        self.__user = wa.WebAuth(login, password)
        self.__session = None

        self.content_id = content_id
        self.author_id = author_id
        self.USERS_BLACKLIST = users_blacklist
        self.USERS_WHITELIST = users_whitelist
        self.WORDS_BLACKLIST = words_blacklist

        self.set_session()

    def set_session(self):
        log("Setting up the session for work")

        captcha = ""
        email_code = ""
        twofactor_code = ""

        while True:
            try:
                self.__user.login(captcha=captcha, email_code=email_code, twofactor_code=twofactor_code)
            except wa.CaptchaRequired:
                log("Opening captcha image.. {captcha_url}".format(captcha_url=self.__user.captcha_url),
                    writetofile=False)
                webbrowser.open(self.__user.captcha_url)
                captcha = input(log("Enter the captcha> ", False, False, False))
            except wa.EmailCodeRequired:
                email_code = input(log("Enter Steam Guard E-mail code> ", False, False, False))
            except wa.TwoFactorCodeRequired:
                twofactor_code = input(log("Enter Mobile Steam Guard code> ", False, False, False))
            except wa.LoginIncorrect:
                log("Incorrect user name or password. Or login limit exceeded")
            except KeyboardInterrupt:
                raise SystemExit
            else:
                break

        self.__session = self.__user.login()

    def get_session(self):
        return self.__session

    def delete_comment(self, gid_comment):
        session = self.get_session()
        cookies = session.cookies.get_dict()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
        }
        params = {
            "count": 10,
            "extended_data": "{'contributors':['" + self.author_id +"'],'appid':4000,'sharedfile':{'m_parentsDetails':[],'m_parentBundlesDetails':[],'m_bundledChildren':[],'m_ownedBundledItems':[]}}",
            "feature2": -1,
            "gidcomment": gid_comment,
            "sessionid": cookies.get("sessionid", "None"),
            "start": 0,
        }

        post = session.post(
            "https://steamcommunity.com/comment/PublishedFile_Public/delete/{author_id}/{content_id}/".format(
                author_id=self.author_id,
                content_id=self.content_id
            ),
            headers=headers, data=params).json()

        if post.get("success", False):
            log("Comment deletion successful (GID: {})".format(gid_comment))
        else:
            log("Comment deletion failed (GID: {})".format(gid_comment))

    def parse_comments(self):
        session = self.get_session()

        # Getting workshop page
        resp = session.get("https://steamcommunity.com/sharedfiles/filedetails/?id=" + self.content_id)
        parsed = bs(resp.content, "html.parser")
        comments = parsed.findAll("div", {"class": "commentthread_comment"})

        # Checking comments
        for comment in comments:
            steam_profile = comment.find("a", {
                "class": "hoverunderline commentthread_author_link"})  # Data about the profile
            mini_profile_id = steam_profile.get(
                "data-miniprofile")  # data-miniprofile is something like SteamID, unchangeable

            # Skipping the users from the whitelist
            if mini_profile_id in self.USERS_WHITELIST:
                continue

            profile_name = steam_profile.find("bdi").get_text()  # The profile name
            profile_link = steam_profile.get("href")  # The profile link

            # Getting the gid of comment
            gid_comment = re.search(r"([0-9]+)", re.search(r", \'([0-9]+)\'  \);$",
                                                           comment.find("a", {"class": "actionlink"}).get(
                                                               "href")).group(0)).group(0)
            text = comment.find("div", {
                "class": "commentthread_comment_text"}).get_text().strip()  # The text

            # Looking for annoying users in blacklist and delete comment if found something
            if mini_profile_id in self.USERS_BLACKLIST:
                log("A fagot has found (Name: {name}, Steam Link: {link}, Mini Profile Id: {mini})".format(
                    name=profile_name,
                    link=profile_link,
                    mini=mini_profile_id))
                log("Deleting comment (Text: {text}, GID: {gid})".format(text=text, gid=gid_comment))
                self.delete_comment(gid_comment)

            # And now looking for blacklist words in comment and delete it if found something
            for word in self.WORDS_BLACKLIST:
                if text.lower().find(word) != -1:
                    log("A fagot has found (Name: {name}, Steam Link: {link}, Mini Profile Id: {mini})".format(
                        name=profile_name,
                        link=profile_link,
                        mini=mini_profile_id))
                    log("Deleting comment (Text: {text}, GID: {gid})".format(text=text, gid=gid_comment))
                    self.delete_comment(gid_comment)
                    break  # We cannot delete this comment again
