#!/usr/bin/env python3
import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'

import tkinter as tk
from tkinter import messagebox

# 澳洲各州印花税税率表（2026年数据）
STAMP_DUTY_RATES = {
    "NSW": {
        "description": "New South Wales",
        "brackets": [
            (0, 15000, 1.25),
            (15001, 30000, 1.50),
            (30001, 100000, 1.75),
            (100001, 200000, 3.50),
            (200001, 300000, 4.50),
            (300001, 1000000, 4.90),
            (1000001, 3000000, 5.45),
            (3000001, float('inf'), 7.00),
        ],
    },
    "QLD": {
        "description": "Queensland",
        "brackets": [
            (0, 5000, 0),
            (5001, 75000, 1.50),
            (75001, 100000, 2.00),
            (100001, 250000, 3.00),
            (250001, 399999, 3.50),
            (400000, 599999, 4.50),
            (600000, 999999, 5.00),
            (1000000, float('inf'), 5.75),
        ],
        "first_home_exempt_up_to": 150000,
        "first_home_concession_up_to": 440000,
    },
    "VIC": {
        "description": "Victoria",
        "brackets": [
            (0, 25000, 1.40),
            (25001, 130000, 2.40),
            (130001, 440000, 5.00),
            (440001, 550000, 6.00),
            (550001, 960000, 6.50),
            (960001, 1600000, 7.00),
            (1600001, 2000000, 7.50),
            (2000001, float('inf'), 8.00),
        ],
    },
    "WA": {
        "description": "Western Australia",
        "brackets": [
            (0, 120000, 0),
            (120001, 150000, 1.90),
            (150001, 360000, 2.85),
            (360001, 725000, 3.80),
            (725001, 1000000, 4.75),
            (1000001, float('inf'), 5.15),
        ],
    },
    "SA": {"description": "South Australia", "brackets": [(0, 12000, 1.00), (12001, 30000, 2.00), (30001, 50000, 3.00), (50001, 100000, 3.50), (100001, 200000, 4.00), (200001, 250000, 4.25), (250001, 300000, 4.75), (300001, 500000, 5.00), (500001, float('inf'), 5.50)]},
    "TAS": {"description": "Tasmania", "brackets": [(0, 130000, 0), (130001, 430000, 2.00), (430001, 750000, 3.00), (750001, float('inf'), 3.50)]},
    "NT": {"description": "Northern Territory", "brackets": [(0, 525000, 0), (525001, 1500000, 3.00), (1500001, float('inf'), 4.50)]},
    "ACT": {"description": "Australian Capital Territory", "brackets": [(0, 200000, 0), (200001, 300000, 2.00), (300001, 500000, 3.00), (500001, 750000, 4.00), (750001, 1000000, 5.00), (1000001, 1455000, 6.00), (1455001, float('inf'), 7.00)]},
}

DEFAULT_LEGAL_FEES = {"QLD": 1500, "NSW": 1800, "VIC": 1700, "default": 1600}
DEFAULT_PEXA_FEE = 120

class LoanCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("澳洲贷款计算器")
        self.root.geometry("550x750")
        
        y = 10
        label_width = 22
        entry_width = 30
        
        # 标题
        tk.Label(root, text="澳洲贷款计算器", font=('Helvetica', 16, 'bold')).place(x=120, y=y)
        y += 50
        
        # 房产信息
        tk.Label(root, text="🏠 房产信息", font=('Helvetica', 12, 'bold')).place(x=10, y=y)
        y += 25
        
        tk.Label(root, text="房产总价值 (AUD):", width=label_width, anchor='w').place(x=10, y=y)
        self.property_value = tk.Entry(root, width=entry_width)
        self.property_value.insert(0, "800000")
        self.property_value.place(x=180, y=y)
        y += 30
        
        tk.Label(root, text="房产所在州:", width=label_width, anchor='w').place(x=10, y=y)
        self.state_var = tk.StringVar(root)
        self.state_var.set("QLD")
        self.state_menu = tk.OptionMenu(root, self.state_var, *STAMP_DUTY_RATES.keys())
        self.state_menu.config(width=26)
        self.state_menu.place(x=180, y=y-2)
        y += 35
        
        self.is_hl_var = tk.IntVar()
        cb = tk.Checkbutton(root, text="House & Land (仅土地算印花税)", variable=self.is_hl_var, command=self.toggle_land)
        cb.place(x=10, y=y)
        y += 30
        
        tk.Label(root, text="土地价格 (AUD - H&L):", width=label_width, anchor='w').place(x=10, y=y)
        self.land_price = tk.Entry(root, width=entry_width, state=tk.DISABLED)
        self.land_price.place(x=180, y=y)
        y += 30
        
        # 贷款信息
        tk.Label(root, text="💰 贷款信息", font=('Helvetica', 12, 'bold')).place(x=10, y=y)
        y += 25
        
        tk.Label(root, text="贷款金额 (AUD):", width=label_width, anchor='w').place(x=10, y=y)
        self.loan_amount = tk.Entry(root, width=entry_width)
        self.loan_amount.insert(0, "640000")
        self.loan_amount.place(x=180, y=y)
        y += 30
        
        tk.Label(root, text="年利率 (%):", width=label_width, anchor='w').place(x=10, y=y)
        self.interest_rate = tk.Entry(root, width=entry_width)
        self.interest_rate.insert(0, "5.5")
        self.interest_rate.place(x=180, y=y)
        y += 30
        
        tk.Label(root, text="贷款期限 (年):", width=label_width, anchor='w').place(x=10, y=y)
        self.loan_term = tk.Entry(root, width=entry_width)
        self.loan_term.insert(0, "30")
        self.loan_term.place(x=180, y=y)
        y += 35
        
        # 费用信息
        tk.Label(root, text="💸 交易费用", font=('Helvetica', 12, 'bold')).place(x=10, y=y)
        y += 25
        
        tk.Label(root, text="律师过户费 (AUD):", width=label_width, anchor='w').place(x=10, y=y)
        self.legal_fee = tk.Entry(root, width=entry_width)
        self.legal_fee.insert(0, str(DEFAULT_LEGAL_FEES["QLD"]))
        self.legal_fee.place(x=180, y=y)
        y += 30
        
        tk.Label(root, text="PEXA 交割费 (AUD):", width=label_width, anchor='w').place(x=10, y=y)
        self.pexa_fee = tk.Entry(root, width=entry_width)
        self.pexa_fee.insert(0, str(DEFAULT_PEXA_FEE))
        self.pexa_fee.place(x=180, y=y)
        y += 30
        
        tk.Label(root, text="LMI 保险 (AUD):", width=label_width, anchor='w').place(x=10, y=y)
        self.lmi_fee = tk.Entry(root, width=entry_width)
        self.lmi_fee.insert(0, "0")
        self.lmi_fee.place(x=180, y=y)
        y += 30
        
        tk.Label(root, text="其他费用 (AUD):", width=label_width, anchor='w').place(x=10, y=y)
        self.other_fees = tk.Entry(root, width=entry_width)
        self.other_fees.insert(0, "0")
        self.other_fees.place(x=180, y=y)
        y += 30
        
        self.first_home_var = tk.IntVar()
        cb = tk.Checkbutton(root, text="首次置业印花税减免", variable=self.first_home_var)
        cb.place(x=10, y=y)
        y += 35
        
        # 客户现金
        tk.Label(root, text="💵 客户资金", font=('Helvetica', 12, 'bold')).place(x=10, y=y)
        y += 25
        
        tk.Label(root, text="客户手头现金 (AUD):", width=label_width, anchor='w').place(x=10, y=y)
        self.cash_on_hand = tk.Entry(root, width=entry_width)
        self.cash_on_hand.insert(0, "200000")
        self.cash_on_hand.place(x=180, y=y)
        y += 40
        
        # 按钮
        tk.Button(root, text="🧮 开始计算", width=15, command=self.calculate).place(x=80, y=y)
        tk.Button(root, text="📋 清空", width=10, command=self.clear).place(x=220, y=y)
        tk.Button(root, text="ℹ️ 帮助", width=10, command=self.help).place(x=330, y=y)
        y += 50
        
        # 结果框
        tk.Label(root, text="📊 计算结果", font=('Helvetica', 12, 'bold')).place(x=10, y=y)
        y += 25
        self.result = tk.Text(root, width=62, height=12, font=('Menlo', 10))
        self.result.place(x=10, y=y)
        
        self.toggle_land()
    
    def toggle_land(self):
        if self.is_hl_var.get():
            self.land_price.config(state=tk.NORMAL)
        else:
            self.land_price.config(state=tk.DISABLED)
    
    def get_float(self, entry):
        try:
            return float(entry.get().strip() or "0")
        except:
            return 0.0
    
    def calc_stamp_duty(self, price, state):
        if price <= 0:
            return 0
        rates = STAMP_DUTY_RATES[state]
        duty = 0.0
        for lower, upper, rate in rates["brackets"]:
            if price <= lower:
                continue
            current_upper = min(upper, price)
            duty += (current_upper - lower) * (rate / 100)
        
        if self.first_home_var.get() and "first_home_exempt_up_to" in rates:
            if price <= rates["first_home_exempt_up_to"]:
                return 0
            elif "first_home_concession_up_to" in rates and price <= rates["first_home_concession_up_to"]:
                concession = (rates["first_home_concession_up_to"] - price) / rates["first_home_concession_up_to"]
                duty *= (1 - concession)
        return round(duty, 2)
    
    def calc_monthly(self, principal, rate, years):
        if rate == 0:
            return principal / (years * 12)
        monthly_rate = rate / 100 / 12
        n = int(years) * 12
        return round(principal * (monthly_rate * (1 + monthly_rate)**n) / ((1 + monthly_rate)**n - 1), 2)
    
    def calculate(self):
        try:
            pv = self.get_float(self.property_value)
            la = self.get_float(self.loan_amount)
            ir = self.get_float(self.interest_rate)
            lt = self.get_float(self.loan_term)
            lf = self.get_float(self.legal_fee)
            pf = self.get_float(self.pexa_fee)
            lm = self.get_float(self.lmi_fee)
            ot = self.get_float(self.other_fees)
            cash = self.get_float(self.cash_on_hand)
            
            state = self.state_var.get()
            is_hl = self.is_hl_var.get()
            
            if is_hl:
                lp = self.get_float(self.land_price)
                sd = self.calc_stamp_duty(lp, state)
                sd_desc = f"H&L 土地 ${lp:,.0f}"
            else:
                sd = self.calc_stamp_duty(pv, state)
                sd_desc = f"全价 ${pv:,.0f}"
            
            monthly = self.calc_monthly(la, ir, lt)
            total_pay = monthly * int(lt) * 12
            total_int = total_pay - la
            
            total_cost = pv + sd + lf + pf + lm + ot
            req_cash = total_cost - la
            shortfall = req_cash - cash
            
            text = "=" * 55 + "\n"
            text += "       澳洲贷款计算器 - 计算结果\n"
            text += "=" * 55 + "\n\n"
            text += f"房产总价:      ${pv:,.2f}\n"
            text += f"所在州:        {STAMP_DUTY_RATES[state]['description']}\n"
            if is_hl:
                text += f"类型:          House & Land, 土地 ${self.get_float(self.land_price):,.0f}\n"
            text += "\n"
            text += f"贷款金额:      ${la:,.2f}\n"
            text += f"年利率:        {ir:.2f}%\n"
            text += f"贷款期限:      {int(lt)} 年\n"
            text += f"月供:          ${monthly:,.2f}\n"
            text += f"总还款:        ${total_pay:,.2f}\n"
            text += f"总利息:        ${total_int:,.2f}\n"
            text += "\n"
            text += f"印花税 ({sd_desc}):\n"
            text += f"               ${sd:,.2f}\n"
            text += f"律师费:         ${lf:,.2f}\n"
            text += f"PEXA 交割费:   ${pf:,.2f}\n"
            text += f"LMI 保险:      ${lm:,.2f}\n"
            text += f"其他费用:       ${ot:,.2f}\n"
            text += f"总费用:         ${sd+lf+pf+lm+ot:,.2f}\n"
            text += "\n"
            text += "交割缺口计算:\n"
            text += f"  房价+费用:   ${total_cost:,.2f}\n"
            text += f"  - 贷款:      ${la:,.2f}\n"
            text += f"  = 需要现金:  ${req_cash:,.2f}\n"
            text += f"  - 已有现金:  ${cash:,.2f}\n"
            text += "  ---------------------\n"
            if shortfall > 0:
                text += f"  ⚠️ 缺口:  ${shortfall:,.2f}\n"
                text += "      需要额外准备现金\n"
            else:
                text += f"  ✅ 盈余:  ${-shortfall:,.2f}\n"
                text += "      现金足够，有剩余\n"
            
            text += "\n" + "=" * 55 + "\n"
            
            self.result.delete(1.0, tk.END)
            self.result.insert(1.0, text)
            
        except Exception as e:
            messagebox.showerror("错误", f"计算出错: {str(e)}")
    
    def clear(self):
        entries = [
            self.property_value, self.land_price, self.loan_amount,
            self.interest_rate, self.loan_term, self.legal_fee,
            self.pexa_fee, self.lmi_fee, self.other_fees, self.cash_on_hand
        ]
        for e in entries:
            e.delete(0, tk.END)
        self.result.delete(1.0, tk.END)
        self.property_value.insert(0, "800000")
        self.loan_amount.insert(0, "640000")
        self.interest_rate.insert(0, "5.5")
        self.loan_term.insert(0, "30")
        self.legal_fee.insert(0, str(DEFAULT_LEGAL_FEES["QLD"]))
        self.pexa_fee.insert(0, str(DEFAULT_PEXA_FEE))
        self.lmi_fee.insert(0, "0")
        self.other_fees.insert(0, "0")
        self.cash_on_hand.insert(0, "200000")
    
    def help(self):
        text = """使用说明:

1. 填写房产总价，选择所在州
2. 如果是 House & Land 打勾，填写土地价格
   印花税只会计算土地价格
3. 填写贷款信息
4. 确认交易费用（默认是市场平均价）
5. 输入客户现有现金
6. 点击开始计算

结果直接显示在下方，包含：
- 贷款月供和总利息
- 印花税
- 交割缺口/盈余
"""
        messagebox.showinfo("帮助", text)

def main():
    root = tk.Tk()
    app = LoanCalculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()