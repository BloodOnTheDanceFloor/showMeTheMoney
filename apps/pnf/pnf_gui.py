import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import sys
import math

# 兼容作为包或脚本运行的导入逻辑
try:
    from .pnf_chart import PNFChart  # 当以包运行：python -m apps.pnf.pnf_gui
except ImportError:
    # 当以脚本运行：python apps\pnf\pnf_gui.py 或在apps\pnf目录下执行
    _cur = os.path.dirname(os.path.abspath(__file__))
    if _cur not in sys.path:
        sys.path.append(_cur)
    from pnf_chart import PNFChart

class PNFChartApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PNF图表生成器")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        self.excel_path = None
        self.pnf_chart = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        
        # 文件选择
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="Excel文件:").pack(side=tk.LEFT, padx=5)
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="浏览...", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        
        # 参数设置
        param_frame = ttk.Frame(control_frame)
        param_frame.pack(fill=tk.X, pady=5)

        # 格值模式选择（预设 / 固定值）
        ttk.Label(param_frame, text="格值来源:").pack(side=tk.LEFT, padx=10)
        self.box_mode_var = tk.StringVar(value='preset')
        ttk.Radiobutton(param_frame, text='预设', value='preset', variable=self.box_mode_var, command=self.on_box_mode_change).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(param_frame, text='固定值', value='fixed', variable=self.box_mode_var, command=self.on_box_mode_change).pack(side=tk.LEFT, padx=2)

        # 预设格值选项（基于股价中位数的建议值列表）
        ttk.Label(param_frame, text="预设格值:").pack(side=tk.LEFT, padx=5)
        self.box_preset_var = tk.StringVar()
        self.box_preset_combo = ttk.Combobox(param_frame, textvariable=self.box_preset_var, width=10, state='readonly')
        self.box_preset_combo['values'] = ('0.25','0.5','1','2','4','5','50','500')
        self.box_preset_combo.current(2)  # 默认选中 '1'
        self.box_preset_combo.pack(side=tk.LEFT, padx=5)

        # 固定格值输入
        ttk.Label(param_frame, text="固定格值:").pack(side=tk.LEFT, padx=5)
        self.box_value_var = tk.DoubleVar(value=1.0)
        self.box_value_entry = ttk.Entry(param_frame, textvariable=self.box_value_var, width=10)
        self.box_value_entry.pack(side=tk.LEFT, padx=5)
        # 默认禁用固定值输入（初始为预设模式）
        self.box_value_entry.configure(state='disabled')
        
        # 反转格数
        ttk.Label(param_frame, text="反转格数:").pack(side=tk.LEFT, padx=5)
        self.reversal_boxes_var = tk.IntVar(value=1)
        ttk.Spinbox(param_frame, from_=1, to=5, increment=1, textvariable=self.reversal_boxes_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # 按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="加载数据", command=self.load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="生成图表", command=self.generate_chart).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存图表", command=self.save_chart).pack(side=tk.LEFT, padx=5)
        
        # 信息显示区域
        info_frame = ttk.LabelFrame(main_frame, text="信息", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        self.info_text = tk.Text(info_frame, height=5, width=80)
        self.info_text.pack(fill=tk.X, expand=True)
        
        # 图表显示区域
        chart_frame = ttk.LabelFrame(main_frame, text="PNF图表", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.figure = plt.Figure(figsize=(10, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        # 禁用约束布局，避免交互注释影响图表尺寸
        try:
            self.figure.set_constrained_layout(False)
        except Exception:
            pass
        # 悬停提示
        self.hover_annot = None
        self.hover_arrow = None
        self.mark_artists = []
        self.hover_cid = self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        
        # 默认加载当前目录下的Excel文件
        default_excel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "工作簿1.xlsx")
        if os.path.exists(default_excel):
            self.file_path_var.set(default_excel)
            self.excel_path = default_excel
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx;*.xls"), ("所有文件", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.excel_path = file_path

    def on_box_mode_change(self):
        mode = self.box_mode_var.get()
        if mode == 'preset':
            self.box_preset_combo.configure(state='readonly')
            self.box_value_entry.configure(state='disabled')
        else:
            self.box_preset_combo.configure(state='disabled')
            self.box_value_entry.configure(state='normal')
    
    def log_info(self, message):
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
    
    def load_data(self):
        if not self.excel_path:
            messagebox.showerror("错误", "请先选择Excel文件")
            return
        
        try:
            # 保留历史信息，不在加载数据时清空
            reversal_boxes = self.reversal_boxes_var.get()
            mode = self.box_mode_var.get()
            if mode == 'fixed':
                try:
                    fixed_val = float(self.box_value_var.get())
                except (TypeError, ValueError):
                    messagebox.showerror("错误", "固定格值必须是大于0的浮点数")
                    return
                if fixed_val <= 0:
                    messagebox.showerror("错误", "固定格值必须大于0")
                    return
                self.pnf_chart = PNFChart(self.excel_path, reversal_boxes=reversal_boxes, box_size_value=fixed_val)
            else:
                # 预设模式：初次加载不带选择，让后端根据中位数提供建议
                self.pnf_chart = PNFChart(self.excel_path, reversal_boxes=reversal_boxes, box_size_choice=None)
            success = self.pnf_chart.load_data()
            
            if success:
                self.log_info(f"数据加载成功: {len(self.pnf_chart.data)}行")
                self.log_info(f"价格范围: {self.pnf_chart.min_price:.2f} - {self.pnf_chart.max_price:.2f}")
                # 根据建议值设置预设下拉框的默认选中
                if mode == 'preset' and getattr(self.pnf_chart, 'suggested_box_size', None):
                    suggested = f"{self.pnf_chart.suggested_box_size:g}"
                    # 如果建议在列表中，选中；否则保持现有选择
                    if suggested in self.box_preset_combo['values']:
                        self.box_preset_var.set(suggested)
                mode_text = "固定值" if mode == 'fixed' else "预设"
                self.log_info(f"格值: {self.pnf_chart.box_size:.4f}  模式: {mode_text}")
                if getattr(self.pnf_chart, 'title', None):
                    self.log_info(f"A1标题: {self.pnf_chart.title}")
            else:
                self.log_info("数据加载失败")
        except Exception as e:
            self.log_info(f"错误: {str(e)}")
            messagebox.showerror("错误", f"加载数据时出错: {str(e)}")
    
    def generate_chart(self):
        if not self.pnf_chart or self.pnf_chart.data is None:
            messagebox.showerror("错误", "请先加载数据")
            return
        
        try:
            # 在生成前应用当前格值选择
            mode = self.box_mode_var.get()
            if mode == 'fixed':
                try:
                    fixed_val = float(self.box_value_var.get())
                    if fixed_val <= 0:
                        raise ValueError
                    self.pnf_chart.box_size = fixed_val
                except Exception:
                    messagebox.showerror("错误", "固定格值必须是大于0的浮点数")
                    return
            else:
                try:
                    preset_val = float(self.box_preset_var.get())
                    if preset_val <= 0:
                        raise ValueError
                    self.pnf_chart.box_size = preset_val
                except Exception:
                    messagebox.showerror("错误", "请选择有效的预设格值")
                    return
            # 计算PNF图表数据
            success = self.pnf_chart.calculate_pnf()
            if not success:
                self.log_info("生成PNF图表数据失败")
                return
            
            # 清除之前的图表
            self.ax.clear()
            self.mark_artists = []
            self.hover_arrow = None
            # 重新初始化悬停注释框（保证在重新加载或重新生成后可用）
            self.hover_annot = self.ax.annotate(
                "", xy=(0,0), xytext=(15,15), textcoords='offset points',
                bbox=dict(boxstyle='round', fc='w', alpha=0.8),
                arrowprops=dict(arrowstyle='->')
            )
            self.hover_annot.set_visible(False)
            
            # 设置Y轴范围（按格值对齐到网格）
            box = self.pnf_chart.box_size
            y_min = math.floor(self.pnf_chart.min_price / box) * box
            y_max = math.ceil(self.pnf_chart.max_price / box) * box
            self.ax.set_ylim(y_min, y_max)
            
            # 设置Y轴刻度为每一格值，并全部标出
            ticks = []
            t = y_min
            while t <= y_max + 1e-9:
                ticks.append(t)
                t += self.pnf_chart.box_size
            self.ax.set_yticks(ticks)
            
            # 设置X轴范围为列数量（文本绘制不自动扩展X轴）
            col_count = len(self.pnf_chart.chart_data)
            self.ax.set_xlim(-0.5, max(col_count - 0.5, 0.5))
            self.ax.set_xticks(range(col_count))
            
            # 在信息窗口中提示列数量
            self.log_info(f"列数量: {col_count}")
            
            # 绘制水平网格线（与刻度一致）
            for ty in ticks:
                self.ax.axhline(y=ty, color='lightgray', linestyle='-', alpha=0.5)
            
            # 绘制PNF图表
            # 提取每列的日期用于 X 轴标签
            dates = [str(date) for date, _ in self.pnf_chart.chart_data]
            
            # 设置 X 轴刻度和标签
            self.ax.set_xticks(range(len(self.pnf_chart.chart_data)))
            self.ax.set_xticklabels(dates, rotation=45, ha='right')
            self.ax.set_xlabel('日期')
            
            # 绘制 PNF 图表（带交互标记）
            for mp in getattr(self.pnf_chart, 'mark_points', []):
                col_idx = mp['col']
                price = mp['price']
                symbol = mp['symbol']
                # 金融标准：上涨(X)用红色，下跌(O)用绿色
                color = 'red' if symbol == 'X' else 'green'
                artist = self.ax.text(col_idx, price, symbol, ha='center', va='center', color=color, fontsize=12)
                self.mark_artists.append({'artist': artist, 'meta': mp})
            
            # 计算每列的总成交额
            column_turnovers = {}
            for mp in getattr(self.pnf_chart, 'mark_points', []):
                col = mp['col']
                turnover = mp.get('turnover', 0)
                if col not in column_turnovers:
                    column_turnovers[col] = 0
                column_turnovers[col] += turnover
            
            # 设置Y轴刻度标签为总成交额
            y_ticks = self.ax.get_yticks()
            y_tick_labels = []
            for y in y_ticks:
                # 找到y值所在列
                col_at_y = -1
                for mp in getattr(self.pnf_chart, 'mark_points', []):
                    if abs(mp['price'] - y) < self.pnf_chart.box_size / 2:
                        col_at_y = mp['col']
                        break
                
                if col_at_y != -1 and col_at_y in column_turnovers:
                    turnover_str = f"{column_turnovers[col_at_y]/1e8:.2f}亿" if column_turnovers[col_at_y] > 1e8 else f"{column_turnovers[col_at_y]/1e4:.2f}万"
                    y_tick_labels.append(turnover_str)
                else:
                    y_tick_labels.append(f"{y:.2f}")

            # self.ax.set_yticklabels(y_tick_labels)
            self.ax.set_yticklabels(y_tick_labels)


            # 设置图表标题和标签
            reversal_type = f"{self.pnf_chart.reversal_boxes}点图"
            # 使用 Excel A1 标题（去除前导空格）作为图表标题
            if getattr(self.pnf_chart, 'title', None):
                self.ax.set_title(self.pnf_chart.title)
            else:
                self.ax.set_title(f"点数图 (PNF) - 格值: {self.pnf_chart.box_size:.2f} - {reversal_type}")
            self.ax.set_xlabel("列")
            self.ax.set_ylabel("价格")
            
            # 显示图表
            self.ax.grid(True)
            self.canvas.draw()
            
            self.log_info("PNF图表生成成功")
        except Exception as e:
            self.log_info(f"错误: {str(e)}")
            messagebox.showerror("错误", f"生成图表时出错: {str(e)}")

    def on_hover(self, event):
        # 鼠标悬停事件处理，显示标记元信息
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            if self.hover_annot:
                self.hover_annot.set_visible(False)
            if self.hover_arrow:
                self.hover_arrow.set_visible(False)
            self.canvas.draw_idle()
            return

        # 近邻阈值判断（容差），避免依赖字体命中检测
        hit_item = None
        min_dist = float('inf')
        
        for item in self.mark_artists:
            meta = item['meta']
            col = meta['col']
            price = meta['price']
            dist = (event.xdata - col)**2 + ((event.ydata - price) / self.pnf_chart.box_size)**2
            if dist < min_dist:
                min_dist = dist
                hit_item = item

        if hit_item is None or min_dist > 0.5: # 调整阈值
            if self.hover_annot:
                self.hover_annot.set_visible(False)
            if self.hover_arrow:
                self.hover_arrow.set_visible(False)
            self.canvas.draw_idle()
            return

        meta = hit_item['meta']
        col = meta['col']
        price = meta['price']
        dt = meta['date']
        op = meta['open']
        cl = meta['close']
        hi = meta['high']
        lo = meta['low']
        turnover = meta.get('turnover', 0)
        turnover_str = f"{turnover/1e8:.2f}亿" if turnover > 1e8 else f"{turnover/1e4:.2f}万"
        # 使用兼容性更好的符号，避免字体缺失：上 '^'（红），下 'v'（绿），平盘 '—'
        is_up = cl > op
        is_down = cl < op
        arrow_symbol = '^' if is_up else ('v' if is_down else '—')
        arrow_color = 'red' if is_up else ('green' if is_down else 'black')
        info_text = (
            f"列: {col + 1}\n"
            f"时间: {dt}\n"
            f"坐标: ({col + 1}, {price:.2f})\n"
            f"开盘: {op:.2f}  收盘: {cl:.2f}\n"
            f"最高: {hi:.2f}  最低: {lo:.2f}\n"
            f"成交额: {turnover_str}\n"
            f"标记: {arrow_symbol}"
        )

        # 更新注释框位置与文本
        self.hover_annot.xy = (col, price)
        self.hover_annot.set_text(info_text)
        self.hover_annot.set_visible(True)

        # 在标记位置叠加箭头/一字
        y_offset = max(self.pnf_chart.box_size * 0.2, 0.1)
        if self.hover_arrow is None:
            self.hover_arrow = self.ax.text(col, price + y_offset, arrow_symbol, color=arrow_color,
                                            fontsize=14, ha='center', va='bottom', zorder=5)
        else:
            self.hover_arrow.set_position((col, price + y_offset))
            self.hover_arrow.set_text(arrow_symbol)
            self.hover_arrow.set_color(arrow_color)
            self.hover_arrow.set_visible(True)

        self.canvas.draw_idle()
    
    def save_chart(self):
        if not self.pnf_chart or not hasattr(self.pnf_chart, 'chart_data') or not self.pnf_chart.chart_data:
            messagebox.showerror("错误", "请先生成图表")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                title="保存图表",
                defaultextension=".png",
                filetypes=[("PNG图片", "*.png"), ("所有文件", "*.*")]
            )
            
            if file_path:
                self.figure.savefig(file_path)
                self.log_info(f"图表已保存至: {file_path}")
                messagebox.showinfo("成功", f"图表已保存至: {file_path}")
        except Exception as e:
            self.log_info(f"错误: {str(e)}")
            messagebox.showerror("错误", f"保存图表时出错: {str(e)}")

def main():
    root = tk.Tk()
    app = PNFChartApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()