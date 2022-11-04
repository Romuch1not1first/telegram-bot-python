from locale import currency
from matplotlib.widgets import Button
import config
import telebot
from yobit import exchange

exchanger = exchange()

bot = telebot.TeleBot(config.TOKEN)

from sql import TelbotDatabase

# DB of currency pairs
couple = ['BTC_USDT','ETH_USDT','DOGE_USDT']


@bot.message_handler(commands=['start'])
def request_handler(message):
    """Adding chat id to sql table"""
    Wallet(message.chat.id)._starter()

    bot.send_message(message.chat.id,'Good night, we are from Ukrain!')

    menu(message)


@bot.message_handler(content_types=['text'])
def menu(message):
    TelebotInterface(message).main_menu(message)



class TelebotInterface:
    def __init__(self,message):
        self.markupremove = telebot.types.ReplyKeyboardRemove()
        self.itembtn = telebot.types.KeyboardButton
        self.markupreply = telebot.types.ForceReply(selective=False)
        self.message_handl = message

        

    def main_menu(self,message):
        markup = telebot.types.ReplyKeyboardMarkup(True, True)
        markup.row(('Wallet'), ('Exchange'))
        
        bot.send_message(message.chat.id, 'Menu', reply_markup=markup)
        bot.register_next_step_handler(message, self.__menu_handler)

    def __menu_handler(self,message):
        markup = telebot.types.ReplyKeyboardMarkup(True, True)
        if message.text == 'Wallet':
            self.__wallet_menu(message)
    
        elif message.text == 'Exchange':
            markup.row(('Buy'), ('Sell'))
            markup.row('Cancel')
            bot.send_message(message.chat.id, 'What to do?', reply_markup=markup)
            bot.register_next_step_handler(message, self.__exchange_menu)

        else:
            bot.reply_to(message, 'For now, you can only use the buttons')


    def __wallet_menu(self,message):
        markup = telebot.types.ReplyKeyboardMarkup(True, True)
        markup.row('Back')
        bot.send_message(message.chat.id, 'Open', reply_markup=markup)
        for curr, vol in Wallet(message.chat.id).items_table('usd').items():
            bot.send_message(message.chat.id, str(vol)+ ' ' + str(curr))


    def __exchange_menu(self,message):
        markup = telebot.types.ReplyKeyboardMarkup(True, True)
        core = Core(message)
        markup.row('Back')
        global buy_sell
        buy_sell = message.text

        # buttons: shopping list of pairs
        if buy_sell == 'Buy':
            for coup in couple:
                markup.row(coup)

                currency = core.currency_correction(coup)
                currency = exchanger.get_currency(currency)['ticker']['last']

                currency = core.round_money(currency)

                currency = str(currency) + ' ' + coup.replace('_','/')
                bot.send_message(message.chat.id, currency, reply_markup=markup)

            bot.register_next_step_handler(message, core.couple_currency)

        # from wallet for sale
        elif buy_sell == 'Sell' and Wallet(message.chat.id).record_count() > 1:
            for cur, money in Wallet(message.chat.id).items_table('not usd').items():
                if cur != '$':
                    button = str(money) + ' - ' + str(cur)
                    markup.row(button)
            bot.send_message(message.chat.id, 'What sell?', reply_markup=markup)
            bot.register_next_step_handler(message, core.couple_currency)

        else:
            bot.send_message(message.chat.id, 'In wallet dont have cripto')
            self.main_menu(message)



    # displaying information about a pair of currencies
    def input_couple_currency(self,message, money, buy_sell):
        bot.send_message(message.chat.id, f'Price!\n{buy_sell}: {money}\nMinimal price buy 5$, maximal 5000$!', reply_markup=self.markupremove)
        bot.send_message(message.chat.id, 'Write your price:', reply_markup=self.markupreply)

    def input_couple_currency_buy_sell(self,message):
        markup = telebot.types.ReplyKeyboardMarkup(True, True)
        markup.row(('Dolars'),('Percent(%)'))
        markup.row('All')
        bot.send_message(message.chat.id, 'Choose a sales method!', reply_markup=markup)

    # entering dollars
    def input_dollars(self,message,cript):
        markup = telebot.types.ReplyKeyboardMarkup(True, True)
        markup.row('Buy')
        markup.row('Cancel')
        bot.send_message(message.chat.id, cript, reply_markup=markup)

    # input info procent
    def input_sell_procent(self,message):
        markup = telebot.types.ReplyKeyboardMarkup(True, True)
        bot.send_message(message.chat.id, 'Write sell precent from 0 to 100:', reply_markup=markup)




class Core:
    
    def __init__(self,message):
        self.interface = TelebotInterface(message)
        self.wallet = Wallet(message.chat.id)

    # currency pair information
    def couple_currency(self,message):
        global currency_save
        self.currency_save = message.text.lower()
        if message.text in couple and buy_sell == 'Buy':

            currency = self.currency_correction(message.text)
            money = exchanger.get_currency(currency)['ticker'][buy_sell.lower()]

            money = self.round_money(money)

            self.interface.input_couple_currency(message,money, buy_sell)

            bot.register_next_step_handler(message, self.__dollars)

        elif buy_sell == 'Sell':
            self.interface.input_couple_currency_buy_sell(message)
            bot.register_next_step_handler(message, self.__sell_handler)
        
        
        # Return from 'display currency pair information' to main menu
        else:
            bot.send_message(message.chat.id, 'Dont have couple',)
            self.interface.main_manu


    def currency_correction(self,currency):
        currency = currency.split(' ')
        currency = currency[-1].lower()
        if 'usd' not in currency:
            currency = currency + '_usdt'
        return currency


    def __sell_handler(self,message):
        if message.text == 'Dolars':
            bot.send_message(message.chat.id, 'Pleace write your price:')
            bot.register_next_step_handler(message, self.__dollars) 
        elif message.text == 'Percent(%)' or message.text == 'All':
            self.currency_save = self.currency_correction(self.currency_save)
            self.__sell(message)
        else:
            bot.send_message(message.chat.id, 'No such option',)
            bot.register_next_step_handler(message, self.__sell_handler)


    def __sell_cripto_handler(self,message):
        if message.text == 'Buy':
            value = self.wallet.select_value(message,'usd') + dollar
            self.wallet.change_value_currency(message,'usd',value) # придавляю количество доларов

            value = self.wallet.select_value(message,self.currency_save) - self.cript
            self.wallet.change_value_currency(message,self.currency_save,value)

            self.interface.main_menu(message)
        elif message.text == 'Cancel':
            self.interface.main_menu(message)

        else:
            bot.send_message(message.chat.id, 'Buy or Cancel?')
            bot.register_next_step_handler(message, self.__sell_cripto_handler)



    def __dollars(self,message):
        global input_num
        input_num = message.text
        currency = self.currency_correction(self.currency_save)
        global dollar
        dollar = float(message.text)
        if 5 <= dollar <= 5000:
            bot.send_message(message.chat.id,'Calculation...')
            self.cript = dollar / exchanger.get_currency(currency)['ticker']['buy']

            self.cript = self.round_money(self.cript)

            self.interface.input_dollars(message,self.cript)
            bot.register_next_step_handler(message, self.__buy_handler)
        
        
        else:
            bot.send_message(message.chat.id,'Do not qualify!')
            bot.register_next_step_handler(message,self.__dollars)



    def __buy_handler(self,message):
        if message.text == 'Buy':
            self.__buy(message)
        if message.text == 'Cancel':
            self.interface.main_menu(message)



    # buy function
    def __buy(self,message):
        'I withdraw dollars'
        
        value = self.wallet.select_value(message,'usd') - dollar
        self.wallet.change_value_currency(message,'usd',value)

        if self.currency_save in self.wallet.columns_currency():
            self.wallet.change_value_currency(message,self.currency_save,self.wallet.select_value(message,self.currency_save) + self.cript)  #прибавляем к существующему списку
        else:
            self.wallet.add_currency(message,self.currency_save)
            self.wallet.change_value_currency(message,self.currency_save,self.cript)  #добавляем новую валюту

        self.interface.main_menu(message)



    def __sell(self,message):
        if self.currency_save in self.wallet.columns_currency():
            if message.text == 'All':
                sellnow = self.wallet.select_value(message,self.currency_save)
                self.wallet.change_value_currency(message,self.currency_save,0)

                currency = self.currency_correction(self.currency_save)
                cur = exchanger.get_currency(currency)['ticker']['sell']

                cur = round(sellnow * cur, 2) # конвертирую крипту в доллары!
                self.wallet.select_value(message,'usd')
                self.wallet.change_value_currency(message,'usd',self.wallet.select_value(message,'usd') + cur) # возвращаю всю переконвертированую крипту в долары

                self.interface.main_menu(message)
            if message.text == 'Percent(%)':
                self.interface.input_sell_procent(message)
                bot.register_next_step_handler(message,self.__sell_precent)

        else:
            self.interface.main_menu(message)


    def __sell_precent(self,message):
        if 0 <= float(message.text) <=100:
            sellnow = self.wallet.select_value(message,self.currency_save) * int(message.text) / 100 # узнай % денег от общей суммы
            self.wallet.change_value_currency(message,self.currency_save, self.wallet.select_value(message,self.currency_save) - sellnow) # забираю % от общей суммы

            currency = self.currency_correction(self.currency_save)
            cur = exchanger.get_currency(currency)['ticker']['sell']
            cur = round(sellnow * cur, 2) # convert cryptocurrency to dollars!

            cur = self.round_money(cur)
            self.wallet.change_value_currency(message,'usd',float(self.wallet.select_value(message,'usd')) + float(cur)) # возвращаю % переконвертированой крипты в долары

        else:
            # bot.send_message(message.chat.id, 'Didn't qualify for sale!')
            self.__sell(message)

        # self.interface.main_menu(message)

    # rounding
    def round_money(self,money):
        return float("%.8f" % money)


class Wallet:
    def __init__(self,messageid):
        self.messageid = messageid
        self.database = TelbotDatabase()

    def _starter(self):
        show_tables = """SHOW TABLES;"""
        Flag = True

        '''Loops users by id'''
        for table in self.database.data_answer(show_tables):
            for id in table:
                if str(id) == 't' + str(self.messageid):
                    Flag = False
                    break

        if Flag:
            create_table = f"""CREATE TABLE {'t' + str(self.messageid)} (usd FLOAT);"""
            self.database.data_answer(create_table)
            insert = f"""INSERT {'t' + str(self.messageid)}(usd) VALUES(5000);"""
            self.database.data_answer(insert)

    def select_value(self,message,currency):
        core = Core(message)
        currency = core.currency_correction(currency)
        select = f"""SELECT {currency} FROM {'t' + str(self.messageid)};"""
        
        '''Gets the amount of currency'''
        answer = None
        for amount in self.database.data_answer(select):
            for number in amount:
                answer = number
        return answer

    def columns_currency(self):
        self.tables = f"""SHOW COLUMNS FROM {'t' + str(self.messageid)};"""

        '''Retrieves all speakers except usd'''
        return [db[0] for db in self.database.data_answer(self.tables) if db[0] != 'id' and 'usd']

    def record_count(self):
        '''Count table records other than 'usd' '''
        r_count = f"""SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE table_name = '{'t' + str(self.messageid)}';"""

        '''takes the number of columns itself'''
        for col in self.database.data_answer(r_count):
            for colum in col:
                answer = colum
        return float(answer)

    def add_currency(self,message,currency):
        '''Add a new column to the table with the name of the currency'''
        core = Core(message)
        currency = core.currency_correction(currency)
        table_check = Wallet.columns_currency(self)
        if currency not in table_check:
            add_currency_table = f"""ALTER TABLE {'t' + str(self.messageid)} ADD {currency} FLOAT NOT NULL DEFAULT(0);"""
            self.database.data_answer(add_currency_table)

        '''Delete if volume = 0'''
        if float(self.select_value(message,currency)) == 0.0:
            drop = f"""ALTER TABLE {'t' + str(self.messageid)} DROP COLUMN {currency};"""
            self.database.data_answer(drop)

    def change_value_currency(self,message,currency,value):
        '''Change the amount of currency in the table'''
        core = Core(message) 
        currency = core.currency_correction(currency)
        change_vol = f"""UPDATE {'t' + str(self.messageid)} SET {currency} = {value};"""
        self.database.data_answer(change_vol)

    def items_table(self,currency):
        '''I get it from the table and translate it into a dict'''
        dic = dict()
        tables = f"""SHOW COLUMNS FROM {'t' + str(self.messageid)};"""

        '''collects type and value'''
        vol = f"""SELECT * FROM {'t' + str(self.messageid)};"""

        if currency == 'usd':
            cur = [take[0] for take in self.database.data_answer(tables)]
            volume = list(self.database.data_answer(vol))[0]
        else:
            cur = [take[0] for take in self.database.data_answer(tables) if take[0] != 'usd']
            volume = list(self.database.data_answer(vol))[0][1:]


        '''pack in dict'''
        for meaning in range(len(volume)):
            dic[cur[meaning]] = volume[meaning]
        return dic





# запуск
if __name__ == '__main__':
    bot.polling(non_stop=True)
