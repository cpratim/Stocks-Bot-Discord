import pymongo, pytz
from datetime import datetime
import json
from config import MONGODB_DBNAME as dbname
from config import MONGODB_PASSWORD as password
from config import INITIAL_BALANCE
from util.helpers import *



def migrate(data, collection):
    for _id in data:
        new_data = {'_id': _id}
        new_data['name'] = data[_id]['name']
        new_data['time'] = data[_id]['time']
        new_data['balance'] = data[_id]['balance']
        new_data['holdings'] = data[_id]['holdings']
        collection.insert_one(new_data)


class Ledger(object):

    def __init__(self, init_balance = INITIAL_BALANCE):

        self.init_balance = init_balance
        self.client = pymongo.MongoClient(f"mongodb+srv://stocksbotdb:{password}@stonkbot.mphmc.mongodb.net/{dbname}?retryWrites=true&w=majority")
        
        self.collection = self.client.stocksdb.stocksbotdb

    def add_user(self, _id, name):
        data = {
            '_id': _id,
            'name': name,
            'time': sdate(),
            'balance': self.init_balance,
            'holdings': {}
        }
        self.collection.insert_one(data)

    def enter_position(self, _id, position, symbol, price, qty=None):
        data = self.collection.find_one({'_id': _id})
        balance = data['balance']
        qty = balance / price if qty is None else qty
        cost = price * qty
        if cost > balance:
            return False
        data['balance'] = balance - cost
        holdings = data['holdings']
        if symbol not in holdings:
            holdings[symbol] = {
                'position': position,
                'entry_price': price,
                'qty': qty,
                'entry_time': sdate(),
            }
        else:
            hqty, ptype, eprice = (
                holdings[symbol]['qty'],
                holdings[symbol]['position'],
                holdings[symbol]['entry_price'],
            )
            if position != ptype or qty < 0:
                return False
            avg_entry_price = ((qty * price) + (hqty * eprice)) / (qty + hqty)
            holdings[symbol]['entry_price'] = avg_entry_price
            holdings[symbol]['qty'] = qty + hqty

        self.collection.delete_one({'_id': _id})
        self.collection.insert_one(data)
        return qty

    def exit_position(self, _id, position, symbol, price, qty=None):
        data = self.collection.find_one({'_id': _id})
        balance, holdings = (
            data['balance'],
            data['holdings'],
        )
        if symbol not in holdings:
            return False
        hqty, ptype, eprice = (
            holdings[symbol]['qty'],
            holdings[symbol]['position'],
            holdings[symbol]['entry_price'],
        )
        qty = hqty if qty == None else qty

        if (
                qty > hqty or
                position == ptype or
                qty < 0 or
                (ptype == 'short' and position == 'sell') 
        ):
            return False
        if position == 'sell':
            data['balance'] = balance + qty * price
        else:
            data['balance'] = balance + qty * (2 * eprice - price)
        if hqty == qty:
            del holdings[symbol]
        else:
            holdings[symbol]['qty'] = hqty - qty

        self.collection.delete_one({'_id': _id})
        self.collection.insert_one(data)
        return qty

    def get_holdings(self, _id):
        data = self.collection.find_one({'_id': _id})
        holdings = data['holdings']
        stocklist = []
        for symbol in holdings:
            qty = holdings[symbol]['qty']
            position = holdings[symbol]['position']
            stocklist.append((symbol, qty, position))
        return stocklist

    def portfolio(self, _id):
        data = self.collection.find_one({'_id': _id})
        holdings = data['holdings']
        port = []
        for symbol in holdings:
            hqty, ptype, eprice = (
                holdings[symbol]['qty'],
                holdings[symbol]['position'],
                holdings[symbol]['entry_price'],
            )
            port.append((symbol, hqty, ptype, eprice))
        return port

    def get_balance(self, _id):
        data = self.collection.find_one({'_id': _id})
        if data is None:
            return False
        return data['balance']

    def get_all_owned(self):
        data = self.collection.find()
        owned = {}
        for user_data in data:
            _id = user_data['_id']
            holdings = user_data['holdings']
            owned[_id] = []
            for sym in holdings:
                owned[_id].append((sym, holdings[sym]['qty'], holdings[sym]['position'], holdings[sym]['entry_price']))
        return owned

    def contains(self, _id):
        data = self.collection.find_one({'_id': _id})
        return data is not None

    def get_name(self, _id):
        data = self.collection.find_one({'_id': _id})
        if data is None:
            return False
        return data['name']

    def set_name(self, _id, name):
        data = self.collection.find_one({'_id': _id})
        data['name'] = name

        self.collection.delete_one({'_id': _id})
        self.collection.insert_one(data)


def reset(collection):
    data = collection.find()
    for user_data in data:
        _id = user_data['_id']
        collection.delete_one({'_id': _id})
        user_data['holdings'] = {}
        user_data['balance'] = INITIAL_BALANCE
        collection.insert_one(user_data)

if __name__ == '__main__':
    reset()