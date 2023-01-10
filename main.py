import twder
import os
import speech_recognition as sr
import requests
import re
import twstock
import pyimgur
import datetime
import matplotlib.pyplot as plt
import dataframe_image as dfi
import pandas as pd
from urllib import request
from pydub import AudioSegment
from bs4 import BeautifulSoup
from flask import Flask
from flask import request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

line_bot_api = LineBotApi(
    "你的 Channel access token")
handler = WebhookHandler('你的 Channel secret')
CLIENT_ID = "imgur的ID"
app = Flask(__name__)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                                   AppleWebKit/537.36 (KHTML, like Gecko) \
                                   Chrome/102.0.0.0 Safari/537.36'}


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=AudioMessage)  # 取得聲音時做的事情
def handle_message_audio(event):
    # 接收使用者語音訊息並存檔
    userid = event.source.user_id
    path = userid + ".wav"
    audio_content = line_bot_api.get_message_content(event.message.id)
    with open(path, 'wb') as fd:
        for chunk in audio_content.iter_content():
            fd.write(chunk)
    fd.close()

    # 進行語音轉文字處理
    r = sr.Recognizer()
    # AudioSegment.converter = 'ffmpeg.exe'  # 輸入自己的ffmpeg.exe路徑
    sound = AudioSegment.from_file_using_temporary_files(path)
    path = os.path.splitext(path)[0] + '.wav'
    sound.export(path, format="wav")
    with sr.AudioFile(path) as source:
        audio = r.record(source)
    audio_text = r.recognize_google(audio, language='zh-Hant')  # 設定要以什麼文字轉換
    base_url = "https://tw.news.yahoo.com"
    url = "https://tw.news.yahoo.com/search?p=" + audio_text
    r = requests.get(url)
    content = ""
    soup = BeautifulSoup(r.text, "html.parser")
    data = soup.select("h3", {"class": "Mb(5px)"})

    for index, d in enumerate(data):
        if index < 5:
            title = d.text
            href = base_url + d.a["href"]
            content += "{}\n{}\n".format(title, href)
        else:
            break

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=content))


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    userid = event.source.user_id
    msg = event.message.text
    if msg == "使用說明":
        text1 = '''
1. 輸入M可查詢匯率,例:M美金。

2. 輸入N及股票代號可查詢個股新聞,例:N2330。

3. 輸入P及股票代號可查詢個股即時報價,例:P2330。

4. 輸入Q及申購筆數可查詢近期股票申購狀態,最多搜尋十筆,例:Q10。

5. 輸入美股及美股股票名稱可查詢個股最新報價,例:美股TSLA

6. 輸入#及加密幣代號可查詢加密幣最新報價,例:#BTC

7. 說出股票名稱或者產業專有名詞可查詢相關新聞,例:台積電,記憶體,鋼鐵
                '''
        message = TextSendMessage(
            text=text1
        )
        line_bot_api.reply_message(event.reply_token, message)

    elif msg[:1] == 'M':
        string = msg
        characters = "M"

        for x in range(len(characters)):
            string = string.replace(characters[x], "")
        exchange_message = string
        currencies = {'美金': 'USD', '美元': 'USD', '港幣': 'HKD', '英鎊': 'GBP', '澳幣': 'AUD', '加拿大幣': 'CAD',
                      '加幣': 'CAD', '新加坡幣': 'SGD', '新幣': 'SGD', '瑞士法郎': 'CHF', '瑞郎': 'CHF', '日圓': 'JPY',
                      '日幣': 'JPY', '南非幣': 'ZAR', '瑞典幣': 'SEK', '紐元': 'NZD', '紐幣': 'NZD', '泰幣': 'THB',
                      '泰銖': 'THB', '菲國比索': 'PHP', '菲律賓幣': 'PHP', '印尼幣': 'IDR', '歐元': 'EUR',
                      '韓元': 'KRW', '韓幣': 'KRW', '越南盾': 'VND', '越南幣': 'VND', '馬來幣': 'MYR', '人民幣': 'CNY'}
        keys = currencies.keys()
        tlist = ['現金買入', '現金賣出', '即期買入', '即期賣出']
        currency = exchange_message
        show = currency + '匯率：\n'
        if currency in keys:
            for i in range(4):
                exchange = float(twder.now(currencies[currency])[i + 1])
                show = show + tlist[i] + '：' + str(exchange) + '\n'
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=show))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='無貨幣資料哦~'))

    elif msg == '美股':
        message = TextSendMessage(
            text='請選擇以下功能',
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(label="美股新聞", text="美股新聞")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="道瓊工業指數", text="@DJI")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="S&P500指數", text="@GSPC")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="NASDAQ指數", text="@IXIC")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="費城半導體指數", text="@SOX")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="E-Mini 道瓊期", text="E-Mini 道瓊期")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="E-Mini NASDAQ期", text="E-Mini NASDAQ期")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="E-Mini S&P500期", text="E-Mini S&P500期")
                    ),
                ]

            )

        )
        line_bot_api.reply_message(event.reply_token, message)
    elif msg == "E-Mini 道瓊期":  # E-Mini 道瓊期報價
        url = "https://invest.cnyes.com/futures/GF/YM"
        r = requests.get(url)

        soup = BeautifulSoup(r.text, "html.parser")
        data = soup.findAll("div", {"class": "jsx-2214436525 info-lp"})
        msg_1 = data[0].text
        data_1 = soup.findAll("div", {"class": "jsx-2214436525 change-net"})
        msg_2 = data_1[0].text
        data_2 = soup.findAll("div", {"class": "jsx-2214436525 change-percent"})
        msg_3 = data_2[0].text
        data_3 = soup.findAll("div", {"class": "jsx-2214436525 info-volume"})
        msg = data_3[0].text
        msg_4 = msg[4:]

        text1 = 'E-Mini 道瓊期最新資料:'
        text1 += "\n指數：" + msg_1
        text1 += "\n漲跌：" + msg_2
        text1 += "\n漲跌幅(%)：" + msg_3
        text1 += "\n成交口數：" + msg_4
        twn_stock_price_message = [  # 串列
            TextSendMessage(  # 傳送文字
                text=text1
            ),
        ]
        line_bot_api.reply_message(event.reply_token, twn_stock_price_message)
    elif msg == "E-Mini NASDAQ期":  # E-Mini NASDAQ期報價
        url = "https://invest.cnyes.com/futures/GF/NQ"
        r = requests.get(url)

        soup = BeautifulSoup(r.text, "html.parser")
        data = soup.findAll("div", {"class": "jsx-2214436525 info-lp"})
        msg_1 = data[0].text
        data_1 = soup.findAll("div", {"class": "jsx-2214436525 change-net"})
        msg_2 = data_1[0].text
        data_2 = soup.findAll("div", {"class": "jsx-2214436525 change-percent"})
        msg_3 = data_2[0].text
        data_3 = soup.findAll("div", {"class": "jsx-2214436525 info-volume"})
        msg = data_3[0].text
        msg_4 = msg[4:]

        text1 = 'E-Mini NASDAQ期最新資料:'
        text1 += "\n指數：" + msg_1
        text1 += "\n漲跌：" + msg_2
        text1 += "\n漲跌幅(%)：" + msg_3
        text1 += "\n成交口數：" + msg_4
        twn_stock_price_message = [  # 串列
            TextSendMessage(  # 傳送文字
                text=text1
            ),
        ]
        line_bot_api.reply_message(event.reply_token, twn_stock_price_message)
    elif msg == "E-Mini S&P500期":  # E-Mini S&P500期報價
        url = "https://invest.cnyes.com/futures/GF/ES"
        r = requests.get(url)

        soup = BeautifulSoup(r.text, "html.parser")
        data = soup.findAll("div", {"class": "jsx-2214436525 info-lp"})
        msg_1 = data[0].text
        data_1 = soup.findAll("div", {"class": "jsx-2214436525 change-net"})
        msg_2 = data_1[0].text
        data_2 = soup.findAll("div", {"class": "jsx-2214436525 change-percent"})
        msg_3 = data_2[0].text
        data_3 = soup.findAll("div", {"class": "jsx-2214436525 info-volume"})
        msg = data_3[0].text
        msg_4 = msg[4:]

        text1 = 'E-Mini S&P500期最新資料:'
        text1 += "\n指數：" + msg_1
        text1 += "\n漲跌：" + msg_2
        text1 += "\n漲跌幅(%)：" + msg_3
        text1 += "\n成交口數：" + msg_4
        twn_stock_price_message = [  # 串列
            TextSendMessage(  # 傳送文字
                text=text1
            ),
        ]
        line_bot_api.reply_message(event.reply_token, twn_stock_price_message)
    elif msg == '台股':
        message = TextSendMessage(
            text='請選擇以下功能',
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(label="台股新聞", text="台股新聞")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="加權指數", text="加權指數")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="櫃買指數", text="櫃買指數")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="台指期", text="台指期")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="台股三大法人買賣超", text="台股三大法人買賣超")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="台股三大法人期貨未平倉", text="台股三大法人期貨未平倉")
                    ),
                ]

            )

        )
        line_bot_api.reply_message(event.reply_token, message)
    elif msg == "區塊鏈新聞":
        url = 'https://blockcast.it/'
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'lxml')
        changes = soup.findAll("h3", {"class": "jeg_post_title"})

        content = ""

        for index_1, title_link_1 in enumerate(changes):
            if index_1 < 8:
                msg = title_link_1.a.text
                msg_1 = title_link_1.a["href"]
                content += "{}\n{}\n".format(msg, msg_1)
            else:
                break

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=content))
    elif msg[:1] == '#':  # 加密貨幣最新報價
        string = msg
        stock_usa_msg = re.sub("\#|", "", string)

        def twn_usa_stock_crawler(bitcoin_name):
            url = f'https://finance.yahoo.com/quote/' + bitcoin_name + "-USD"
            r = requests.get(url, headers=headers)
            soup = BeautifulSoup(r.text, 'lxml')
            price = soup.find('fin-streamer', {'class': 'Fw(b) Fz(36px) Mb(-4px) D(ib)'})
            changes = soup.findAll('fin-streamer', {'class': 'Fw(500) Pstart(8px) Fz(24px)'})
            stock_msg = price.text
            stock_msg2 = str(stock_msg)
            stock_price = changes[0].find('span').text
            stock_quote = changes[1].find('span').text
            return stock_msg2, stock_price, stock_quote

        stock_msg2, stock_price, stock_quote = twn_usa_stock_crawler(stock_usa_msg)
        try:
            text1 = stock_usa_msg + '最新資料:'
            text1 += "\n股價：" + stock_msg2
            text1 += "\n漲跌：" + stock_price
            text1 += "\n漲跌幅(%)：" + stock_quote
            stock_time_price_message = [  # 串列
                TextSendMessage(  # 傳送文字
                    text=text1
                ),
            ]
            line_bot_api.reply_message(event.reply_token, stock_time_price_message)
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='加密幣代碼輸入錯誤哦~'))
    elif msg == "美股新聞":
        base = "https://news.cnyes.com"
        url = "https://news.cnyes.com/news/cat/us_stock"
        r = requests.get(url)

        content = ""

        soup = BeautifulSoup(r.text, "html.parser")
        data = soup.find_all("a", {"class": "_1Zdp"})

        for index, d in enumerate(data):
            if index < 8:
                title = d.text
                href = base + d.get("href")
                content += "{}\n{}\n".format(title, href)
            else:
                break
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=content))
    elif msg == "台股新聞":
        url = "https://money.udn.com/rank/newest/1001/5590/1"
        r = requests.get(url)
        content = ""
        soup = BeautifulSoup(r.text, "html.parser")
        data = soup.find_all("div", {"class": "story__content"})

        for index, title_link in enumerate(data):
            if index < 8:
                msg = title_link.h3.text
                msg_1 = msg[29:]
                msg_2 = title_link.a['href']
                content += "{}\n{}\n".format(msg_1, msg_2)
            else:
                break
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=content))

    elif msg == "加權指數":  # 加權指數報價
        url = "https://invest.cnyes.com/index/TWS/TSE01"
        r = requests.get(url)

        soup = BeautifulSoup(r.text, "html.parser")
        data = soup.findAll("div", {"class": "jsx-2214436525 info-lp"})
        msg_1 = data[0].text
        data_1 = soup.findAll("div", {"class": "jsx-2214436525 change-net"})
        msg_2 = data_1[0].text
        data_2 = soup.findAll("div", {"class": "jsx-2214436525 change-percent"})
        msg_3 = data_2[0].text
        data_3 = soup.findAll("div", {"class": "jsx-2214436525 info-volume"})
        msg = data_3[0].text
        msg_4 = msg[4:]

        text1 = '加權指數最新資料:'
        text1 += "\n指數：" + msg_1
        text1 += "\n漲跌：" + msg_2
        text1 += "\n漲跌幅(%)：" + msg_3
        text1 += "\n成交金額：" + msg_4
        twn_stock_price_message = [  # 串列
            TextSendMessage(  # 傳送文字
                text=text1
            ),
        ]
        line_bot_api.reply_message(event.reply_token, twn_stock_price_message)

    elif msg == "櫃買指數":  # 櫃買指數報價
        url = "https://invest.cnyes.com/index/TWS/OTC01"
        r = requests.get(url)

        soup = BeautifulSoup(r.text, "html.parser")
        data = soup.findAll("div", {"class": "jsx-2214436525 info-lp"})
        msg_1 = data[0].text
        data_1 = soup.findAll("div", {"class": "jsx-2214436525 change-net"})
        msg_2 = data_1[0].text
        data_2 = soup.findAll("div", {"class": "jsx-2214436525 change-percent"})
        msg_3 = data_2[0].text
        data_3 = soup.findAll("div", {"class": "jsx-2214436525 info-volume"})
        msg = data_3[0].text
        msg_4 = msg[4:]

        text1 = '櫃買指數最新資料:'
        text1 += "\n指數：" + msg_1
        text1 += "\n漲跌：" + msg_2
        text1 += "\n漲跌幅(%)：" + msg_3
        text1 += "\n成交金額：" + msg_4
        twn_stock_price_message = [  # 串列
            TextSendMessage(  # 傳送文字
                text=text1
            ),
        ]
        line_bot_api.reply_message(event.reply_token, twn_stock_price_message)

    elif msg == "台指期":  # 台指期報價
        url = "https://invest.cnyes.com/futures/TWF/TXF"
        r = requests.get(url)

        soup = BeautifulSoup(r.text, "html.parser")
        data = soup.findAll("div", {"class": "jsx-2214436525 info-lp"})
        msg_1 = data[0].text
        data_1 = soup.findAll("div", {"class": "jsx-2214436525 change-net"})
        msg_2 = data_1[0].text
        data_2 = soup.findAll("div", {"class": "jsx-2214436525 change-percent"})
        msg_3 = data_2[0].text
        data_3 = soup.findAll("div", {"class": "jsx-2214436525 info-volume"})
        msg = data_3[0].text
        msg_4 = msg[4:]

        text1 = '台指期最新資料:'
        text1 += "\n指數：" + msg_1
        text1 += "\n漲跌：" + msg_2
        text1 += "\n漲跌幅(%)：" + msg_3
        text1 += "\n成交口數：" + msg_4
        twn_stock_price_message = [  # 串列
            TextSendMessage(  # 傳送文字
                text=text1
            ),
        ]
        line_bot_api.reply_message(event.reply_token, twn_stock_price_message)

    elif msg[:1] == '@':  # 美股四大指數最新報價
        string = msg
        stock_usa_msg = re.sub("\@|", "", string)

        def twn_usa_stock_crawler(stock):
            url = f'https://finance.yahoo.com/quote/%5E' + stock
            r = requests.get(url, headers=headers)
            soup = BeautifulSoup(r.text, 'lxml')
            price = soup.find('fin-streamer', {'class': 'Fw(b) Fz(36px) Mb(-4px) D(ib)'})
            changes = soup.findAll('fin-streamer', {'class': 'Fw(500) Pstart(8px) Fz(24px)'})
            stock_msg = price.text

            stock_msg2 = str(stock_msg)
            stock_price = changes[0].find('span').text
            stock_quote = changes[1].find('span').text
            return stock_msg2, stock_price, stock_quote

        stock_msg2, stock_price, stock_quote = twn_usa_stock_crawler(stock_usa_msg)

        try:
            text1 = stock_usa_msg + '最新資料:'
            text1 += "\n股價：" + stock_msg2
            text1 += "\n漲跌：" + stock_price
            text1 += "\n漲跌幅(%)：" + stock_quote
            stock_time_price_message = [  # 串列
                TextSendMessage(  # 傳送文字
                    text=text1
                ),
            ]
            line_bot_api.reply_message(event.reply_token, stock_time_price_message)
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='股票代碼輸入錯誤哦~'))

    elif msg[:2] == '美股':  # 美國個股最新股價
        string = msg
        stock_usa_msg = re.sub("\美|\股|", "", string)

        def yahoo_stock_crawler(stock):
            url = f'https://finance.yahoo.com/quote/' + stock + '/?fr=sycsrp_catchall'
            r = requests.get(url, headers=headers)
            soup = BeautifulSoup(r.text, 'lxml')
            price = soup.find('fin-streamer', {'class': 'Fw(b) Fz(36px) Mb(-4px) D(ib)'})
            changes = soup.findAll('fin-streamer', {'class': 'Fw(500) Pstart(8px) Fz(24px)'})
            stock_msg = float(price.text)
            stock_msg2 = str(stock_msg)
            stock_price = changes[0].find('span').text
            stock_quote = changes[1].find('span').text
            return stock_msg2, stock_price, stock_quote

        stock_msg2, stock_price, stock_quote = yahoo_stock_crawler(stock_usa_msg)

        try:
            text1 = stock_usa_msg + '最新資料:'
            text1 += "\n股價：" + stock_msg2
            text1 += "\n漲跌：" + stock_price
            text1 += "\n漲跌幅(%)：" + stock_quote
            stock_time_price_message = [  # 串列
                TextSendMessage(  # 傳送文字
                    text=text1
                ),
            ]
            line_bot_api.reply_message(event.reply_token, stock_time_price_message)
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='股票代碼輸入錯誤哦~'))

    elif msg == '台股三大法人買賣超':
        tse_df = pd.read_html("https://histock.tw/stock/three.aspx")[0]
        dfi.export(tse_df.iloc[0:10], userid + '.jpg')
        tse_stock_image = userid + '.jpg'

        im = pyimgur.Imgur(CLIENT_ID)
        uploaded_df_image = im.upload_image(tse_stock_image, title=userid)  # 上傳圖片並獲得圖片資訊
        try:
            image_message = ImageSendMessage(
                original_content_url=uploaded_df_image.link,
                preview_image_url=uploaded_df_image.link
            )
            line_bot_api.reply_message(event.reply_token, image_message)
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Error'))

    elif msg == '台股三大法人期貨未平倉':
        tx_df = pd.read_html("https://histock.tw/stock/three.aspx")[1]
        dfi.export(tx_df.iloc[0:10], userid + '.jpg')
        tx_stock_image = userid + '.jpg'

        im = pyimgur.Imgur(CLIENT_ID)
        uploaded_tx_image = im.upload_image(tx_stock_image, title=userid)  # 上傳圖片並獲得圖片資訊
        try:
            image_message = ImageSendMessage(
                original_content_url=uploaded_tx_image.link,
                preview_image_url=uploaded_tx_image.link
            )
            line_bot_api.reply_message(event.reply_token, image_message)
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Error'))

    elif msg[:1] == 'N':
        string = msg
        characters = "N"

        for x in range(len(characters)):
            news_message = string.replace(characters[x], "")
            try:
                recommend_message = [  # 串列
                    TemplateSendMessage(
                        alt_text=news_message + '新聞',
                        template=ImageCarouselTemplate(
                            columns=[
                                ImageCarouselColumn(
                                    image_url='https://money.udn.com/static/img/moneyudn.jpg',
                                    action=URIAction(
                                        label=news_message + '新聞',
                                        uri="https://money.udn.com/search/result/1001/" + news_message
                                    )
                                ),
                                ImageCarouselColumn(
                                    image_url='https://www.cnyes.com/static/anue-og-image.png',
                                    action=URIAction(
                                        label=news_message + '新聞',
                                        uri="https://www.cnyes.com/search/news?keyword=" + news_message
                                    )
                                ),
                                ImageCarouselColumn(
                                    image_url='https://ibw.bwnet.com.tw/image/blog/bw/528e82d67c8c267b3dcf011eaa6cd546.jpg',
                                    action=URIAction(
                                        label=news_message + '新聞',
                                        uri="https://udn.com/search/word/2/" + news_message
                                    )
                                ),
                            ]
                        ),
                    ),
                    TextSendMessage(
                        text='請選擇以下功能',
                        quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label=news_message + "三大法人", text="Z" + news_message)
                                ),
                                QuickReplyButton(
                                    action=MessageAction(label=news_message + "融資融券", text="X" + news_message)
                                ),
                                QuickReplyButton(
                                    action=MessageAction(label=news_message + "券商分點買賣", text="C" + news_message)
                                ),
                                QuickReplyButton(
                                    action=MessageAction(label=news_message + "集保戶股權分散表",
                                                         text="V" + news_message)
                                ),
                                QuickReplyButton(
                                    action=MessageAction(label=news_message + "上個月股價走勢圖",
                                                         text="T" + news_message)
                                ),
                                QuickReplyButton(
                                    action=MessageAction(label=news_message + "股利政策",
                                                         text="B" + news_message)
                                ),
                                QuickReplyButton(
                                    action=MessageAction(label=news_message + "獲利能力",
                                                         text="S" + news_message)
                                ),
                            ]
                        )
                    )
                ]
                line_bot_api.reply_message(event.reply_token, recommend_message)
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Error'))

    elif msg[:1] == 'Z':  # 個股三大法人資訊
        string = msg
        characters = "Z"

        for x in range(len(characters)):
            stock_news_message = string.replace(characters[x], "")
            stock_news_df = pd.read_html("https://histock.tw/stock/chips.aspx?no=" + stock_news_message)[0]
            dfi.export(stock_news_df.iloc[0:10], userid + '.jpg')
            tse_stock_image = userid + '.jpg'

            im = pyimgur.Imgur(CLIENT_ID)
            uploaded_df_image = im.upload_image(tse_stock_image, title=userid)  # 上傳圖片並獲得圖片資訊
            try:
                image_message = ImageSendMessage(
                    original_content_url=uploaded_df_image.link,
                    preview_image_url=uploaded_df_image.link
                )
                line_bot_api.reply_message(event.reply_token, image_message)
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Error'))

    elif msg[:1] == 'X':  # 個股融資融券資訊
        string = msg
        characters = "X"

        for x in range(len(characters)):
            stock_news_message = string.replace(characters[x], "")
            stock_news_df = pd.read_html("https://histock.tw/stock/chips.aspx?no=" + stock_news_message + "&m=mg")[0]
            dfi.export(stock_news_df.iloc[0:10], userid + '.jpg')
            tse_stock_image = userid + '.jpg'

            im = pyimgur.Imgur(CLIENT_ID)
            uploaded_df_image = im.upload_image(tse_stock_image, title=userid)  # 上傳圖片並獲得圖片資訊
            try:
                image_message = ImageSendMessage(
                    original_content_url=uploaded_df_image.link,
                    preview_image_url=uploaded_df_image.link
                )
                line_bot_api.reply_message(event.reply_token, image_message)
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Error'))

    elif msg[:1] == 'B':  # 個股股利政策資訊
        string = msg
        characters = "B"

        for x in range(len(characters)):
            stock_news_message = string.replace(characters[x], "")
            stock_news = pd.read_html("https://histock.tw/stock/" + stock_news_message + "/%E9%99%A4%E6%AC%8A%E9%99%A4"
                                                                                         "%E6%81%AF")[0]
            msg_df = stock_news.drop(index=[0])
            dfi.export(msg_df.iloc[0:5], userid + '.jpg')
            tse_stock_image = userid + '.jpg'

            im = pyimgur.Imgur(CLIENT_ID)
            uploaded_df_image = im.upload_image(tse_stock_image, title=userid)  # 上傳圖片並獲得圖片資訊
            try:
                image_message = ImageSendMessage(
                    original_content_url=uploaded_df_image.link,
                    preview_image_url=uploaded_df_image.link
                )
                line_bot_api.reply_message(event.reply_token, image_message)
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Error'))

    elif msg[:1] == 'C':  # 個股券商分點買賣資訊
        string = msg
        characters = "C"

        for x in range(len(characters)):
            stock_news_message = string.replace(characters[x], "")
            stock_news_df = pd.read_html("https://histock.tw/stock/branch.aspx?no=" + stock_news_message)[0]
            dfi.export(stock_news_df.iloc[0:10], userid + '.jpg')
            tse_stock_image = userid + '.jpg'

            im = pyimgur.Imgur(CLIENT_ID)
            uploaded_df_image = im.upload_image(tse_stock_image, title=userid)  # 上傳圖片並獲得圖片資訊
            try:
                image_message = ImageSendMessage(
                    original_content_url=uploaded_df_image.link,
                    preview_image_url=uploaded_df_image.link
                )
                line_bot_api.reply_message(event.reply_token, image_message)
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Error'))

    elif msg[:1] == 'V':  # 個股集保戶股權分散表資訊
        string = msg
        characters = "V"

        for x in range(len(characters)):
            stock_news_message = string.replace(characters[x], "")
            stock_news_df = pd.read_html("https://histock.tw/stock/equity.aspx?no=" + stock_news_message)[0]
            dfi.export(stock_news_df.iloc[0:10], userid + '.jpg')
            tse_stock_image = userid + '.jpg'

            im = pyimgur.Imgur(CLIENT_ID)
            uploaded_df_image = im.upload_image(tse_stock_image, title=userid)  # 上傳圖片並獲得圖片資訊
            try:
                image_message = ImageSendMessage(
                    original_content_url=uploaded_df_image.link,
                    preview_image_url=uploaded_df_image.link
                )
                line_bot_api.reply_message(event.reply_token, image_message)
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Error'))

    elif msg[:1] == 'S':  # 個股獲利能力資訊
        string = msg
        characters = "S"

        for x in range(len(characters)):
            stock_news_message = string.replace(characters[x], "")
            stock_news_df = \
                pd.read_html(
                    "https://histock.tw/stock/" + stock_news_message + "/%E6%AF%8F%E8%82%A1%E7%9B%88%E9%A4%98")[0]
            dfi.export(stock_news_df, userid + '.jpg')
            tse_stock_image = userid + '.jpg'

            im = pyimgur.Imgur(CLIENT_ID)
            uploaded_df_image = im.upload_image(tse_stock_image, title=userid)  # 上傳圖片並獲得圖片資訊
            try:
                image_message = ImageSendMessage(
                    original_content_url=uploaded_df_image.link,
                    preview_image_url=uploaded_df_image.link
                )
                line_bot_api.reply_message(event.reply_token, image_message)
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Error'))

    elif msg[:1] == 'T':  # 個股上個月份股價走勢圖
        string = msg
        characters = "T"

        for x in range(len(characters)):
            string_msg = string.replace(characters[x], "")
            # 詢問使用者股票代碼
            stock = twstock.realtime.get(string_msg)
            if stock['success'] == True:
                p_stock = twstock.Stock(string_msg)  # 建立 Stock 物件
                now_date = datetime.datetime.now()  # 取得查詢當下的時間
                now_year = now_date.year  # 取得查詢當下當年年份

                m_sg = twstock.realtime.get(string_msg)
                stock_message = m_sg.values()
                stock_index = list(stock_message)[1]
                stock_name = stock_index.values()

                # 取得查詢當下上個月月份
                if (now_date.month != 1):
                    last_month = now_date.month - 1
                else:
                    last_month = 12

                stock_list = p_stock.fetch(now_year, last_month)

                list_x = []
                list_y = []
                for value in stock_list:
                    list_x.append(value.date.strftime('%Y-%m-%d'))
                    list_y.append(value.close)

                plt.figure(figsize=(10, 10))  # 設定圖表區寬高
                plt.xlabel('日期', fontsize="25")  # 設定 x 軸標題內容及大小
                plt.ylabel('股價', fontsize="25")  # 設定 y 軸標題標題內容及大小
                plt.title(list(stock_name)[2], fontsize="30")  # 設定圖表標題內容及大小
                plt.plot(list_x, list_y, color='red', markersize="16", marker=".")  # 紅色，實線，標記大小 16，標記為「點」
                plt.xticks(rotation=45)  # 讓 x 坐標軸標題旋轉 45 度

                # 設定讓中文可順利顯示不亂碼
                plt.rcParams["font.sans-serif"] = "Microsoft JhengHei"  # 將字體換成 Microsoft JhengHei
                plt.rcParams["axes.unicode_minus"] = False  # 讓負號可正常顯示

                plt.savefig(userid + '.jpg')
                stock_image = userid + '.jpg'  # 上傳的圖片路徑

                im = pyimgur.Imgur(CLIENT_ID)
                uploaded_image = im.upload_image(stock_image, title=userid)  # 上傳圖片並獲得圖片資訊

                try:
                    image_message = ImageSendMessage(
                        original_content_url=uploaded_image.link,
                        preview_image_url=uploaded_image.link
                    )
                    line_bot_api.reply_message(event.reply_token, image_message)
                except:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text='Error'))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='輸入錯誤股票代號哦~'))

    elif msg[:1] == 'P':  # 個股即時報價
        string = msg
        characters = "P"

        for x in range(len(characters)):
            stock_search_name = string.replace(characters[x], "")
            stock = twstock.realtime.get(stock_search_name)
            if stock['success'] == True:
                stock_name_n = twstock.realtime.get(stock_search_name)
                stock_message = stock_name_n.values()
                stock_index = list(stock_message)[2]

                stock_name = stock_index.values()
                stock_name_price = list(stock_name)[0]

                stock_name_open = list(stock_name)[7]

                stock_name_high = list(stock_name)[8]

                stock_name_low = list(stock_name)[9]

                accumulate_trade_volume = list(stock_name)[2]  # 成交量

                buy_price = stock_name_n['realtime']['best_bid_price']
                buy_num = stock_name_n['realtime']['best_bid_volume']
                sel_price = stock_name_n['realtime']['best_ask_price']
                sel_num = stock_name_n['realtime']['best_ask_volume']

                dict_frame = {'買量': buy_num, '買價': buy_price, '賣價': sel_price, '賣量': sel_num}
                df = pd.DataFrame(dict_frame, index=range(1, 6))
                dfi.export(df, userid + '.jpg')
                stock_image = userid + '.jpg'

                im = pyimgur.Imgur(CLIENT_ID)
                uploaded_df_image = im.upload_image(stock_image, title=userid)  # 上傳圖片並獲得圖片資訊

                text2 = stock_search_name + "即時資料如下："
                text2 += "\n收盤價：" + stock_name_price
                text2 += "\n開盤價：" + stock_name_open
                text2 += "\n最高價：" + stock_name_high
                text2 += "\n最低價：" + stock_name_low
                text2 += "\n成交量：" + accumulate_trade_volume
                stock_time_price_message = [  # 串列
                    TextSendMessage(  # 傳送文字
                        text=text2
                    ),
                    ImageSendMessage(
                        original_content_url=uploaded_df_image.link,
                        preview_image_url=uploaded_df_image.link
                    )
                ]
                line_bot_api.reply_message(event.reply_token, stock_time_price_message)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='輸入錯誤股票代號哦~'))

    elif msg[:1] == 'Q':  # 股票申購資訊
        string = msg
        characters = "Q"

        for x in range(len(characters)):
            msg_number = string.replace(characters[x], "")
            int_number = int(msg_number)
            if int_number <= 10:
                url = "https://histock.tw/stock/public.aspx"
                response = requests.get(url)
                stock_listed = pd.read_html(response.text)[0]
                dfi.export(stock_listed.iloc[0:int_number], userid + '.jpg')
                stock_listed_image = userid + '.jpg'

                im = pyimgur.Imgur(CLIENT_ID)
                uploaded_stock_image = im.upload_image(stock_listed_image, title=userid)  # 上傳圖片並獲得圖片資訊
                stock_listed_price_message = [  # 串列
                    ImageSendMessage(
                        original_content_url=uploaded_stock_image.link,
                        preview_image_url=uploaded_stock_image.link
                    )
                ]
                line_bot_api.reply_message(event.reply_token, stock_listed_price_message)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='輸入錯誤或超過搜尋筆數哦~'))


if __name__ == '__main__':
    app.run()
