#!/usr/bin/env python3
# 解决 macOS Tk deprecation warning
import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'
"""
澳洲贷款计算器 - 简单版
功能：
- 标准贷款计算（月供、总利息、总还款）
- 各州印花税计算（支持 House & Land 仅土地计算）
- 费用估算（律师费、PEXA交割费）
- 计算交割缺口(settlement shortfall)
"""

import tkinter as tk
from tkinter import ttk, messagebox

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
        "first_home_boost": 0,
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
    "SA": {
        "description": "South Australia",
        "brackets": [
            (0, 12000, 1.00),
            (12001, 30000, 2.00),
            (30001, 50000, 3.00),
            (50001, 100000, 3.50),
            (100001, 200000, 4.00),
            (200001, 250000, 4.25),
            (250001, 300000, 4.75),
            (300001, 500000, 5.00),
            (500001, float('inf'), 5.50),
        ],
    },
    "TAS": {
        "description": "Tasmania",
        "brackets": [
            (0, 130000, 0),
            (130001, 430000, 2.00),
            (430001, 750000, 3.00),
            (750001, float('inf'), 3.50),
        ],
    },
    "NT": {
        "description": "Northern Territory",
        "brackets": [
            (0, 525000, 0),
            (525001, 1500000, 3.00),
            (1500001, float('inf'), 4.50),
        ],
    },
    "ACT": {
        "description": "Australian Capital Territory",
        "brackets": [
            (0, 200000, 0),
            (200001, 300000, 2.00),
            (300001, 500000, 3.00),
            (500001, 750000, 4.00),
            (750001, 1000000, 5.00),
            (1000001, 1455000, 6.00),
            (1455001, float('inf'), 7.00),
        ],
    },
}

# 默认收费参考
DEFAULT_LEGAL_FEES = {
    "QLD": 1500,
    "NSW": 1800,
    "VIC": 1700,
    "default": 1600,
}
DEFAULT_PEXA_FEE = 120

class LoanCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("澳洲贷款计算器")
        self.root.geometry("600x800")
        self.root.minsize(500, 700)
        
        # 设置主题
        style = ttk.Style()
        if 'aqua' in style.theme_names():
            style.theme_use('aqua')
        
        self.create_widgets()
    
    def create_widgets(self):
        # 主画布加滚动条，防止内容太多
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 存储所有输入框
        self.entries = {}
        
        # 标题
        title = ttk.Label(main_frame, text="澳洲高级贷款计算器", font=('Helvetica', 16, 'bold'))
        title.pack(pady=(0, 20))
        
        # 房产信息区域
        self.create_section_label(main_frame, "🏠 房产信息")
        
        # 房产总价值
        self.create_label_entry(main_frame, "房产总价值 (AUD):", "property_value", "800000")
        
        # 州选择
        ttk.Label(main_frame, text="房产所在州:").pack(anchor=tk.W, pady=(5, 2))
        self.state_var = tk.StringVar(value="QLD")
        state_combo = ttk.Combobox(main_frame, textvariable=self.state_var,
                                  values=list(STAMP_DUTY_RATES.keys()),
                                  state="readonly")
        state_combo.pack(fill=tk.X, pady=(0, 8))
        state_combo.bind("<<ComboboxSelected>>", self.update_default_fees)
        
        # House & Land
        self.is_hl_var = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(
            main_frame,
            text="House & Land 拆分（仅对土地价格计算印花税）",
            variable=self.is_hl_var,
            command=self.toggle_land_price
        )
        cb.pack(anchor=tk.W, pady=(5, 8))
        
        # 土地价格
        self.create_label_entry(main_frame, "土地购买价格 (AUD - 仅H&L):", "land_price", "")
        self.land_price_entry.config(state=tk.DISABLED)
        
        # 贷款信息区域
        self.create_section_label(main_frame, "💰 贷款信息")
        self.create_label_entry(main_frame, "贷款金额 (AUD):", "loan_amount", "640000")
        self.create_label_entry(main_frame, "年利率 (%):", "interest_rate", "5.5")
        self.create_label_entry(main_frame, "贷款期限 (年):", "loan_term", "30")
        
        # 费用信息区域
        self.create_section_label(main_frame, "💸 交易费用")
        default_legal = DEFAULT_LEGAL_FEES["QLD"]
        self.create_label_entry(main_frame, "律师过户费 (AUD):", "legal_fee", str(default_legal))
        self.create_label_entry(main_frame, "PEXA 交割费 (AUD):", "pexa_fee", str(DEFAULT_PEXA_FEE))
        self.create_label_entry(main_frame, "LMI 保险 (AUD - 可选):", "lmi_fee", "0")
        self.create_label_entry(main_frame, "其他费用 (AUD):", "other_fees", "0")
        
        # 优惠选项
        self.first_home_var = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(
            main_frame,
            text="申请首次置业印花税减免",
            variable=self.first_home_var
        )
        cb.pack(anchor=tk.W, pady=(5, 8))
        
        # 客户资金区域
        self.create_section_label(main_frame, "💵 客户资金")
        self.create_label_entry(main_frame, "客户手头现金/存款 (AUD):", "cash_on_hand", "200000")
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 10))
        
        ttk.Button(
            button_frame,
            text="🧮 开始计算",
            command=self.calculate_all
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="📋 清空",
            command=self.clear_form
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="ℹ️ 帮助",
            command=self.show_help
        ).pack(side=tk.RIGHT)
        
        # 结果区域
        self.create_section_label(main_frame, "📊 计算结果")
        self.result_text = tk.Text(main_frame, wrap=tk.WORD, height=15, font=('Menlo', 11))
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 存储所有输入框
        self.entries = {}
    
    def create_section_label(self, parent, text):
        """创建区域标题"""
        label = ttk.Label(parent, text=text, font=('Helvetica', 12, 'bold'))
        label.pack(anchor=tk.W, pady=(15, 5))
    
    def create_label_entry(self, parent, label_text, name, default_value):
        """创建标签+输入框对"""
        ttk.Label(parent, text=label_text).pack(anchor=tk.W, pady=(5, 2))
        var = tk.StringVar(value=default_value)
        entry = ttk.Entry(parent, textvariable=var)
        entry.pack(fill=tk.X, pady=(0, 5))
        setattr(self, f"{name}_var", var)
        setattr(self, f"{name}_entry", entry)
        self.entries[name] = (var, entry)
    
    def toggle_land_price(self):
        if self.is_hl_var.get():
            self.land_price_entry.config(state=tk.NORMAL)
        else:
            self.land_price_entry.config(state=tk.DISABLED)
    
    def update_default_fees(self, event=None):
        state = self.state_var.get()
        default_fee = DEFAULT_LEGAL_FEES.get(state, DEFAULT_LEGAL_FEES["default"])
        self.legal_fee_var.set(str(default_fee))
    
    def get_float(self, var):
        try:
            return float(var.get().strip() or "0")
        except:
            return 0.0
    
    def calculate_stamp_duty(self, price: float, state: str) -> float:
        if price <= 0:
            return 0
        
        rates = STAMP_DUTY_RATES[state]
        duty = 0.0
        
        for lower, upper, rate in rates["brackets"]:
            if price <= lower:
                continue
            current_upper = min(upper, price)
            bracket_amount = current_upper - lower
            duty += bracket_amount * (rate / 100)
        
        # 首次置业减免
        if self.first_home_var.get() and "first_home_exempt_up_to" in rates:
            if price <= rates["first_home_exempt_up_to"]:
                return 0.0
            elif "first_home_concession_up_to" in rates and price <= rates["first_home_concession_up_to"]:
                concession = (rates["first_home_concession_up_to"] - price) / rates["first_home_concession_up_to"]
                duty *= (1 - concession)
        
        return round(duty, 2)
    
    def calculate_monthly_payment(self, principal, annual_rate, years):
        if annual_rate == 0:
            return principal / (years * 12)
        monthly_rate = annual_rate / 100 / 12
        n_payments = int(years) * 12
        payment = principal * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
        return round(payment, 2)
    
    def calculate_all(self):
        try:
            # 获取输入
            property_value = self.get_float(self.property_value_var)
            loan_amount = self.get_float(self.loan_amount_var)
            interest_rate = self.get_float(self.interest_rate_var)
            loan_term = self.get_float(self.loan_term_var)
            legal_fee = self.get_float(self.legal_fee_var)
            pexa_fee = self.get_float(self.pexa_fee_var)
            lmi_fee = self.get_float(self.lmi_fee_var)
            other_fees = self.get_float(self.other_fees_var)
            cash_on_hand = self.get_float(self.cash_on_hand_var)
            
            # 计算印花税
            state = self.state_var.get()
            is_hl = self.is_hl_var.get()
            
            if is_hl:
                land_price = self.get_float(self.land_price_var)
                stamp_duty = self.calculate_stamp_duty(land_price, state)
                sd_desc = f"House & Land 仅土地 ${land_price:,.0f}"
            else:
                stamp_duty = self.calculate_stamp_duty(property_value, state)
                sd_desc = f"完整房产 ${property_value:,.0f}"
            
            # 贷款计算
            monthly_payment = self.calculate_monthly_payment(loan_amount, interest_rate, loan_term)
            total_payments = monthly_payment * int(loan_term) * 12
            total_interest = total_payments - loan_amount
            
            # 交割缺口计算
            total_costs = (
                property_value 
                + stamp_duty 
                + legal_fee 
                + pexa_fee 
                + lmi_fee 
                + other_fees
            )
            required_cash = total_costs - loan_amount
            settlement_shortfall = required_cash - cash_on_hand
            
            # 生成结果
            result = "=" * 60 + "\n"
            result += "          🧮 澳洲贷款计算器 - 计算结果\n"
            result += "=" * 60 + "\n\n"
            
            result += "🏠 房产信息\n"
            result += f"  总房产价值:  ${property_value:,.2f}\n"
            result += f"  州:          {STAMP_DUTY_RATES[state]['description']} ({state})\n"
            if is_hl:
                land_price = self.get_float(self.land_price_var)
                result += f"  类型:        House & Land 拆分\n"
                result += f"  土地价格:    ${land_price:,.2f}\n"
            else:
                result += f"  类型:        完整房产\n"
            result += "\n"
            
            result += "💰 贷款信息\n"
            result += f"  贷款金额:    ${loan_amount:,.2f}\n"
            result += f"  年利率:      {interest_rate:.2f}%\n"
            result += f"  贷款期限:    {int(loan_term)} 年\n"
            result += f"  月供:        ${monthly_payment:,.2f}\n"
            result += f"  总还款:      ${total_payments:,.2f}\n"
            result += f"  总利息:      ${total_interest:,.2f}\n"
            result += "\n"
            
            result += "💸 交易费用\n"
            result += f"  印花税 ({sd_desc}):\n"
            result += f"               ${stamp_duty:,.2f}\n"
            result += f"  律师费:       ${legal_fee:,.2f}\n"
            result += f"  PEXA交割费:  ${pexa_fee:,.2f}\n"
            result += f"  LMI保险:     ${lmi_fee:,.2f}\n"
            result += f"  其他费用:     ${other_fees:,.2f}\n"
            result += f"  总费用:       ${stamp_duty + legal_fee + pexa_fee + lmi_fee + other_fees:,.2f}\n"
            result += "\n"
            
            result += "💵 交割缺口\n"
            result += f"  房价 + 交易费用:  ${total_costs:,.2f}\n"
            result += f"  - 获批贷款:       ${loan_amount:,.2f}\n"
            result += f"  = 需要现金:       ${required_cash:,.2f}\n"
            result += f"  - 客户已有现金:   ${cash_on_hand:,.2f}\n"
            result += "  -------------------------\n"
            
            if settlement_shortfall > 0:
                result += f"  ⚠️ 缺口: ${settlement_shortfall:,.2f}\n"
                result += "      需要额外准备这么多现金\n"
            else:
                result += f"  ✅ 盈余: ${-settlement_shortfall:,.2f}\n"
                result += "      现金足够，交割后剩余\n"
            
            result += "\n" + "=" * 60 + "\n"
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, result)
            
        except Exception as e:
            messagebox.showerror("错误", f"计算出错:\n{str(e)}\n\n请检查输入都是有效数字。")
    
    def clear_form(self):
        for name, (var, entry) in self.entries.items():
            var.set("")
        self.result_text.delete(1.0, tk.END)
        self.property_value_var.set("800000")
        self.loan_amount_var.set("640000")
        self.interest_rate_var.set("5.5")
        self.loan_term_var.set("30")
        self.cash_on_hand_var.set("200000")
        self.state_var.set("QLD")
        self.update_default_fees()
    
    def show_help(self):
        help_text = """使用说明:

1. 填写房产基本信息，选择所在州
2. 如果是 House & Land 勾选后填土地价格
   印花税只会计算土地价格
3. 填写贷款金额、利率、年限
4. 确认交易费用（默认是市场平均价）
5. 输入客户手头有多少现金
6. 点击开始计算即可得到结果

计算结果会显示：
- 月供、总利息
- 印花税
- 最终交割缺口/盈余

如有需要修改功能请提出来 😄
"""
        messagebox.showinfo("帮助", help_text)

def main():
    root = tk.Tk()
    app = LoanCalculatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()