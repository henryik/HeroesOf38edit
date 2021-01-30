import pandas as pd
import tkinter as tk
from tkinter import ttk, scrolledtext as tkst
from tkinter import messagebox, filedialog
import os, shutil


class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("三國群英傳8 存檔修改v0.2")
        self.iconbitmap("tools.ico")
        self.resizable(False, False)
        style = ttk.Style()
        style.configure("Treeview.Heading", font=(None, 12))
        style.configure('Treeview', rowheight=20)
        self.df = None
        self.tree = ttk.Treeview(self, height=20)
        self.font = "Consolas 12"
        self.default = []
        self.header, self.footer = "", []
        self.labels = []
        self.data = []
        self.opened_file = None
        self.group_map = None
        self.path = ""
        self.imap, self.mapping = self.func()
        tk.Label(self, text="金錢", font=self.font).grid(row=0, column=1, sticky="e")
        tk.Label(self, text="糧食", font=self.font).grid(row=1, column=1, sticky="e")
        for num, i in enumerate((0, 0)):
            ent = tk.Entry(self)
            ent.grid(row=num, column=2)
            ent.insert("end", i)
            ent.config(state="disabled")
            self.labels.append(ent)
        header = ("16位元", "物品", "數量(16位元)", "數量", "種類")
        width = (80, 300, 80, 80, 100)
        self.tree["columns"] = header
        self.tree["displaycolumns"] = ("16位元", "物品", "數量", "種類")
        self.tree.grid(row=3, column=0, columnspan=6)
        self.tree.tag_configure('T', font='Consolas 10')
        self.t_vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.t_vsb.grid(row=3, column=8, sticky="ns")
        self.tree.configure(yscrollcommand=self.t_vsb.set)
        for txt, w in zip(header, width):
            self.tree.column(txt, width=w, anchor="w")
            self.tree.heading(txt, text=txt, anchor='w',
                              command=lambda _col=txt: self.tree_sort(self.tree, _col, False))
        self.tree['show'] = 'headings'
        self.open_but = tk.Button(self, text="開啟", font=self.font, command=self.open_file, relief="groove")
        self.open_but.grid(row=0, column=0, rowspan=2, sticky="nesw")
        tk.Button(self, text="尋找", font=self.font, command=self.seek_address, relief="groove"
                  ).grid(row=0, column=3, rowspan=2, sticky="nesw")
        tk.Button(self, text="存檔", font=self.font, command=self.save_file, relief="groove"
                  ).grid(row=0, column=4, rowspan=2, sticky="nesw")
        tk.Button(self, text="離開", font=self.font, command=self.destroy, relief="groove"
                  ).grid(row=0, column=5, rowspan=2, sticky="nesw")
        self.tree.bind("<Button-3>", self.popup_menu)
        self.msg_var = tk.StringVar(value="請選擇存檔")
        self.msg = tk.Label(self, textvariable=self.msg_var)
        self.msg.grid(row=4, column=0, columnspan=6, padx=(5, 0), sticky="w")
        menuBar = tk.Menu(self, tearoff=0)
        menuBar.add_command(label="關於", command=lambda: AboutWin(self))
        self.config(menu=menuBar)

    def add_item(self):
        self.tree.selection_set(self.tree.insert("", 0, values=("???","???","01",1,"???"), tags="T"))

    @staticmethod
    def dec_to_hex_rev(i):
        s = hex(i)[2:]
        if len(s) % 2:
            s = "0" + s
        return "ff22" + "".join(map(str.__add__, s[-2::-2], s[-1::-2])).ljust(8, '0')

    @staticmethod
    def func():
        df = pd.DataFrame(code.split("\n"))
        df = df[0].str.replace(r"(?<!\+)[0-9]{4}", "").str.split(expand=True, n=2)
        df["group"] = ((~df[0].str.contains("[A-Z0-9]")).cumsum())
        df[0] = df[0].str.strip("：")
        group_map = df[~df[0].str.contains("[A-Z0-9]")].set_index("group")[0].to_dict()
        tmp = df[df[0].str.contains("[A-Z0-9]")].copy()
        tmp["Code"] = (tmp[0] + tmp[1]).str.lower()
        tmp = tmp.fillna("")
        tmp = tmp[["Code", 2, "group"]]
        tmp.columns = ["Code", "Desc", "Group"]
        tmp["Group"] = tmp["Group"].map(group_map).str.replace("代碼", "")
        return tmp, tmp.set_index("Code").to_dict(orient="index")

    def tree_sort(self, tv, col, reverse):
        items = [(tv.set(k, col), k) for k in tv.get_children('')]
        items.sort(reverse=reverse)

        for index, (val, k) in enumerate(items):
            tv.move(k, '', index)

        tv.heading(col, command=lambda: self.tree_sort(tv, col, not reverse))

    def popup_menu(self, event=None):
        if isinstance(event.widget, ttk.Treeview):
            iid = self.tree.identify_row(event.y)
            if not iid:
                self.open_file()
                return
            rmenu = tk.Menu(None, tearoff=0, takefocus=0)
            item_display = tk.Menu(self, tearoff=0)
            amount_display = tk.Menu(self, tearoff=0)
            rmenu.add_command(label=" 新增物品", font="微軟正黑體 9", command=self.add_item)
            rmenu.add_cascade(label=" 修改物品", menu=item_display, font="微軟正黑體 9")
            for i in self.imap["Group"].unique():
                m = tk.Menu(self, tearoff=0)
                item_display.add_cascade(label=i, menu=m, font="微軟正黑體 9")
                for j in self.imap.loc[self.imap["Group"].eq(i), "Desc"]:
                    m.add_command(label=j, font="微軟正黑體 9",
                                  command=lambda iid=iid, j=j: self.change_item(iid, j))
            rmenu.add_cascade(label=" 修改數量", menu=amount_display, font="微軟正黑體 9")
            for i in (1, 5, 10, 25, 50, 75, 99, '全10', '全50', '全99'):
                amount_display.add_command(label=i, font="微軟正黑體 9",
                                           command=lambda iid=iid, i=i: self.change_quantity(iid, i))
            rmenu.tk_popup(event.x_root + 40, event.y_root + 10, entry="0")

    def change_item(self, iid="", text=""):
        res = self.df[self.df["iDesc"].eq(text)]
        if len(res):
            num = str(res.index[0])
            self.tree.see(num)
            self.tree.selection_set(num)
            messagebox.showerror("錯誤", "已擁有該物品！")
            return
        cur = self.tree.item(iid)["values"]
        s = self.imap.loc[self.imap["Desc"].eq(text)]
        for i in s.itertuples(index=False):
            cur[0], cur[1], cur[4] = i
        self.tree.item(iid, value=cur)

    def change_quantity(self, iid="", num=1):
        if isinstance(num, str):
            num = int(num[1:])
            for child in self.tree.get_children():
                cur = self.tree.item(child)["values"]
                cur[2], cur[3] = hex(num)[2:], num
                self.tree.item(child, value=cur)
        else:
            cur = self.tree.item(iid)["values"]
            cur[2], cur[3] = hex(num)[2:], num
            self.tree.item(iid, value=cur)

    def clear_all(self):
        self.df = None
        self.tree.delete(*self.tree.get_children())
        self.data = []
        self.default = []
        self.header, self.footer = "", []
        self.opened_file = None
        self.group_map = None
        self.path = ""

    @staticmethod
    def count_to_int(content):
        cty_pat = "0000010f000000436f756e74727947616d6544617461"
        pos = content.find(cty_pat)
        s = content[pos - 4:pos]
        return int("".join(map(str.__add__, s[-2::-2], s[-1::-2])), 16), s+cty_pat

    def save_file(self):
        start = []
        footer = "".join(self.footer[::-1])
        res = self.header+"".join(self.default[::-1])+footer
        item_count = 0
        for child in self.tree.get_children():
            item_count += 1
            v = self.tree.item(child)["values"]
            start.append("ff22"+str(v[0]).rjust(4, "0")+"0000"+"ff22"+str(v[2]).rjust(2, "0")+"000000")
        rep = "ff22"+hex(item_count)[2:].rjust(2, "0")+"000000"+"".join(start)+footer
        try:
            shutil.copy2(self.path, self.path+".bak")
            self.msg_var.set("成功備份至 {}".format((self.path+'.bak').split("/")[-1]))
        except PermissionError:
            messagebox.showerror("備份失敗", "不能備份檔案！")
            return
        with open(self.path, "rb") as f:
            content = f.read().hex()
            d, old = self.count_to_int(content)
            diff = d + 12*(item_count-int(self.header[4:6], 16))
            new = hex(diff)[4:]+hex(diff)[2:4]+old[4:]
        with open(self.path, "wb") as e:
            try:
                e.write(bytearray.fromhex(content.replace(res, rep).replace(old, new)))
                messagebox.showinfo("成功", "已存檔至 {}".format(self.path.split('/')[-1]))
            except PermissionError:
                messagebox.showerror("儲存失敗", "不能儲存檔案！")

    def seek_address(self):
        if not self.opened_file:
            messagebox.showerror("錯誤", "先選擇存檔！")
            return
        try:
            gold, food = [int(i.get()) for i in self.labels]
        except ValueError:
            return
        gold, food = self.dec_to_hex_rev(gold), self.dec_to_hex_rev(food)
        end = self.opened_file.find(gold + food) - 12
        if end < 0:
            return messagebox.showerror("位置找尋失敗", "金錢或糧食數量錯誤！")
        inf_p = 0
        while True:
            inf_p += 1
            if inf_p > 1000:
                return messagebox.showerror("錯誤", "位置找尋失敗；先隨機獲取任何物品再嘗試")
            cur = self.opened_file[end - 24:end]
            left, right = cur[:12], cur[12:]
            if len(left.rstrip("0")) != 8 or len(right.rstrip("0")) > 6:
                end -= 24
                self.footer += [right, left]
                continue
            self.default += [right, left]
            item = self.mapping.get(left[4:8], {})
            value = (left[4:8], item.get("Desc", "???"), right[4:6], int(right[4:6], 16), item.get("Group", "???"))
            self.data.append(value)
            if self.opened_file[end - 84:end].startswith("ff010000"):
                self.header = self.opened_file[end - 36:end - 24]
                break
            end -= 24

        self.df = pd.DataFrame(self.data, columns=["iHex", "iDesc", "nHex", "n", "Group"])
        for i in self.df.itertuples():
            self.tree.insert("", 0, iid=i[0], values=i[1:], tags="T")

    def open_file(self):
        self.clear_all()
        s_dir = ""
        try:
            s_dir = f"{os.environ['USERPROFILE']}"+r"\AppData\LocalLow\UserJoy\SG8\Save"
            profile_no = os.listdir(s_dir)
            if profile_no:
                s_dir += f"\{profile_no[0]}"
        except:
            print ("Oh no")
        self.path = filedialog.askopenfilename(title=f"Select save file",
                                               filetypes=[("Save file", "*.bytes")],
                                               initialdir=s_dir)
        if self.path:
            with open(self.path, "rb") as f:
                self.opened_file = f.read().hex()
            for i in self.labels:
                i.config(state="normal")
            self.msg_var.set(f"已開啟存檔 {self.path.split('/')[-1]}")
        else:
            for i in self.labels:
                i.config(state="disabled")
            self.msg_var.set("請選擇存檔")


class AboutWin(tk.Toplevel):
    """
    Information and version history for the App.
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.config(highlightbackground="grey", highlightthickness=2)
        self.grab_set()
        self.overrideredirect(True)
        self.geometry("217x180+{}+{}".format(master.winfo_x() + 210, master.winfo_y()+200))
        self.iconbitmap("")
        window_label = tk.Label(self, text=" Program By PactOfShadows",
                                font="Calibri 10 bold", justify="left")
        window_label.grid(row=0, column=1, columnspan=2, sticky="w")
        modify_label = tk.Label(self, text=" pactofshadows@gmail.com", font=("Calibri", 8), justify="left")
        modify_label.grid(row=1, column=1, columnspan=2, sticky="w")
        tools_logo = tk.PhotoImage(file="tools.png")
        tools_label = tk.Label(self, image=tools_logo, compound="left", justify="left")
        tools_label.grid(row=0, column=0, rowspan=2)
        tools_label.img = tools_logo
        about_info = tkst.ScrolledText(self, wrap=tk.WORD, width=32, height=6)
        about_info.config(font=("Calibri", 8))
        about_info.grid(row=3, column=0, columnspan=4)
        general = ["Kind:", "Version:"]
        info = ["存檔修改器", "0.2"]
        for i, (text, detail) in enumerate(zip(general,info)):
            tk.Label(self, text=text, font=("Calibri", 8)).grid(row=4 + i, column=0, sticky="ne")
            tk.Label(self, text=detail, font=("Calibri", 8), justify="left").grid(row=4 + i, column=1,
                                                                                  sticky="ws", columnspan=4)
        about_info.insert("end",  "v0.2 - 2021/01/30\n"
                                  "- 允許新增物品\n"
                                  "- 修正傳說武器種類\n"
                                  "- 修正重覆開啟錯誤\n"
                                  "- 防止位置找尋錯誤時無限輪迴\n\n"
                                  "v0.1 - 2021/01/28\n"
                                  "- 初版\n"
                                  "- 以金錢/糧食搜尋物品位置\n"
                          )
        about_info.bind("<Key>", "break")
        self.resizable(False, False)
        self.transient(master)
        self.bind("<Button-1>", lambda e: self.destroy())


code = """禮物
 F1 0A 金錠（普通）  2801
 F2 0A 夜明珠（史詩）  2802
 F3 0A 珊瑚翡翠（傳說）  2803
 FB 0A 侍女 （普通） 2811
 FC 0A 憐人 （史詩） 2812
 FD 0A 清韻樂師 （傳說） 2813
 05 0B 功績碑 （普通） 2821
 06 0B 銘功盤 （史詩） 2822
 07 0B 合名玉蝶 （傳說） 2823
 0F 0B 奇殽異果 （普通） 2831
 10 0B 八珍玉食 （史詩） 2832
 11 0B 瓊漿玉液 （傳說） 2833
 19 0B 百花戰袍 （普通） 2841
 1A 0B 翠羽鞘 （史詩） 2842
 1B 0B 金羈玳瑁鞍 （傳說） 2843
 23 0B 西域奇香 （普通） 2851
 24 0B 花枝步搖 （史詩） 2852
 25 0B 七色琉璃珠 （傳說） 2853
 2D 0B 琴操 （普通） 2861
 2E 0B 帛畫 （史詩） 2862
 2F 0B 鎏金銅熏爐 （傳說） 2863
 37 0B 三國群英攻略 （傳說） 2871
 97 0F 煉體丹（普通） 3991 提升武將技能等級1-2
 98 0F 精元丹（精良） 3992 提升武將技能等級2-3
 99 0F 氣魄丹（史詩） 3993 提升武將技能等級3-4
 9A 0F 神髓丹（傳說） 3994 提升武將技能等級4-5
 遠攻法器
 B1 04 羽扇（基本）武力+4 智力+23  1201
 B2 04 清風扇（普通）武力+5 智力+26  1202
 B3 04 流雲扇（精良）武力+6 智力+33  1203
 B4 04 孔雀扇（史詩）武力+9 智力+46  1204
 B5 04 凰雀扇（史詩）武力+10 智力+52  1205
 遠射長弓
 E3 04 桑木弓（基本）武力+23 智力+4  1251
 E4 04 雕弓（普通）武力+26 智力+5  1252
 E5 04 穿雲裂石弓（史詩）武力+46 智力+9  1253
 E6 04 流星追月弓（史詩）武力+52 智力+10  1254
 E7 04 路弓（普通）武力+26 智力+5  1255
 E8 04 角端弓（精良）武力+33 智力+6  1256
 E9 04 長藤弓（基本）武力+19 智力+3  1257
 EA 04 短藤弓（基本）武力+23 智力+4  1258
 EB 04 虎筋藤弓（普通）武力+26 智力+5  1259
 14 05 毛竹弓（基本）武力+10 智力+3  1300
 單手兵器
 15 05 環首刀（普通）武力+12 智力+12  1301
 16 05 大夏龍雀（精良）武力+18 智力+18  1302
 17 05 百勝刀（普通）武力+10 智力+10  1303
 18 05 百辟刀（普通）武力+14 智力+14  1304
 19 05 九環刀（普通）武力+16 智力+16  1305
 1A 05 雪花鑌鐵刀（精良）武力+18 智力+18  1306
 1B 05 柳葉刀（精良）武力+21 智力+21  1307
 1C 05 吳鉤（精良）武力+21 智力+21  1308
 1D 05 短鐵斧 （基本）武力+10 智力+10  1309
 1E 05 蠻彎刀 （基本）武力+12 智力+12  1310
 78 05 劣鐵刀（基本）武力+5 智力+5  1400
 79 05 輕劍（基本）武力+12 智力+12  1401
 7A 05 鐵劍（基本）武力+12 智力+12  1402
 7B 05 含光（史詩）武力+25 智力+25  1403
 7C 05 承影（史詩）武力+25 智力+25  1404
 7D 05 宵練（史詩）武力+25 智力+25  1405
 7E 05 青霜（精良）武力+21 智力+21  1406
 7F 05 龍淵（史詩）武力+29 智力+29  1407
 80 05 神聖萬里伏 （精良）武力+18 智力+18  1408
 DD 05 龜紋鋼環（基本）武力+10 智力+10  1501
 DE 05 金剛圈（普通）武力+14 智力+14  1502
 0F 06 混鐵錘（基本）武力+10 智力+10  1551
 10 06 金瓜錘（普通）武力+14 智力+14  1552
 11 06 梅花亮銀錘（精良）武力+18 智力+18  1553
 12 06 青龍銅錘（史詩）武力+25 智力+25  1554
 長桿兵器
 41 06 車輪斧（基本）武力+15 智力+3  1601
 42 06 青紋石斧（普通）武力+21 智力+5  1602
 43 06 湛金斧（精良）武力+26 智力+6  1603
 44 06 開山大斧（史詩）武力+36 智力+9  1604
 45 06 宣花大斧（精良）武力+26 智力+6  1605
 46 06 鐵槳（基本）武力+15 智力+3  1606
 47 06 狼牙棒（基本）武力+18 智力+4  1607
 73 06 牛交叉（基本）武力+18 智力+4  1651
 74 06 混鐵點鋼叉（普通）武力+21 智力+5  1652
 75 06 齒翼月牙鏜（精良）武力+26 智力+6  1653
 76 06 雁尾鏜（史詩）武力+35 智力+9  1654
 A5 06 長鐵槍（基本）武力+15 智力+3  1701
 A6 06 鶴項槍（普通）武力+21 智力+5  1702
 A7 06 七星龍鱗槍（史詩）武力+36 智力+9  1703
 A8 06 紅纓槍（普通）武力+21 智力+5  1704
 A9 06 太寧筆槍（精良）武力+26 智力+6 1705
 09 07 槊矛（普通）武力+18 智力+4  1801
 0A 07 夫差矛（普通）武力+21 智力+5  1802
 0B 07 馬槊 （精良）武力+26 智力+6  1803
 0C 07 蟬紋矛 （史詩）武力+36 智力+9  1804
 6D 07 鳳嘴刀（基本）武力+15 智力+3 1901
 6E 07 屈刀（普通）武力+21 智力+5 1902
 6F 07 鉤鐮刀（普通）武力+23 智力+5 1903
 70 07 象鼻刀（普通）武力+23 智力+5 1904
 71 07 三尖兩刃刀（精良）武力+26 智力+6  1905
 D1 07 長戟（基本）武力+15 智力+3  2001
 D2 07 銀剪戟（基本）武力+18 智力+4  2002
 D3 07 月牙戟（普通）武力+21 智力+5  2003
 D4 07 畫桿描金戟（精良）武力+26 智力+6  2004
 D5 07 雷火震天戟（史詩）武力+36 智力+9  2005
 D6 07 天龍破城戟（史詩）武力+42 智力+10  2006
 雙手兵器
 FC 08 雙鐵刀（基本）武力+5 智力+5  2300
 35 08 雪花鑌鐵雙刀（精良）武力+18 智力+18  2101
 36 08 柳葉雙刀（精良）武力+21 智力+21  2102
 37 08 新月雙鉤（精良）武力+18 智力+18  2103
 38 08 鴛鴦劍（精良）武力+21 智力+21  2104
 39 08 毛貴二劍（精良）武力+21 智力+21  2105
 3A 08 龜紋鋼雙環（基本）武力+10 智力+10  2106
 3B 08 金剛雙圈（普通）武力+14 智力+14  2107
 3C 08 混沌雙錘（基本）武力+10 智力+10  2108
 3D 08 金瓜雙錘（普通）武力+14 智力+14  2109
 3E 08 寒梅雙銀錘（精良）武力+18 智力+18  2110
 3F 08 青龍雙龍錘（史詩）武力+25 智力+9  2111
 專屬武器代碼
 A1 04 虞姬 太阿劍 武力+36 智力+36 (單手)
 A2 04 神關羽 金龍偃月刀 武力+58 智力+15 (長桿)
 4D 04 大喬 月牙刺 武力+36 智力+36 (雙手)
 4E 04 小喬 蟬翼扇 武力+13 智力+66 (遠攻法器)
 4F 04 公孫瓚 棗陽槊 武力+52 智力+13 (長桿)
 50 04 太史慈 鵲畫弓 武力+52 智力+13 (遠射長弓)
 51 04 文醜 滅賊刀 武力+52 智力+13 (長桿)
 52 04 王元姬 麒麟弓 武力+52 智力+13 (遠射長弓)
 53 04 司馬懿 玄冥法扇 武力+13 智力+66 (遠攻法器)
 54 04 左慈 古黎杖 武力+13 智力+66 (遠攻法器)
 55 04 甘寧 中山刀 武力+36 智力+36 (單手)
 56 04 呂布 方天畫戟 武力+52 智力+13 (長桿)
 57 04 呂蒙 斷流劍 武力+36 智力+36 (單手)
 58 04 李典 虎賁方天戟 武力+52 智力+13 (長桿)
 59 04 典韋 雙鐵戟 武力+36 智力+36 (雙手)
 5A 04 周倉 鰲頭兩刃斧 武力+36 智力+36 (單手)
 5B 04 周泰 幼平刀 武力+36 智力+36 (單手)
 5C 04 周瑜 蕩寇將軍刀 武力+36 智力+36 (單手)
 5D 04 法正 更國劍 武力+36 智力+36 (單手)
 5E 04 姜維 綠沈槍 武力+52 智力+13 (長桿)
 5F 04 淩統 寶赤刀 武力+36 智力+36 (雙手)
 60 04 夏侯惇 絳纓槍 武力+52 智力+13 (長桿)
 61 04 夏侯淵 定光劍 武力+36 智力+36 (單手)
 62 04 孫尚香 白陽刀 武力+36 智力+36 (單手)
 63 04 孫堅 古錠刀 武力+36 智力+36 (單手)
 64 04 孫策 狻猊嘯日槍 武力+52 智力+13 (長桿)
 65 04 孫權 白虹劍 武力+36 智力+36 (單手)
 66 04 徐晃 貫石斧 武力+52 智力+13 (長桿)
 67 04 徐庶 赤霄劍 武力+36 智力+36 (單手)
 68 04 荀彧 鵬羽扇 武力+13 智力+66 (遠攻法器)
 69 04 袁紹 思召劍 武力+36 智力+36 (單手)
 6A 04 袁術 陽瞿劍 武力+36 智力+36 (雙手)
 6B 04 馬良 鶴羽扇 武力+13 智力+66 (遠攻法器)
 6C 04 馬岱 馬岱寶刀 武力+36 智力+36 (單手)
 6D 04 馬超 飛翼槍 武力+52 智力+13 (長桿)
 6E 04 馬騰 虎頭湛金槍 武力+52 智力+13 (長桿)
 6F 04 張角 太平法杖 武力+13 智力+66 (遠攻法器)
 70 04 張郃 斷魂槍 武力+52 智力+13 (長桿)
 71 04 張飛 丈八蛇矛 武力+52 智力+13 (長桿)
 72 04 張遼 破山劍 武力+36 智力+36 (單手)
 73 04 曹仁 含章刀 武力+36 智力+36 (單手) 
 74 04 曹丕 飛景劍 武力+36 智力+36 (單手) 
 75 04 曹操 七星寶劍 武力+36 智力+36 (單手) 
 76 04 許褚 火雲劍 武力+36 智力+36 (單手) 
 77 04 郭嘉 清翎扇 武力+13 智力+66 (遠攻法器)
 78 04 陳宮 方土劍 武力+36 智力+36 (單手) 
 79 04 陸遜 火精劍 武力+36 智力+36 (單手) 
 7A 04 程普 鐵脊蛇矛 武力+52 智力+13 (長桿)
 7B 04 華佗 刮骨刀 武力+13 智力+66 (遠攻法器)
 7C 04 貂蟬 流華刀 武力+36 智力+36 (雙手)
 7D 04 黃月英 宛景矛 武力+52 智力+13 (長桿)
 7E 04 黃忠 百剛弓 武力+52 智力+13 (遠射長弓)
 7F 04 黃蓋 斷海鞭 武力+36 智力+36 (單手)
 80 04 董卓 巨闕劍 武力+36 智力+36 (單手)
 81 04 賈詡 湛盧劍 武力+36 智力+36 (單手)
 82 04 甄宓 魚腸劍 武力+13 智力+66 (遠攻法器)
 83 04 趙雲 涯角槍 武力+52 智力+13 (長桿)
 84 04 劉備 鴛鴦雙股劍 武力+36 智力+36 (雙手)
 85 04 諸葛亮 神機羽扇 武力+13 智力+66 (遠攻法器)
 86 04 鐘會 太常劍 武力+36 智力+36 (單手)
 87 04 魏延 三環大刀 武力+36 智力+36 (雙手)
 88 04 龐統 勝邪杖 武力+36 智力+36 (單手) 
 89 04 龐德 虎賁大刀 武力+52 智力+13 (長桿)
 8A 04 關平 定國刀 武力+36 智力+36 (單手)
 8B 04 關羽 青龍偃月刀 武力+52 智力+13 (長桿)
 8C 04 關鳳 回鳳槍 武力+52 智力+13 (長桿)
 8D 04 孟獲 松紋雙斧 武力+36 智力+36 (雙手)
 8E 04 祝融夫人 綠藤彎弓 武力+52 智力+13 (遠射長弓)
 傳說武器
 99 08 UJ多賴把（傳說）武力+13 智力+88  2201
 9A 08 UJ玩具弓（傳說）武力+80 智力+26  2202
 9B 08 UJ玩具錘（傳說）武力+52 智力+52  2203
 9C 08 UJ大雞腿（傳說）武力+44 智力+44  2204
 9D 08 UJ長掃帚（傳說）武力+88 智力+13  2205
 特殊武器
 00 04 夫諸_坐騎等級需求99
 01 04 犀渠_武器等級需求99
 02 04 犀渠_坐騎等級需求99
 03 04 巨木樹妖_武器等級需求99
 04 04 巨木樹妖_坐騎等級需求99
 05 04 魍魎石鬼_武器等級需求99
 06 04 魍魎石鬼_坐騎等級需求99
 07 04 ？？？武器（精良）等級需求99
 08 04 ？？？坐騎（精良）等級需求99
 09 04 ？？？武器（精良）等級需求99
 0A 04 ？？？坐騎（精良）等級需求99
 坐騎：
 FD 08 黃鬃馬（基本）體力+750 速度+10  2301
 FE 08 黑鬃馬（普通）體力+1000 速度+10.2  2302
 FF 08 雲鬃馬（普通）體力+1125 速度+10.5  2303
 00 09 青駹馬（精良）體力+1250 速度+10.8  2304
 01 09 滇馬（史詩）體力+1750 速度+11  2305
 02 09 烏孫馬 （史詩）體力+1750 速度+11  2306
 03 09 汗血馬（史詩）體力+2000 速度+11.2  2307
 04 09 鐵騎馬（史詩）體力+2000 速度+11.5  2308
 05 09 重甲戰馬 （史詩）體力+2000 速度+11.5  2309
 06 09 玄驪 （傳說）體力+2250 速度+12  2310
 07 09 絕影 （傳說）體力+2250 速度+12  2311
 09 09 豹月烏（傳說）體力+2250 速度+12  2313
 0A 09 爪黃飛電 （傳說）體力+2250 速度+13  2314
 0B 09 的盧 （傳說）體力+2250 速度+13  2315
 0C 09 赤兔 （傳說）體力+2500 速度+14  2316
 61 09 鱗甲青狼（普通） 武力+3 體力+1000 速度+9  2401 
 62 09 鐵甲戰狼（精良） 武力+5 體力+1250 速度+9.5  2402 
 63 09 嗜血狻狼（精良） 武力+7 體力+1750 速度+10  2403 
 93 09 鱗甲赤豹（普通） 武力+3 體力+1000 速度+10  2451 
 94 09 鋼甲黑豹（史詩） 武力+6 體力+1750 速度+10.5  2452 
 95 09 蠻虎（普通） 武力+4 體力+1000 速度+9  2453 
 96 09 藤甲蠻虎（精良） 武力+6 體力+1250 速度+9.5  2454 
 97 09 鋼甲戰虎（史詩） 武力+7 體力+1750 速度+10  2455 
 98 09 鋼甲猛虎（史詩） 武力+8 體力+2000 速度+10.5  2456 
 C5 09 梅花鹿（普通）智力+3 體力+1000 速度+9.5  2501
 C6 09 角鹿（精良）智力+5 體力+1250 速度+10.5  2502
 C7 09 白鹿（史詩）智力+6 體力+1750 速度+11  2503
 C8 09 麟鹿（史詩）智力+7 體力+2000 速度+12  2504
 其他
 B9 0B 營寨（一）（基本）營寨類  3001
 BA 0B 營寨（二）（基本）營寨類  3002
 BB 0B 營寨（三）（普通）營寨類  3003
 BC 0B 營寨（四）（普通）營寨類  3004
 BD 0B 營寨（五）（精良）營寨類  3005
 BE 0B 拒馬槍（一）（基本）拒馬類  3006
 BF 0B 拒馬槍（二）（基本）拒馬類  3007
 C0 0B 拒馬槍（三）（基本）拒馬類  3008
 C1 0B 拒馬槍（四）（基本）拒馬類  3009
 C2 0B 拒馬槍（五）（精良）拒馬類  3010
 C3 0B 箭塔（一）（基本）箭塔類  3011
 C4 0B 箭塔（二）（基本）箭塔類  3012
 C5 0B 箭塔（三）（普通）箭塔類  3013
 C6 0B 箭塔（四）（普通）箭塔類  3014
 C7 0B 箭塔（五）（精良）箭塔類  3015
 C8 0B 大門加固（一）（基本）城門防具  3016
 C9 0B 大門加固（二）（基本）城門防具  3017
 CA 0B 大門加固（三）（普通）城門防具  3018
 CB 0B 大門加固（四）（普通）城門防具  3019
 CC 0B 大門加固（五）（精良）城門防具  3020
 CD 0B 台座加固（一）（基本）角台防具  3021
 CE 0B 台座加固（二）（基本）角台防具  3022
 CF 0B 台座加固（三）（普通）角台防具  3023
 D0 0B 台座加固（四）（普通）角台防具  3024
 D1 0B 台座加固（五）（精良）角台防具  3025
 D2 0B 墻面加固（一）（基本）守備弓手  3026
 D3 0B 墻面加固（二）（基本）守備弓手  3027
 D4 0B 墻面加固（三）（普通）守備弓手  3028
 D5 0B 墻面加固（四）（普通）守備弓手  3029
 D6 0B 墻面加固（五）（精良）守備弓手  3030
 D7 0B 油鍋（一）（基本）城門防具  3031
 D8 0B 油鍋（二）（基本）城門防具  3032
 D9 0B 油鍋（三）（普通）城門防具  3033
 DA 0B 油鍋（四）（普通）城門防具  3034
 DB 0B 油鍋（五）（精良）城門防具  3035
 DC 0B 夜叉擂（一）（基本）城門防具  3036
 DD 0B 夜叉擂（二）（基本）城門防具  3037
 DE 0B 夜叉擂（三）（普通）城門防具  3038
 DF 0B 夜叉擂（四）（普通）城門防具  3039
 E0 0B 夜叉擂（五）（精良）城門防具  3040
 E1 0B 巨弩炮（一）（基本）角台防具  3041
 E2 0B 巨弩炮（二）（基本）角台防具  3042
 E3 0B 巨弩炮（三）（普通）角台防具  3043
 E4 0B 巨弩炮（四）（普通）角台防具  3044
 E5 0B 巨弩炮（五）（精良）角台防具  3045
 E6 0B 投石機（一）（基本）角台防具  3046
 E7 0B 投石機（二）（基本）角台防具  3047
 E8 0B 投石機（三）（普通）角台防具  3048
 E9 0B 投石機（四）（普通）角台防具  3049
 EA 0B 投石機（五）（精良）角台防具  3050
 EB 0B 守墻弓兵（一）（基本）守備弓手  3051
 EC 0B 守墻弓兵（二）（基本）守備弓手  3052
 ED 0B 守墻弓兵（三）（普通）守備弓手  3053
 EE 0B 守墻弓兵（四）（普通）守備弓手  3054
 EF 0B 守墻弓兵（五）（精良）守備弓手  3055
 材料
 30 23 周易占卜案例 (史詩)  9008
 31 0C 石灰石（普通） 3121
 32 0C 神獸血（傳說） 3122
 33 0C 甜象草（普通） 3123
 34 0C 黑麥草（精良） 3124
 35 0C 紫花苜蓿（史詩） 3125
 36 0C 玄鐵（傳說） 3126
 37 0C 鳳凰梧桐（傳說） 3127
 38 0C 家畜（普通） 3128
 39 0C 野獸血食（精良） 3129
 3A 0C 獸王血食（史詩） 3130
 DB 0C 豹月烏飼育書（傳說） 3291
 DC 0C 爪黃飛電飼育書（傳說） 3292
 DD 0C 的盧飼育書（傳說） 3293
 DE 0C 赤兔飼育書（傳說） 3294
 DF 0C 嗜血狻狼飼育書（史詩） 3295
 E0 0C 鋼甲黑豹飼育書（史詩） 3296
 E1 0C 鐵甲戰虎飼育書（史詩） 3297
 E2 0C 鋼甲猛虎飼育書（史詩） 3298
 E3 0C 白鹿飼育書（史詩） 3299
 E4 0C 麟鹿飼育書（史詩） 3300
 E5 0C UJ工具卡（傳說） 3301
 E6 0C UJ體屈卡（傳說） 3302
 E7 0C UJ棒槌卡（傳說） 3303
 E8 0C UJ神腿卡（傳說） 3304
 E9 0C UJ好人卡（傳說） 3305
 飾品：
 F7 09 尉繚子（基本） 2551
 F8 09 六韜（普通） 2552
 F9 09 黃石三略（精良） 2553
 FA 09 吳子（史詩） 2554
 FB 09 孫子兵法（傳說） 2555
 01 0A 平安鎖片（基本） 2561
 02 0A 內甲（普通） 2562 
 03 0A 護心鏡（精良） 2563 
 04 0A 玄鐵珠（史詩） 2564 
 05 0A 金身符（傳說） 2565 
 0B 0A 太極幡（基本） 2571
 0C 0A 辟邪幡（基本） 2572
 0D 0A 驅魔幡（精良） 2573
 0E 0A 五行幡（史詩） 2574
 0F 0A 八卦幡（傳說） 2575
 15 0A 引火旗（基本） 2581 獲得:灼火（一）
 16 0A 火齊指環（普通） 2582 獲得:灼火（二）
 17 0A 朱雀羽（精良） 2583 獲得:灼火（三）
 18 0A 禦火令（史詩） 2584 獲得:灼火（四）
 19 0A 火靈珠（傳說） 2585 獲得:灼火（五） 
 1F 0A 紫雷針（基本） 2591 獲得:纏雷（一） 
 20 0A 醞雷玉塔（普通） 2592 獲得:纏雷（二） 
 21 0A 吞雷吐電壺（精良） 2593 獲得:纏雷（三）
 22 0A 禦雷令（史詩） 2594 獲得:纏雷（四）
 23 0A 雷光珠（史詩） 2595 獲得:纏雷（五）
 29 0A 淒風鈴（基本） 2601 獲得:霜甲（一）
 2A 0A 冷冽金冠（普通） 2602 獲得:霜甲（二）
 2B 0A 傲雪淩霜靴（精良） 2603 獲得:霜甲（三）
 2C 0A 禦寒令（史詩） 2604 獲得:霜甲（四）
 2D 0A 寒冰珠（傳說） 2605 獲得:霜甲（五）
 47 0A 清風蓑（基本） 2631
 48 0A 流雲紗帶（普通） 2632
 49 0A 九尾狐裘（精良） 2633
 4A 0A 八卦仙衣（史詩） 2634
 4B 0A 遁甲天書（傳說） 2634
 51 0A 避身符（基本） 2641
 52 0A 八面玲瓏鏡（普通） 2642
 53 0A 三頭六臂丹（精良） 2643
 54 0A 五行周天盾（史詩） 2644
 55 0A 琉璃金光罩（傳說） 2645
 5B 0A 鷹視珠（基本） 2651 
 5C 0A 大運符（普通） 2652 
 5D 0A 鬼人心法（精良） 2653
 5E 0A 七殺星盤（史詩） 2654
 5F 0A 白虎牙（傳說） 2655
 65 0A 庖丁解牛書（基本） 2661
 66 0A 痛擊符（普通） 2662
 67 0A 奪命符（精良） 2663
 68 0A 追魂令（史詩） 2664
 69 0A 暴血石（史詩） 2665 
 6F 0A 六丁神甲（基本） 2671 
 70 0A 天蠶寶甲（普通） 2672 
 71 0A 紫綬仙衣（精良） 2673 
 72 0A 混元幡（史詩） 2674 
 73 0A 玄武甲（傳說） 2675 
 技能書代碼
 11 0E 赤焰
 12 0E 赤焰燃
 13 0E 赤焰火障
 14 0E 冰柱刺
 15 0E 冰柱嵯峨
 16 0E 冰柱群峰
 17 0E 突石
 18 0E 突石棘刺
 19 0E 突石劍山
 1A 0E 集火柱
 1B 0E 強火柱
 1C 0E 強襲地火
 1D 0E 雷擊
 1E 0E 雷擊閃
 1F 0E 雷光焦獄
 20 0E 半月斬
 21 0E 半月輪斬
 22 0E 半月狂斬
 23 0E 水浪襲
 24 0E 水浪沖擊
 25 0E 水浪怒濤
 26 0E 火牛陣
 27 0E 火牛群舞
 28 0E 火牛烈崩
 29 0E 芭蕉扇
 2A 0E 蕉扇狂風
 2B 0E 蕉扇颶風
 2C 0E 劍輪斬
 2D 0E 劍輪舞華
 2E 0E 流沙術
 2F 0E 流沙縛陣
 30 0E 流沙封禁
 31 0E 地巖刺
 32 0E 地刺巖障
 33 0E 地刺疊嶂
 34 0E 神鳶
 35 0E 神鳶彈
 36 0E 神鳶空襲
 37 0E 暴旋風
 38 0E 龍卷沖擊
 39 0E 龍卷颶風
 3A 0E 龍卷亂舞
 3B 0E 太極陣
 3C 0E 混天太極陣
 3D 0E 八卦太極陣
 3E 0E 旋燈火
 3F 0E 旋燈熾焰
 40 0E 旋燈烈发
 41 0E 生死門
 42 0E 生死獄
 43 0E 生死滅道
 44 0E 蓮花焰
 45 0E 蓮花爆炎
 46 0E 蓮花焚天
 47 0E 心劍
 48 0E 心劍雨落
 49 0E 心劍奔流
 4A 0E 屍鬼召喚
 4B 0E 屍鬼群起
 4C 0E 屍鬼大陣
 4D 0E 巨木樹妖
 4E 0E 樹妖聚沖
 4F 0E 樹妖大陣
 50 0E 魍魎石鬼
 51 0E 石鬼眾襲
 52 0E 石鬼大陣
 53 0E 鬼域
 54 0E 鬼域之殤
 55 0E 鬼域大陣
 56 0E 回天
 57 0E 回天返血
 58 0E 回春貫元
 59 0E 回春陣
 5A 0E 回春療血
 5B 0E 回春活元
 5C 0E 凝氣盾
 5D 0E 剛氣盾
 5E 0E 坤元氣盾
 5F 0E 挪移術
 60 0E 挪移大陣
 61 0E 挪移遁甲
 62 0E 邪刃
 63 0E 邪靈刃
 64 0E 邪靈妖刃
 65 0E 化氣術
 66 0E 滅氣術
 67 0E 移氣術
 68 0E 地龍
 69 0E 地龍震
 6A 0E 地龍極震
 6B 0E 破城錐
 6C 0E 破城大鉞
 6D 0E 破城神錘
 6E 0E 飛刃擊
 6F 0E 百刃裂空
 70 0E 千刃星落
 71 0E 迷魂術
 72 0E 迷心大法
 73 0E 迷蜃幻境
 74 0E 五星延命
 75 0E 七星續命
 76 0E 九星化劫
 77 0E 煙燎毒氣
 78 0E 血輪斬（基本）  3705
 79 0E 千煞毒雲（精良）  3705
 7A 0E 血輪斬（基本）  3706
 7B 0E 四血輪斬（普通）  3707
 7C 0E 八血輪斬（精良）  3708
 7D 0E 青龍狂雷（傳說）  3709
 7E 0E 玄武怒流（傳說）  3710
 7F 0E 白虎傲嘯（傳說）  3711
 80 0E 朱雀焚天（傳說）  3712 
 81 0E 麒麟滅世（傳說）  3713 
 82 0E 罡刃墜擊
 83 0E 罡刃崩殺
 84 0E 罡刃烈轟
 85 0E 躍天擊
 86 0E 貫天破
 87 0E 翔龍天爆
 88 0E 迅風沖
 89 0E 疾風突斬
 8A 0E 烈風奔襲
 8B 0E 奔雷
 8C 0E 烈風
 8D 0E 混沌法珠
 8E 0E 靈彈
 8F 0E 爆炎
 90 0E 七星閃
 91 0E 一擊
 92 0E 天地一閃
 93 0E 風車
 94 0E 牙突
 95 0E 二連閃
 96 0E 飛輪
 97 0E 怒風
 98 0E 地裂
 99 0E 狂雷
 9A 0E 連刺
 9B 0E 二連斬
 9C 0E 重斬
 9D 0E 亂舞
 9E 0E 嗜血
 9F 0E 鬼煞
 A0 0E 狂斬
 A1 0E 爆裂箭
 A2 0E 火箭
 A3 0E 暴風
 A4 0E 電光
 A5 0E 霜雪
 A6 0E 側斬
 A7 0E 二連斬
 A8 0E 蘇生
 A9 0E 斬鐵
 AA 0E 烈風
 AB 0E 雷電
 AC 0E 雙血輪
 AD 0E 裂地
 AE 0E 冰霜
 AF 0E 怒雷
 B0 0E 騰火
 B1 0E 巖棘
 B2 0E 翻浪
 B3 0E 弧月
 B4 0E 落雷
 B5 0E 爆彈
 B6 0E 召喚虎豹騎
 B7 0E 召喚飛熊軍
 B8 0E 召喚白毦兵
 B9 0E 召喚無當飛軍
 BA 0E 召喚解煩兵
 BB 0E 召喚西涼鐵騎
 BC 0E 召喚先登死士
 BD 0E 召喚丹陽兵
 BE 0E 召喚黃巾兵"""


root = GUI()
root.mainloop()
