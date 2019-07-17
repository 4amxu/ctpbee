from threading import Thread
from time import sleep

from flask import request, render_template, url_for, redirect
from flask.views import MethodView

from ctpbee import CtpBee, current_app
from ctpbee import helper
from .default_settings import DefaultSettings, true_response, false_response
from .ext import io

is_send = True


class AccountView(MethodView):
    def get(self):
        return render_template("account.html")


class LoginView(MethodView):
    def get(self):
        return render_template("login.html")

    def post(self):
        info = request.values
        app = CtpBee(info.get("username"), __name__)
        login_info = {
            "CONNECT_INFO": info,
            "INTERFACE": "ctp",
            "TD_FUNC": True,
            "MD_FUNC": True,
        }
        app.config.from_mapping(login_info)
        default = DefaultSettings("default_settings", app, io)
        app.start()

        def run(app: CtpBee):
            while True:
                app.query_position()
                sleep(1)
                app.query_account()
                sleep(1)

        p = Thread(target=run, args=(app,))
        p.start()
        return redirect(url_for("index"))


class IndexView(MethodView):
    def get(self):
        from .default_settings import contract_list
        global is_send
        if is_send:
            sleep(1)
            io.emit("contract", contract_list)
            print("发送emit", contract_list)
            is_send = False
        return render_template("index.html")


class MarketView(MethodView):
    def post(self):
        symbol = request.values.get("symbol")
        current_app.subscribe(symbol)
        return true_response(message="订阅成功")

    def get(self):
        return render_template("market.html")


class OrderView(MethodView):
    def post(self):
        """ 发单 """
        info = request.values
        local_symbol = info.get("local_symbol")
        direction = info.get("direction"),
        offset = info.get("offset")
        type = info.get("type"),
        price = info.get("price")
        volume = info.get("volume")
        req = helper.generate_order_req_by_str(symbol=local_symbol,
                                               exchange=current_app.recorder.get_contract(
                                                   local_symbol=local_symbol).exchange.value,
                                               direction=direction, offset=offset, volume=volume, price=price, type=type
                                               )
        try:
            current_app.send_order(req)
            return true_response(message="成功下单")
        except Exception:
            return false_response(message="下单失败")

    def delete(self):
        """ 撤单 """
        info = request.values
        local_symbol = info.get("local_symbol")
        order_id = info.get("order_id")
        req = helper.generate_cancle_req_by_str(symbol=local_symbol, exchange=current_app.recorder.get_contract(
            local_symbol=local_symbol).exchange.value, order_id=order_id)
        try:
            current_app.cancle_order(req)
            return true_response(message="成功撤单")
        except Exception:
            return false_response(message="撤单失败")
