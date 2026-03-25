#!/usr/bin/env python3
# 解决 macOS Tk deprecation warning
import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'
"""
澳洲贷款计算器
功能：
- 标准贷款计算（月供、总利息、总还款）
- 各州印花税计算（支持 House & Land 仅土地计算）
- 费用估算（律师费、PEXA交割费）
- 计算交割缺口(settlement shortfall)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List

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
        "first_home_boost": 0,  # 首次置业减免需额外计算
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
DEFAULT_PEXA_FEE = 120  # PEXA 网络交割费平均水平

class LoanCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("澳洲贷款计算器 - 高级版")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 设置主题
        self.setup_style()
        self.create_ui()
        self.center_window()
        
    def setup_style(self):
        style = ttk.Style()
        if 'aqua' in style.theme_names():
            style.theme_use('aqua')
        style.configure('Bold.TLabel', font=('Helvetica Neue', 12, 'bold'))
        style.configure('Title.TLabel', font=('Helvetica Neue', 16, 'bold'))
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')
    
    def create_ui(self):
        # 创建 notebook 分栏
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 标签页1: 基础信息输入
        input_frame = ttk.Frame(notebook, padding=10)
        notebook.add(input_frame, text='输入信息')
        self.create_input_tab(input_frame)
        
        # 标签页2: 计算结果
        result_frame = ttk.Frame(notebook, padding=10)
        notebook.add(result_frame, text='计算结果')
        self.create_result_tab(result_frame)
        
        # 底部计算按钮
        button_frame = ttk.Frame(self.root, padding=(5, 10))
        button_frame.pack(fill=tk.X)
        ttk.Button(
            button_frame, 
            text="🧮 重新计算", 
            command=self.calculate_all
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            button_frame, 
            text="📋 清空表单", 
            command=self.clear_form
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            button_frame, 
            text="ℹ️ 帮助", 
            command=self.show_help
        ).pack(side=tk.RIGHT, padx=5)
    
    def create_input_tab(self, parent):
        # 用一个容器分为左右两列
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左栏 - 房产和贷款信息
        col1 = ttk.Frame(container, padding=10)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 房产标题
        ttk.Label(col1, text="🏠 房产信息", style='Bold.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Property Value
        ttk.Label(col1, text="房产总价值 (AUD):").pack(anchor=tk.W, pady=(0, 2))
        self.property_value_var = tk.StringVar(value="800000")
        ttk.Entry(col1, textvariable=self.property_value_var, width=28).pack(anchor=tk.W, pady=(0, 12))
        
        # 选择州
        ttk.Label(col1, text="房产所在州:").pack(anchor=tk.W, pady=(0, 2))
        self.state_var = tk.StringVar(value="QLD")
        state_combo = ttk.Combobox(col1, textvariable=self.state_var, 
                                  values=list(STAMP_DUTY_RATES.keys()), 
                                  state="readonly", width=25)
        state_combo.pack(anchor=tk.W, pady=(0, 12))
        state_combo.bind("<<ComboboxSelected>>", self.update_default_fees)
        
        # House & Land 选项
        ttk.Label(col1, text="房屋类型:").pack(anchor=tk.W, pady=(0, 2))
        self.is_hl_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            col1, 
            text="House & Land 拆分（仅土地价格计算印花税", 
            variable=self.is_hl_var,
            command=self.toggle_land_price
        ).pack(anchor=tk.W, pady=(0, 12))
        
        # Land Price (only if H&L)
        ttk.Label(col1, text="土地购买价格 (AUD - H&L):").pack(anchor=tk.W, pady=(0, 2))
        self.land_price_var = tk.StringVar(value="")
        self.land_price_entry = ttk.Entry(col1, textvariable=self.land_price_var, width=28, state=tk.DISABLED)
        self.land_price_entry.pack(anchor=tk.W, pady=(0, 12))
        
        # 贷款信息标题
        ttk.Label(col1, text="💰 贷款信息", style='Bold.TLabel').pack(anchor=tk.W, pady=(10, 10))
        
        # 贷款比例/金额
        ttk.Label(col1, text="贷款金额 (AUD):").pack(anchor=tk.W, pady=(0, 2))
        self.loan_amount_var = tk.StringVar(value="640000")
        ttk.Entry(col1, textvariable=self.loan_amount_var, width=28).pack(anchor=tk.W, pady=(0, 12))
        
        ttk.Label(col1, text="利率 (% 年息):").pack(anchor=tk.W, pady=(0, 2))
        self.interest_rate_var = tk.StringVar(value="5.5")
        ttk.Entry(col1, textvariable=self.interest_rate_var, width=28).pack(anchor=tk.W, pady=(0, 12))
        
        ttk.Label(col1, text="贷款期限 (年):").pack(anchor=tk.W, pady=(0, 2))
        self.loan_term_var = tk.StringVar(value="30")
        ttk.Entry(col1, textvariable=self.loan_term_var, width=28).pack(anchor=tk.W, pady=(0, 12))
        
        # 右栏 - 费用和现金
        col2 = ttk.Frame(container, padding=10)
        col2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(col2, text="💸 交易费用", style='Bold.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # 律师费
        ttk.Label(col2, text="律师过户费用 (AUD):").pack(anchor=tk.W, pady=(0, 2))
        self.legal_fee_var = tk.StringVar(value=str(DEFAULT_LEGAL_FEES["QLD"]))
        ttk.Entry(col2, textvariable=self.legal_fee_var, width=28).pack(anchor=tk.W, pady=(0, 12))
        
        # PEXA fee
        ttk.Label(col2, text="PEXA 网络交割费 (AUD):").pack(anchor=tk.W, pady=(0, 2))
        self.pexa_fee_var = tk.StringVar(value=str(DEFAULT_PEXA_FEE))
        ttk.Entry(col2, textvariable=self.pexa_fee_var, width=28).pack(anchor=tk.W, pady=(0, 12))
        
        # LMI 保险（可选）
        ttk.Label(col2, text="贷方抵押保险 LMI (AUD - 可选):").pack(anchor=tk.W, pady=(0, 2))
        self.lmi_fee_var = tk.StringVar(value="0")
        ttk.Entry(col2, textvariable=self.lmi_fee_var, width=28).pack(anchor=tk.W, pady=(0, 12))
        
        # 其他费用
        ttk.Label(col2, text="其他政府/经纪费用 (AUD):").pack(anchor=tk.W, pady=(0, 2))
        self.other_fees_var = tk.StringVar(value="0")
        ttk.Entry(col2, textvariable=self.other_fees_var, width=28).pack(anchor=tk.W, pady=(0, 12))
        
        # 客户现金
        ttk.Label(col2, text="💰 客户资金", style='Bold.TLabel').pack(anchor=tk.W, pady=(25, 10))
        ttk.Label(col2, text="客户手头现金/存款 (AUD):").pack(anchor=tk.W, pady=(0, 2))
        self.cash_on_hand_var = tk.StringVar(value="200000")
        ttk.Entry(col2, textvariable=self.cash_on_hand_var, width=28).pack(anchor=tk.W, pady=(0, 12))
        
        # 选项：首次置业减免
        ttk.Label(col2, text="🎁 优惠选项", style='Bold.TLabel').pack(anchor=tk.W, pady=(25, 10))
        self.first_home_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            col2,
            text="申请首次置业印花税减免",
            variable=self.first_home_var
        ).pack(anchor=tk.W, pady=(0, 12))
    
    def create_result_tab(self, parent):
        # 创建结果文本框
        self.result_text = tk.Text(parent, wrap=tk.WORD, font=('Menlo', 12))
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def toggle_land_price(self):
        """切换土地价格输入框状态"""
        if self.is_hl_var.get():
            self.land_price_entry.config(state=tk.NORMAL)
        else:
            self.land_price_entry.config(state=tk.DISABLED)
    
    def update_default_fees(self, event=None):
        """根据选择的州更新默认费用"""
        state = self.state_var.get()
        default_fee = DEFAULT_LEGAL_FEES.get(state, DEFAULT_LEGAL_FEES["default"])
        self.legal_fee_var.set(str(default_fee))
    
    def calculate_stamp_duty(self, price: float, state: str) -> float:
        """根据价格和州计算印花税"""
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
        
        # 首次置业减免（简单处理主要州）
        if self.first_home_var.get() and "first_home_exempt_up_to" in rates:
            if price <= rates["first_home_exempt_up_to"]:
                return 0.0
            elif "first_home_concession_up_to" in rates and price <= rates["first_home_concession_up_to"]:
                # 简化计算 concession
                concession = (rates["first_home_concession_up_to"] - price) / rates["first_home_concession_up_to"]
                duty *= (1 - concession)
        
        return round(duty, 2)
    
    def calculate_monthly_payment(self, principal: float, annual_rate: float, years: int) -> float:
        """计算月供"""
        if annual_rate == 0:
            return principal / (years * 12)
        monthly_rate = annual_rate / 100 / 12
        n_payments = years * 12
        payment = principal * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
        return round(payment, 2)
    
    def get_float(self, var: tk.StringVar, default: float = 0.0) -> float:
        """安全获取输入浮点数"""
        try:
            return float(var.get().strip() or "0")
        except ValueError:
            return default
    
    def calculate_all(self):
        """执行所有计算"""
        try:
            # 获取基础输入
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
                # House & Land: 只用土地价格计算
                land_price = self.get_float(self.land_price_var)
                stamp_duty = self.calculate_stamp_duty(land_price, state)
                sd_description = f"House & Land 仅土地价格: ${land_price:,.0f}"
            else:
                # 正常计算：使用总房价
                stamp_duty = self.calculate_stamp_duty(property_value, state)
                sd_description = f"完整房产价格: ${property_value:,.0f}"
            
            # 计算贷款
            monthly_payment = self.calculate_monthly_payment(loan_amount, interest_rate, int(loan_term))
            total_payments = monthly_payment * int(loan_term) * 12
            total_interest = total_payments - loan_amount
            
            # 计算总成本和交割缺口
            # 总应付 = 房价 + 所有费用 - 贷款
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
            
            # 生成结果文本
            result = "=" * 60 + "\n"
            result += "           🧮 澳洲贷款计算器 - 计算结果\n"
            result += "=" * 60 + "\n\n"
            
            result += "🏠 房产信息\n"
            result += f"  总房产价值:     ${property_value:,.2f}\n"
            result += f"  所在州:         {STAMP_DUTY_RATES[state]['description']} ({state})\n"
            if is_hl:
                land_price = self.get_float(self.land_price_var)
                result += f"  房屋类型:       House & Land (拆分)\n"
                result += f"  土地价格:       ${land_price:,.2f}\n"
            else:
                result += f"  房屋类型:       完整房产\n"
            result += "\n"
            
            result += "💰 贷款信息\n"
            result += f"  贷款金额:       ${loan_amount:,.2f}\n"
            result += f"  年利率:         {interest_rate:.2f}%\n"
            result += f"  贷款期限:       {int(loan_term)} 年\n"
            result += f"  月供:           ${monthly_payment:,.2f}\n"
            result += f"  总还款额:       ${total_payments:,.2f}\n"
            result += f"  总利息:         ${total_interest:,.2f}\n"
            result += "\n"
            
            result += "💸 交易费用\n"
            result += f"  印花税 ({sd_description}):\n"
            result += f"                  ${stamp_duty:,.2f}\n"
            result += f"  律师过户费:     ${legal_fee:,.2f}\n"
            result += f"  PEXA交割费:     ${pexa_fee:,.2f}\n"
            result += f"  LMI 保险:       ${lmi_fee:,.2f}\n"
            result += f"  其他费用:       ${other_fees:,.2f}\n"
            result += f"  💰 总交易费用:   ${stamp_duty + legal_fee + pexa_fee + lmi_fee + other_fees:,.2f}\n"
            result += "\n"
            
            result += "💵 交割缺口计算\n"
            result += f"  房产总价:                 ${property_value:,.2f}\n"
            result += f"  + 全部交易费用:           ${stamp_duty + legal_fee + pexa_fee + lmi_fee + other_fees:,.2f}\n"
            result += f"  = 总应付:                 ${total_costs:,.2f}\n"
            result += f"  - 获批贷款:               ${loan_amount:,.2f}\n"
            result += f"  = 交割需要总现金:          ${required_cash:,.2f}\n"
            result += f"  - 客户手头现有现金:        ${cash_on_hand:,.2f}\n"
            result += "  -----------------------------\n"
            if settlement_shortfall > 0:
                result += f"  ⚠️  交割缺口:              ${settlement_shortfall:,.2f}\n"
                result += "      客户需要额外准备这么多现金用于交割\n"
            else:
                result += f"  ✅ 交割盈余:              ${-settlement_shortfall:,.2f}\n"
                result += "      客户现金足够，交割后剩余\n"
            
            result += "\n" + "=" * 60 + "\n"
            result += "计算完成 - 如需修改参数请回到输入页调整后重新计算\n"
            
            # 更新结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, result)
            
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中发生错误:\n{str(e)}\n\n请检查输入是否都是有效数字。")
    
    def clear_form(self):
        """清空所有输入"""
        self.property_value_var.set("")
        self.land_price_var.set("")
        self.loan_amount_var.set("")
        self.interest_rate_var.set("")
        self.loan_term_var.set("")
        self.legal_fee_var.set("")
        self.pexa_fee_var.set("")
        self.lmi_fee_var.set("0")
        self.other_fees_var.set("0")
        self.cash_on_hand_var.set("")
        self.first_home_var.set(False)
        self.is_hl_var.set(False)
        self.toggle_land_price()
        self.result_text.delete(1.0, tk.END)
    
    def show_help(self):
        """显示帮助"""
        help_text = """澳洲高级贷款计算器 使用说明：

1. 输入房产信息
   - 填写房产总价值
   - 选择房产所在州（自动按该州税率计算印花税
   - 如果是 House & Land，勾选后填写土地价格，印花税只计算土地

2. 输入贷款信息
   - 贷款金额、年利率、贷款年限
   自动计算月供、总利息、总还款

3. 交易费用
   - 默认律师费按州预置，你可以修改为实际金额
   - PEXA 交割费默认市场均价，可以修改
   - LMI 和其他费用按需填写

4. 交割缺口
   - 输入客户手头现金
   自动计算：总房价+费用-贷款-客户现金 = 最终缺口/盈余

如有更多需求请老板提出修改 😄
"""
        messagebox.showinfo("帮助", help_text)

def main():
    root = tk.Tk()
    app = LoanCalculatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()