import os
import sys
import shutil
import subprocess
import threading
import time
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# 兼容导入 run_once
try:
    from .trade_review import run_once
except ImportError:
    _cur = os.path.dirname(os.path.abspath(__file__))
    if _cur not in sys.path:
        sys.path.append(_cur)
    from trade_review import run_once


class TradeReviewApp:
    def __init__(self, root):
        self.root = root
        self.root.title('交易复盘生成器')
        self.root.geometry('600x360')
        self.root.resizable(False, False)

        # 预览服务器进程信息
        self.server_proc = None
        self.server_port = 8000

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar(value=self._default_output_path())

        self._build_ui()

    def _default_output_path(self):
        # 默认输出到项目根 reports/trade_review.html（若不可写则回退到模块内）
        proj_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        root_reports = os.path.join(proj_root, 'reports')
        try:
            os.makedirs(root_reports, exist_ok=True)
            return os.path.join(root_reports, 'trade_review.html')
        except Exception:
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports', 'trade_review.html')

    def _build_ui(self):
        pad = {'padx': 12, 'pady': 8}
        frm = ttk.Frame(self.root)
        frm.pack(fill=tk.BOTH, expand=True)

        # 输入文件选择
        row1 = ttk.Frame(frm)
        row1.pack(fill=tk.X, **pad)
        ttk.Label(row1, text='成交报告单.xlsx:').pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.input_path, width=48).pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        ttk.Button(row1, text='浏览...', command=self._browse_input).pack(side=tk.LEFT)

        # 输出路径选择
        row2 = ttk.Frame(frm)
        row2.pack(fill=tk.X, **pad)
        ttk.Label(row2, text='输出HTML路径:').pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.output_path, width=48).pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        ttk.Button(row2, text='浏览...', command=self._browse_output).pack(side=tk.LEFT)

        # 操作按钮
        row3 = ttk.Frame(frm)
        row3.pack(fill=tk.X, **pad)
        ttk.Button(row3, text='生成报告', command=self._generate).pack(side=tk.LEFT)
        ttk.Button(row3, text='打开输出目录', command=self._open_dir).pack(side=tk.LEFT, padx=8)

        # 日志输出
        self.log = tk.Text(frm, height=12)
        self.log.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

    def _browse_input(self):
        path = filedialog.askopenfilename(title='选择成交报告单.xlsx', filetypes=[('Excel 文件', '*.xlsx;*.xls'), ('所有文件', '*.*')])
        if path:
            self.input_path.set(path)

    def _browse_output(self):
        path = filedialog.asksaveasfilename(title='选择输出HTML路径', defaultextension='.html', filetypes=[('HTML 文件', '*.html')])
        if path:
            self.output_path.set(path)

    def _open_dir(self):
        out = self.output_path.get().strip()
        if not out:
            return
        d = os.path.dirname(out)
        try:
            os.makedirs(d, exist_ok=True)
            if sys.platform.startswith('win'):
                os.startfile(d)
            else:
                import subprocess
                subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', d])
        except Exception:
            pass

    def _log(self, msg):
        self.log.insert(tk.END, msg + '\n')
        self.log.see(tk.END)

    def _sync_static_site(self, output_path: str):
        """将模块内的前端静态文件（index.html/stock.html/assets）同步到输出目录，确保交互页可用。"""
        try:
            out_dir = os.path.dirname(os.path.abspath(output_path))
            mod_reports = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
            # 拷贝 index.html / stock.html
            for fname in ['index.html', 'stock.html']:
                src = os.path.join(mod_reports, fname)
                dst = os.path.join(out_dir, fname)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
            # 拷贝 assets 目录
            assets_src = os.path.join(mod_reports, 'assets')
            assets_dst = os.path.join(out_dir, 'assets')
            if os.path.isdir(assets_src):
                if os.path.isdir(assets_dst):
                    shutil.rmtree(assets_dst, ignore_errors=True)
                shutil.copytree(assets_src, assets_dst)
            self._log('静态资源已同步到输出目录（index.html / stock.html / assets）')
        except Exception as e:
            self._log(f'静态资源同步失败：{e}')

    def _start_server_and_open(self, site_dir: str, port: int = 8000):
        """在输出目录启动本地HTTP服务器，并自动打开 index.html 进行预览。"""
        try:
            # 若已有服务器，先终止
            if self.server_proc and self.server_proc.poll() is None:
                try:
                    self.server_proc.terminate()
                    time.sleep(0.5)
                except Exception:
                    pass

            self._log(f'启动本地预览服务器: http://localhost:{port}/ （目录：{site_dir}）')
            # 使用当前Python解释器启动http.server
            self.server_proc = subprocess.Popen([sys.executable, '-m', 'http.server', str(port)], cwd=site_dir)

            # 异步打开浏览器，稍等服务器就绪
            def _open_after_delay():
                time.sleep(1.0)
                url = f'http://localhost:{port}/index.html'
                self._log(f'打开预览：{url}')
                try:
                    webbrowser.open(url)
                except Exception as e:
                    self._log(f'打开浏览器失败：{e}')

            threading.Thread(target=_open_after_delay, daemon=True).start()
        except Exception as e:
            self._log(f'预览服务器启动失败：{e}')

    def _generate(self):
        inp = self.input_path.get().strip()
        out = self.output_path.get().strip()
        if not inp:
            messagebox.showerror('错误', '请先选择成交报告单.xlsx')
            return
        try:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            self._log(f'输入: {inp}')
            self._log(f'输出: {out}')
            run_once(inp, out)
            # 同步交互页面静态资源到输出目录，前端将读取同目录的 data/*.json
            self._sync_static_site(out)
            # 启动本地服务器并自动打开 index.html
            self._start_server_and_open(os.path.dirname(out), self.server_port)
            self._log('生成完成')
            msg = f'报告已生成:\n{out}\n\n交互仪表盘：{os.path.join(os.path.dirname(out), "index.html")}\n' \
                  f'个股详情页：{os.path.join(os.path.dirname(out), "stock.html")}\n' \
                  f'数据目录：{os.path.join(os.path.dirname(out), "data")}'
            messagebox.showinfo('成功', msg)
        except Exception as e:
            self._log(f'错误: {e}')
            messagebox.showerror('错误', f'生成失败: {e}')

    def _on_close(self):
        # 关闭窗口时尝试停止服务器
        try:
            if self.server_proc and self.server_proc.poll() is None:
                self.server_proc.terminate()
                time.sleep(0.2)
        except Exception:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app = TradeReviewApp(root)
    root.protocol('WM_DELETE_WINDOW', app._on_close)
    root.mainloop()


if __name__ == '__main__':
    main()