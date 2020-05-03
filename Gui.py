from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
from tkinter import ttk
from tkinter.scrolledtext import *
import subprocess
import sys
import asyncio
import signal
import re
import time

def setEntry(self, newval):
    old_state = self['state']
    self.configure(state='normal')
    self.delete(0, END)
    self.insert(0, newval)
    self.configure(state=old_state)

Entry.set = setEntry

class Logger:
    def __init__(self, _cbprintfunc, _cbdeclaretagsfunc, _debugging = False):
        self.init_t = time.time()
        self.debugging = _debugging
        self.cbprintfunc = _cbprintfunc
        self.cbdeclaretagsfunc = _cbdeclaretagsfunc
        self.declare_tags()

    def elapsed_t(self):
        now_t = time.time()
        return int(now_t - self.init_t)

    def declare_tags(self):
        self.cbdeclaretagsfunc('msg', foreground='#468cff')
        self.cbdeclaretagsfunc('err', foreground='#ff2828')
        self.cbdeclaretagsfunc('wrn', foreground='#ffe646')
        self.cbdeclaretagsfunc('scs', foreground='#46ff8c')
        self.cbdeclaretagsfunc('inf', foreground='#bebebe')
        self.cbdeclaretagsfunc('otr', foreground='#fa5fff')
        self.cbdeclaretagsfunc('dbg', foreground='#98d3ce')
    
    def msg(self, content: str):
        self.cbprintfunc('[{:>5}s] {}'.format(self.elapsed_t(), content), 'msg')

    def msg_err(self, content: str):
        self.cbprintfunc('[{:>5}s] {}'.format(self.elapsed_t(), content), 'err')

    def msg_wrn(self, content: str):
        self.cbprintfunc('[{:>5}s] {}'.format(self.elapsed_t(), content), 'wrn')

    def msg_scs(self, content: str):
        self.cbprintfunc('[{:>5}s] {}'.format(self.elapsed_t(), content), 'scs')

    def msg_inf(self, content: str):
        self.cbprintfunc('[{:>5}s] {}'.format(self.elapsed_t(), content), 'inf')

    def msg_otr(self, content: str):
        self.cbprintfunc('[{:>5}s] {}'.format(self.elapsed_t(), content), 'otr')

    def msg_dbg(self, content: str):
        if self.debugging:
            self.cbprintfunc('[{:>5}s] {}'.format(self.elapsed_t(), content), 'dbg')

def background(f):
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, *kwargs)

    return wrapped

class a_instance_modal:
    def __init__(self, parent, retval):
        self.retval = retval
        self.top = Toplevel(parent)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.title('Add Instance')
        Label(self.top, text='Instance Name').grid(column=0, row=0, columnspan=4, padx=5, pady=5)
        self.entry = Entry(self.top)
        self.entry.bind('<Return>', self.retok)
        self.entry.bind('<Escape>', self.retcancel)
        self.entry.grid(column=0, row=1, columnspan=4, sticky=E+W, padx=40, pady=5)
        self.entry.focus_set()
        self.top.geometry('300x100')
        self.top.resizable(False, False)
        self.top.columnconfigure(0, weight=1)
        self.top.protocol('WM_DELETE_WINDOW', self.close_mod)
        self.top.update_idletasks()
        self.top.geometry('300x100+{}+{}'.format(int(parent.winfo_rootx() + parent.winfo_width() / 2 - 150), int(parent.winfo_rooty() + parent.winfo_height() / 2 - 100)))
        Button(self.top, text='OK', command=self.retok).grid(column=2, row=2, padx=5, pady=5)
        Button(self.top, text='Cancel', command=self.retcancel).grid(column = 3, row=2, padx=(5, 10), pady=5)
        self.top.deiconify()

    def retok(self, event=None):
        if not self.entry.get():
            messagebox.showerror('Error', 'Please enter a valid name')
        else:
            self.retval.set(self.entry.get())
            self.top.destroy()

    def retcancel(self, event=None):
        self.top.destroy()

    def close_mod(self):
        self.top.destroy()
        

class Application(Tk):
    def __init__(self, title, geometry, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self.title(title)
        self.geometry(geometry)
        self.init_menubar()
        self.init_notebook()

    def init_menubar(self):
        self.menu = Menu(self)
        #self.menu.add_command(label='Settings', command=self.settings_onclick)
        #self.menu.add_command(label='Profiles', command=self.profiles_onclick)
        #self.menu.add_command(label='Updates', command=self.updates_onclick)
        self.menu.add_command(label='Add Instance', command=self.a_instance_onclick)
        self.menu.add_command(label='Delete Instance', command=self.d_instance_onclick)
        self.config(menu=self.menu)

    def init_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=1, fill='both', padx=5, pady=5)
        newpage = instancepage('Instance', False, self.notebook)
        self.add_notebookpage(newpage)
        newpage.Logger.msg_scs('Initializing {} complete.'.format(newpage.name))

    def add_notebookpage(self, page):
        self.notebook.add(page, text=page.name)

    def settings_onclick(self):
        messagebox.showinfo('Settings', 'Clicked')

    def profiles_onclick(self):
        messagebox.showinfo('Profile', 'Clicked')

    def updates_onclick(self):
        messagebox.showinfo('Updates', 'Clicked')

    def a_instance_onclick(self):
        pagename = StringVar(self)
        a_modal = a_instance_modal(self, pagename)
        self.wait_window(a_modal.top)
        if pagename.get():
            newpage = instancepage(pagename.get(), False, self.notebook)
            self.add_notebookpage(newpage)
            newpage.Logger.msg_scs('Initializing {} complete.'.format(newpage.name))

    def d_instance_onclick(self):
        if messagebox.askokcancel('Delete Instance', 'Delete selected instance?'):
            selectedtab_name = self.notebook.select()
            if selectedtab_name:
                page_object = self.notebook.nametowidget(selectedtab_name)
                page_object.self_destruct()

class instancepage(ttk.Frame):
    def __init__(self, _name, _debugging, *args, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)
        self.rightpanel = rightpanel(_name, _debugging, self)
        self.Logger = self.rightpanel.Logger
        self.leftpanel = leftpanel(_name, _debugging, self)
        self.name = _name
        self.debugging = _debugging
        self.leftpanel.grid(column=0, row=0, sticky=N+W+S+E, padx=5, pady=5)
        self.rightpanel.grid(column=1, row=0, sticky=N+S+E+W, padx=5, pady=5)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.update_state = self.rightpanel.update_state

    def savelog(self):
        with open('guilogs.log', 'w') as f:
            buffer = self.rightpanel.console.get('1.0', 'end-1c')
            f.write(buffer)

    def self_destruct(self):
        if self.leftpanel.running:
            self.leftpanel.send_interrupt()
        self.destroy()


class rightpanel(ttk.Frame):
    def __init__(self, _name, _debugging, *args, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)
        self.console = ScrolledText(self, bg='#101010', fg='#ffffff', font=('Consolas', 10), selectbackground='#5e5e5e', insertbackground='#101010')
        self.state_lbl = Label(self, text='State: ')
        self.state = Label(self, text='Idle')
        self.state_lbl.grid(column=0, row=0, sticky=W)
        self.state.grid(column=1, row=0, sticky=W)
        self.console.grid(column=0, row=1, sticky=N+S+E+W, columnspan=3)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        self.Logger = Logger(self.print_console, self.declare_console_tag, _debugging)
        self.console.bind('<Key>', lambda e: None if (e.state == 12 and e.keysym == 'c') else 'break')

    def print_console(self, content, tagname):
        self.console.insert(END, content + '\n', tagname)

    def declare_console_tag(self, tagname, *args, **kwargs):
        self.console.tag_config(tagname, *args, **kwargs)

    def update_state(self, newstate):
        self.state.configure(text=newstate)

class leftpanel(ttk.Frame):
    def __init__(self, _name, _debugging, *args, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)
        self.name = _name
        self.debugging = _debugging
        self.running = False
        self.paused = False
        self.vnumonly = (self.register(self.validate_only_digits), '%P')
        self.init_adb_form()
        self.init_server_form()
        self.init_combat_form()
        self.init_retire_form()
        self.init_headquarters_form()
        self.init_enhancement_form()
        self.init_research_form()
        self.init_events_form()
        self.init_module_form()
        self.init_control_buttons()
        self.uniform_column()
        self.Logger = self.master.Logger
        try:
            self.apply_config(self.decode_config('generated.ini'))
        except FileNotFoundError:
            self.apply_config(self.decode_config('config.ini'))

    def uniform_column(self):
        self.columnconfigure(2, weight=1)

    def validate_only_digits(self, new_value):
        return new_value.isdigit()

    def init_adb_form(self):
        self.adb_lbl = Label(self, text='ADB')
        self.adb_input = Entry(self, width=30)
        self.adb_lbl.grid(column=0, row=0, sticky=W, padx=5)
        self.adb_input.grid(column=1, row=0, ipady=1, columnspan=3,sticky=E+W, padx=5)

    def init_server_form(self):
        self.server_lbl = Label(self, text='Server')
        self.server_input = ttk.Combobox(self, values=['EN', 'JP'], state='readonly', width=5)
        self.server_input.current(0)
        self.server_lbl.grid(column=4, row=0, padx=5)
        self.server_input.grid(column=5, row=0, ipady=1)

    def init_combat_form(self):
        self.combat_enabled = BooleanVar(self)
        self.combat_input = Checkbutton(self, text='Combat', var=self.combat_enabled, command=self.combat_onchange)
        self.combat_input.grid(column=0, row=1, sticky=W, padx=5, columnspan=2)
        self.init_combat_section()

    def init_combat_section(self):
        self.combat_section = ttk.Labelframe(self, text='Combat')
        self.combat_map_lbl = Label(self.combat_section, text='Map')
        self.combat_map_input = ttk.Combobox(self.combat_section, 
            values=[
                '1', '2', '3', '4', '5', 
                '6', '7', '8', '9', '10',
                '11', '12', '13', 'E-A', 
                'E-B', 'E-C', 'E-D', 'E-SP'],
            state='readonly',
            width=4
            )
        self.combat_node_input = ttk.Combobox(self.combat_section,
            values=['1', '2', '3', '4'],
            state='readonly',
            width=4
        )
        self.combat_map_input.current(0)
        self.combat_node_input.current(0)
        self.combat_kills_before_boss_lbl = Label(self.combat_section, text='Kills Before Boss')
        self.combat_kills_before_boss = Entry(self.combat_section, width=7, validate='key', validatecommand=self.vnumonly)
        self.combat_boss_fleet = BooleanVar(self.combat_section)
        self.combat_reversed_fleet = BooleanVar(self.combat_section)
        self.combat_boss_fleet_input = Checkbutton(self.combat_section, text='Boss Fleet', var=self.combat_boss_fleet)
        self.combat_reversed_fleet_input = Checkbutton(self.combat_section, text='Reverse Fleet', var=self.combat_reversed_fleet)
        self.combat_oil_limit_lbl = Label(self.combat_section, text='Oil Limit')
        self.combat_oil_limit = Entry(self.combat_section, width=7, validate='key', validatecommand=self.vnumonly)
        self.combat_retreat_after_lbl = Label(self.combat_section, text='Retreat After')
        self.combat_retreat_after = Entry(self.combat_section, width=7, validate='key', validatecommand=self.vnumonly)
        self.combat_mysteries = BooleanVar(self.combat_section)
        self.combat_mysteries_input = Checkbutton(self.combat_section, text='Mystery Nodes', var=self.combat_mysteries)
        self.combat_hide_sub_range = BooleanVar(self.combat_section)
        self.combat_hide_sub_range_input = Checkbutton(self.combat_section, text='Hide Sub Range', var=self.combat_hide_sub_range)
        self.combat_small_boss = BooleanVar(self.combat_section)
        self.combat_small_boss_input = Checkbutton(self.combat_section, text='Small Boss', var=self.combat_small_boss)
        self.combat_clearing_mode = BooleanVar(self.combat_section)
        self.combat_clearing_mode_input = Checkbutton(self.combat_section, text='Clearing Mode', var=self.combat_clearing_mode)
        self.combat_siren_elite = BooleanVar(self.combat_section)
        self.combat_siren_elite_input = Checkbutton(self.combat_section, text='Siren Elites', var=self.combat_siren_elite)
        self.combat_ignore_morale = BooleanVar(self.combat_section)
        self.combat_ignore_morale_input = Checkbutton(self.combat_section, text='Ignore Morale', var=self.combat_ignore_morale)
        self.combat_low_mood_sleep_time_lbl = Label(self.combat_section, text='Low Mood Sleep Time')
        self.combat_low_mood_sleep_time = Entry(self.combat_section, width=7, validate='key', validatecommand=self.vnumonly)
        self.combat_searchmode_lbl = Label(self.combat_section, text='Search Mode')
        self.combat_searchmode = ttk.Combobox(self.combat_section, values=['0: Normal', '1: Intersect'], state='readonly', width=7)
        self.combat_searchmode.current(0)

        # Grid Packing
        self.combat_map_lbl.grid(column=0, row=0, sticky=E, pady=(5,0))
        self.combat_map_input.grid(column=1, row=0, sticky=E, pady=(5, 0))
        self.combat_node_input.grid(column=2, row=0, pady=(5,0))
        self.combat_boss_fleet_input.grid(column=3, row=0, sticky=W, padx=5, pady=(5, 0))
        self.combat_reversed_fleet_input.grid(column=3, row=1, sticky=W, padx=5)
        self.combat_oil_limit_lbl.grid(column=0, row=1, columnspan=2, sticky=E, padx=5, pady=5)
        self.combat_oil_limit.grid(column=2, row=1)
        self.combat_retreat_after_lbl.grid(column=0, row=2, columnspan=2, sticky=E, padx=5)
        self.combat_retreat_after.grid(column=2, row=2)
        self.combat_kills_before_boss_lbl.grid(column=0, row=3, sticky=E, padx=5, pady=5, columnspan=2)
        self.combat_kills_before_boss.grid(column=2, row=3)
        self.combat_mysteries_input.grid(column=3, row=2, sticky=W, padx=5)
        self.combat_hide_sub_range_input.grid(column=3, row=3, sticky=W, padx=5)
        self.combat_small_boss_input.grid(column=4, row=0, sticky=W, padx=5, pady=(5,0))
        self.combat_clearing_mode_input.grid(column=4, row=1, sticky=W, padx=5)
        self.combat_siren_elite_input.grid(column=4, row=2, sticky=W, padx=5)
        self.combat_ignore_morale_input.grid(column=4, row=3, sticky=W, padx=5)
        self.combat_low_mood_sleep_time_lbl.grid(column=0, row=4, columnspan=2, sticky=E, padx=5, pady=(0,5))
        self.combat_low_mood_sleep_time.grid(column=2, row=4)
        self.combat_searchmode_lbl.grid(column=3, row=4)
        self.combat_searchmode.grid(column=4, row=4, sticky=E+W)

        # Main Grid Packing
        self.combat_section.grid(column=2, row=1, columnspan=4, sticky=N+S+E+W, pady=5)
        self.combat_section.columnconfigure(4, weight=1)
        disableChildren(self.combat_section)

    def init_retire_form(self):
        self.retire_enabled = BooleanVar(self)
        self.retire_input = Checkbutton(self, text='Retirement', var=self.retire_enabled, command=self.retire_onchange)
        self.retire_input.grid(column=0, row=2, sticky=W, padx=5, columnspan=2)
        self.init_retire_section()

    def init_retire_section(self):
        self.retire_section = ttk.Labelframe(self, text='Retirement')
        self.retire_common = BooleanVar(self.retire_section)
        self.retire_rare = BooleanVar(self.retire_section)
        self.retire_common_input = Checkbutton(self.retire_section, text='Common', var=self.retire_common)
        self.retire_rare_input = Checkbutton(self.retire_section, text='Rare', var=self.retire_rare)
        self.retire_interval_lbl = Label(self.retire_section, text='Cycle')
        self.retire_interval = Entry(self.retire_section, width=5, validate='key', validatecommand=self.vnumonly)
        self.retire_common_input.grid(column=0, row=0, padx=5, pady=5)
        self.retire_rare_input.grid(column=1, row=0, padx=5)
        self.retire_interval_lbl.grid(column=2, row=0, padx=5)
        self.retire_interval.grid(column=3, row=0, padx=5)
        self.retire_section.grid(column=2, row=2, columnspan=4, sticky=N+S+E+W, pady=5)
        disableChildren(self.retire_section)

    def init_headquarters_form(self):
        self.headquarters_enabled = BooleanVar(self)
        self.headquarters_input = Checkbutton(self, text='Headquarters', var=self.headquarters_enabled, command=self.headquarters_onchange)
        self.headquarters_input.grid(column=0, row=3, sticky=W, padx=5, columnspan=2)
        self.init_headquarters_section()

    def init_headquarters_section(self):
        self.headquarters_section = ttk.Labelframe(self, text='Headquarters')
        self.headquarters_dorm_enabled = BooleanVar(self.headquarters_section)
        self.headquarters_dorm_enabled_input = Checkbutton(self.headquarters_section, text='Dorm', var=self.headquarters_dorm_enabled)
        self.headquarters_academy_enabled = BooleanVar(self.headquarters_section)
        self.headquarters_academy_enabled_input = Checkbutton(self.headquarters_section, text='Academy', var=self.headquarters_academy_enabled)
        self.headquarters_skillbook_lbl = Label(self.headquarters_section, text='Skillbooks')
        self.headquarters_skillbook_input = ttk.Combobox(self.headquarters_section, values=['T1','T2','T3'], state='readonly')
        self.headquarters_skillbook_input.current(0)

        self.headquarters_dorm_enabled_input.grid(column=0, row=0, padx=5, pady=5)
        self.headquarters_academy_enabled_input.grid(column=1, row=0, padx=5, pady=5)
        self.headquarters_skillbook_lbl.grid(column=2, row=0, padx=5, pady=5)
        self.headquarters_skillbook_input.grid(column=3, row=0, padx=5, pady=5)
        self.headquarters_section.grid(column=2, row=3, columnspan=4, sticky=N+S+E+W, pady=5)
        disableChildren(self.headquarters_section)

    def init_enhancement_form(self):
        self.enhancement_enabled = BooleanVar(self)
        self.enhancement_input = Checkbutton(self, text='Enhancement', var=self.enhancement_enabled, command=self.enhancement_onchange)
        self.enhancement_input.grid(column=0, row=4, sticky=W, padx=5, columnspan=2)
        self.init_enhancement_section()

    def init_enhancement_section(self):
        self.enhancement_section = ttk.Labelframe(self, text='Enhancement')
        self.enhancement_single = BooleanVar(self.enhancement_section)
        self.enhancement_single_input = Checkbutton(self.enhancement_section, text='Single Enhance', var=self.enhancement_single)
        self.enhancement_single_input.grid(column=0, row=0, padx=5, pady=5)
        self.enhancement_section.grid(column=2, row=4, columnspan=4, sticky=N+S+E+W, pady=5)
        disableChildren(self.enhancement_section)

    def init_research_form(self):
        self.research_enabled = BooleanVar(self)
        self.research_input = Checkbutton(self, text='Research', var=self.research_enabled, command=self.research_onchange)
        self.research_input.grid(column=0, row=5, sticky=W, padx=5, columnspan=2)
        self.init_research_section()

    def init_research_section(self):
        self.research_section = ttk.Labelframe(self, text='Research Filters')
        self.research_free_project = BooleanVar(self.research_section)
        self.research_use_coins = BooleanVar(self.research_section)
        self.research_use_cubes = BooleanVar(self.research_section)
        self.research_no_requirements = BooleanVar(self.research_section)
        self.research_have_blueprint = BooleanVar(self.research_section)
        self.research_30m = BooleanVar(self.research_section)
        self.research_1h = BooleanVar(self.research_section)
        self.research_1h30m = BooleanVar(self.research_section)
        self.research_2h = BooleanVar(self.research_section)
        self.research_2h30m = BooleanVar(self.research_section)
        self.research_4h = BooleanVar(self.research_section)
        self.research_5h = BooleanVar(self.research_section)
        self.research_6h = BooleanVar(self.research_section)
        self.research_8h = BooleanVar(self.research_section)
        self.research_12h = BooleanVar(self.research_section)

        self.research_free_project_input = Checkbutton(self.research_section, var=self.research_free_project, text='Free')
        self.research_use_coins_input = Checkbutton(self.research_section, var=self.research_use_coins, text='Use Coins')
        self.research_use_cubes_input = Checkbutton(self.research_section, var=self.research_use_cubes, text='Use Cubes')
        self.research_no_requirements_input = Checkbutton(self.research_section, var=self.research_no_requirements, text='No requirements')
        self.research_have_blueprint_input = Checkbutton(self.research_section, var=self.research_have_blueprint, text='Reward BPs')
        self.research_30m_input = Checkbutton(self.research_section, var=self.research_30m, text='30m')
        self.research_1h_input = Checkbutton(self.research_section, var=self.research_1h, text='1h')
        self.research_1h30m_input = Checkbutton(self.research_section, var=self.research_1h30m, text='1h30m')
        self.research_2h_input = Checkbutton(self.research_section, var=self.research_2h, text='2h')
        self.research_2h30m_input = Checkbutton(self.research_section, var=self.research_2h30m, text='2h30m')
        self.research_4h_input = Checkbutton(self.research_section, var=self.research_4h, text='4h')
        self.research_5h_input = Checkbutton(self.research_section, var=self.research_5h, text='5h')
        self.research_6h_input = Checkbutton(self.research_section, var=self.research_6h, text='6h')
        self.research_8h_input = Checkbutton(self.research_section, var=self.research_8h, text='8h')
        self.research_12h_input = Checkbutton(self.research_section, var=self.research_12h, text='12h')

        self.research_free_project_input.grid(column=0, row=0, sticky=W, padx=5)
        self.research_use_coins_input.grid(column=1, row=0, sticky=W, padx=5)
        self.research_use_cubes_input.grid(column=2, row=0, sticky=W, padx=5)
        self.research_no_requirements_input.grid(column=3, row=0, sticky=W, padx=5)
        self.research_have_blueprint_input.grid(column=0, row=1, sticky=W, padx=5)
        self.research_30m_input.grid(column=1, row=1, sticky=W, padx=5)
        self.research_1h_input.grid(column=2, row=1, sticky=W, padx=5)
        self.research_1h30m_input.grid(column=3, row=1, sticky=W, padx=5)
        self.research_2h_input.grid(column=0, row=2, sticky=W, padx=5)
        self.research_2h30m_input.grid(column=1, row=2, sticky=W, padx=5)
        self.research_4h_input.grid(column=2, row=2, sticky=W, padx=5)
        self.research_5h_input.grid(column=3, row=2, sticky=W, padx=5)
        self.research_6h_input.grid(column=0, row=3, sticky=W, padx=5)
        self.research_8h_input.grid(column=1, row=3, sticky=W, padx=5)
        self.research_12h_input.grid(column=2, row=3, sticky=W, padx=5)

        self.research_section.grid(column=2, row=5, columnspan=4, sticky=N+S+E+W, pady=5)
        disableChildren(self.research_section)

    def init_events_form(self):
        self.events_enabled = BooleanVar(self)
        self.events_input = Checkbutton(self, text='Events', var=self.events_enabled, command=self.events_onchange)
        self.events_input.grid(column=0, row=6, columnspan=2, padx=5, sticky=W)
        self.init_events_section()

    def init_events_section(self):
        self.events_section = ttk.Labelframe(self, text='Events')
        self.events_level_E = BooleanVar(self.events_section)
        self.events_level_N = BooleanVar(self.events_section)
        self.events_level_H = BooleanVar(self.events_section)
        self.events_level_EX = BooleanVar(self.events_section)
        self.events_ignore_rateup = BooleanVar(self.events_section)

        self.events_selected_lbl = Label(self.events_section, text='Event')
        self.events_selected = ttk.Combobox(self.events_section, values=['Royal Maids'], state='readonly')
        self.events_selected.current(0)
        self.events_level_E_input = Checkbutton(self.events_section, var=self.events_level_E, text='E')
        self.events_level_N_input = Checkbutton(self.events_section, var=self.events_level_N, text='N')
        self.events_level_H_input = Checkbutton(self.events_section, var=self.events_level_H, text='H')
        self.events_level_EX_input = Checkbutton(self.events_section, var=self.events_level_EX, text='EX')
        self.events_ignore_rateup_input = Checkbutton(self.events_section, var=self.events_ignore_rateup, text='Ignore Rateup')

        self.events_selected_lbl.grid(column=0, row=0, padx=5)
        self.events_selected.grid(column=1, row=0, padx=5)
        self.events_ignore_rateup_input.grid(column=0, row=1, columnspan=2, padx=5, sticky=W)
        self.events_level_E_input.grid(column=2, row=0, padx=5, sticky=W)
        self.events_level_N_input.grid(column=3, row=0, padx=5, sticky=W)
        self.events_level_H_input.grid(column=2, row=1, padx=5, sticky=W)
        self.events_level_EX_input.grid(column=3, row=1, padx=5, sticky=W)
        
        self.events_section.grid(column=2, row=6, columnspan=4, sticky=N+S+E+W, pady=5)
        disableChildren(self.events_section)

    def init_module_form(self):
        self.module_section = ttk.Labelframe(self, text='Modules')
        self.commissions_enabled = BooleanVar(self.module_section)
        self.missions_enabled = BooleanVar(self.module_section)
        self.ascreencap_enabled = BooleanVar(self.module_section)
        self.logger_debugging = BooleanVar(self.module_section)
        self.commissions_enabled_input = Checkbutton(self.module_section, text='Commissions', var=self.commissions_enabled)
        self.missions_enabled_input = Checkbutton(self.module_section, text='Missions', var=self.missions_enabled)
        self.ascreencap_enabled_input = Checkbutton(self.module_section, text='AScreenCap', var=self.ascreencap_enabled)
        self.logger_debugging_input = Checkbutton(self.module_section, text='Debugging', var=self.logger_debugging, command=self.logger_ondebugchange)
        self.commissions_enabled_input.grid(column=0, row=0, padx=5)
        self.missions_enabled_input.grid(column=1, row=0, padx=5)
        self.ascreencap_enabled_input.grid(column=2, row=0, padx=5)
        self.logger_debugging_input.grid(column=3, row=0, padx=5)
        self.module_section.grid(column=0, row=7, columnspan=6, sticky=N+S+E+W, pady=5)

    def init_control_buttons(self):
        self.controls = ttk.Frame(self)
        self.control_run = Button(self.controls, text='Run', command=self.control_onrun)
        self.control_savelog = Button(self.controls, text='Save logs', command=self.master.savelog)
        self.control_sendINT = Button(self.controls, text='Interrupt', command=self.send_interrupt, state='disable')
        self.control_run.grid(column=0, row=0, padx=5)
        self.control_sendINT.grid(column=1, row=0, padx=5)
        self.control_savelog.grid(column=2, row=0, padx=5)
        self.controls.grid(column=0, row=10, columnspan=6, sticky=N+S+E+W, pady=5)

    def control_onrun(self):
        if not self.running:
            self.running = True
            self.master.update_state('Active')
            self.encode_config()
            self.prettify_config()
            self.write_config()
            self.exec_script()
            self.listen_script()
            self.control_run.configure(state='disable')
            self.control_sendINT.configure(state='normal')

    def send_interrupt(self):
        if self.running:
            self.running = False
            self.master.update_state('Idle')
            try:
                self.process.send_signal(signal.SIGINT)
            except:
                self.process.send_signal(signal.CTRL_C_EVENT)
            self.control_run.configure(state='normal')
            self.control_sendINT.configure(state='disable')

    def decode_stdout_tag(self, bytesline):
        if bytesline[:5] == b'\x1b[94m':
            return 'msg'
        elif bytesline[:5] == b'\x1b[92m':
            return 'scs'
        elif bytesline[:5] == b'\x1b[93m':
            return 'wrn'
        elif bytesline[:5] == b'\x1b[91m':
            return 'err'
        elif bytesline[:5] == b'\x1b[35m':
            return 'inf'
        elif bytesline[:5] == b'\x1b[97m':
            return 'dbg'
        else:
            return 'otr'

    def sanitize_stdout(self, bytesline):
        if bytesline[len(bytesline) - 2:] == b'\r\n':
            bytesline = bytesline[:len(bytesline) - 2]
        if bytesline[len(bytesline) - 4:] == b'\x1b[0m':
            bytesline = bytesline[:len(bytesline) - 4]
        if bytesline[0] == 27:
            decoded = bytesline[5:].decode('utf-8').strip()
        else:
            decoded = bytesline.decode('utf-8').strip()
        decoded = re.sub(r'\[\d{4}(-\d{2}){2} \d{2}(:\d{2}){2}\]', '', decoded).strip()
        return decoded

    def exec_script(self):
        """https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running"""
        command = [sys.executable.replace('pythonw.exe', 'python.exe'), '-u' ,'ALAuto.py', '--debug', '--config', 'generated.ini']
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    @background
    def listen_script(self):
        while True:
            line = self.process.stdout.readline()
            if not line: break
            tag = self.decode_stdout_tag(line)
            if tag == 'msg':
                self.Logger.msg(self.sanitize_stdout(line))
            elif tag == 'scs':
                self.Logger.msg_scs(self.sanitize_stdout(line))
            elif tag == 'wrn':
                self.Logger.msg_wrn(self.sanitize_stdout(line))
            elif tag == 'err':
                self.Logger.msg_err(self.sanitize_stdout(line))
            elif tag == 'inf':
                self.Logger.msg_inf(self.sanitize_stdout(line))
            elif tag == 'dbg':
                self.Logger.msg_dbg(self.sanitize_stdout(line))
            else:
                self.Logger.msg_otr(self.sanitize_stdout(line))

        output = self.process.communicate()[0]
        exitCode = self.process.returncode

        if (exitCode == 0):
            return output

    def combat_onchange(self):
        setChildren(self.combat_section, self.combat_enabled.get())

    def retire_onchange(self):
        setChildren(self.retire_section, self.retire_enabled.get())

    def headquarters_onchange(self):
        setChildren(self.headquarters_section, self.headquarters_enabled.get())

    def enhancement_onchange(self):
        setChildren(self.enhancement_section, self.enhancement_enabled.get())

    def research_onchange(self):
        setChildren(self.research_section, self.research_enabled.get())

    def events_onchange(self):
        setChildren(self.events_section, self.events_enabled.get())

    def logger_ondebugchange(self):
        self.debugging = self.Logger.debugging = self.logger_debugging.get()

    def parse_map(self):
        try:
            int(self.combat_map_input.get())
            return '{}-{}'.format(self.combat_map_input.get(), self.combat_node_input.get())
        except:
            return self.combat_map_input.get() + self.combat_node_input.get()

    def parse_event_levels(self):
        level = []
        if self.events_level_E.get():
            level.append('E')
        if self.events_level_N.get():
            level.append('N')
        if self.events_level_H.get():
            level.append('H')
        if self.events_level_EX.get():
            level.append('EX')
        return ', '.join(level)

    def encode_config(self):
        self.raw_config = {
            '[Network]': {
                'Service': self.adb_input.get()
            },
            '[Screenshot]': {
                'UseAScreenCap': self.ascreencap_enabled.get()
            },
            '[Updates]': {
                'Enabled': True,
                'Channel': 'Development'
            },
            '[Assets]': {
                'Server': self.server_input.get()
            },
            '[Combat]': {
                'Enabled': self.combat_enabled.get(),
                'Map': self.parse_map(),
                'KillsBeforeBoss': self.combat_kills_before_boss.get(),
                'BossFleet': self.combat_boss_fleet.get(),
                'OilLimit': self.combat_oil_limit.get(),
                'RetireCycle': self.retire_interval.get(),
                'RetreatAfter': self.combat_retreat_after.get(),
                'IgnoreMysteryNodes': True if not self.combat_mysteries.get() else False,
                'FocusOnMysteryNodes': True if self.combat_mysteries.get() else False,
                'ClearingMode': self.combat_clearing_mode.get(),
                'HideSubsHuntingRange': self.combat_hide_sub_range.get(),
                'SmallBossIcon': self.combat_small_boss.get(),
                'SirenElites': self.combat_siren_elite.get(),
                'IgnoreMorale': self.combat_ignore_morale.get(),
                'LowMoodSleepTime': self.combat_low_mood_sleep_time.get(),
                'SearchMode': self.combat_searchmode.get()[0]
            },
            '[Headquarters]': {
                'Dorm': self.headquarters_dorm_enabled.get() if self.headquarters_enabled.get() else False,
                'Academy': self.headquarters_academy_enabled.get() if self.headquarters_enabled.get() else False,
                'SkillBookTier': self.headquarters_skillbook_input.get().replace('T', '')
            },
            '[Modules]': {
                'Commissions': self.commissions_enabled.get(),
                'Missions': self.missions_enabled.get(),
            },
            '[Enhancement]': {
                'Enabled': self.enhancement_enabled.get(),
                'SingleEnhancement':self.enhancement_single.get()
            },
            '[Retirement]': {
                'Enabled': self.retire_enabled.get(),
                'Rares': self.retire_rare.get(),
                'Commons': self.retire_common.get(),
            },
            '[Research]': {
                'Enabled': self.research_enabled.get(),
                'AllowFreeProjects': self.research_free_project.get(),
                'AllowConsumingCoins': self.research_use_coins.get(),
                'AllowConsumingCubes': self.research_use_cubes.get(),
                'WithoutRequirements': self.research_no_requirements.get(),
                'AwardMustContainPRBlueprint': self.research_have_blueprint.get(),
                '30Minutes': self.research_30m.get(),
                '1Hour': self.research_1h.get(),
                '1Hour30Minutes': self.research_1h30m.get(),
                '2Hours': self.research_2h.get(),
                '2Hours30Minutes': self.research_2h30m.get(),
                '4Hours': self.research_4h.get(),
                '5Hours': self.research_5h.get(),
                '6Hours': self.research_6h.get(),
                '8Hours': self.research_8h.get(),
                '12Hours': self.research_12h.get()
            },
            '[Events]': {
                'Enabled': self.events_enabled.get(),
                'Event': self.events_selected.get().replace(' ', '_'),
                'Levels': self.parse_event_levels(),
                'IgnoreRateUp': self.events_ignore_rateup.get()
            },
            '[GUI]': {
                'Debugging': self.debugging
            }
        }
    
    def decode_config(self, configfile):
        decoded = {}
        section = ''
        with open(configfile, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line == '': continue
                if re.search(r'\[.*\]', line):
                    section = line
                    decoded[section] = {}
                else:
                    decoded[section][line[:line.index(':')]] = line[line.index(':') + 1:].strip()
        return decoded

    def apply_map(self, map):
        node = map[len(map) - 1:]
        world = map[:len(map) - 1]
        if world[len(world) - 1] == '-':
            world = world[:len(world) - 1]
        self.combat_map_input.set(world)
        self.combat_node_input.set(node)

    def apply_eventlevel(self, eventlevel):
        eventlevel = eventlevel.split(',')
        eventlevel = [x.strip() for x in eventlevel]
        while eventlevel:
            if eventlevel[0] == 'E':
                self.events_level_E.set(True)
            if eventlevel[0] == 'N':
                self.events_level_N.set(True)
            if eventlevel[0] == 'H':
                self.events_level_H.set(True)
            if eventlevel[0] == 'EX':
                self.events_level_EX.set(True)
            eventlevel.pop(0)

    def apply_config(self, config_dict):
        self.adb_input.set(config_dict['[Network]']['Service'])
        self.ascreencap_enabled.set(eval(config_dict['[Screenshot]']['UseAScreenCap']))
        self.server_input.set(config_dict['[Assets]']['Server'])
        self.combat_enabled.set(config_dict['[Combat]']['Enabled'])
        self.apply_map(config_dict['[Combat]']['Map'])
        self.combat_kills_before_boss.set(config_dict['[Combat]']['KillsBeforeBoss'])
        self.combat_boss_fleet.set(eval(config_dict['[Combat]']['BossFleet']))
        self.combat_oil_limit.set(config_dict['[Combat]']['OilLimit'])
        self.retire_interval.set(config_dict['[Combat]']['RetireCycle'])
        self.combat_retreat_after.set(config_dict['[Combat]']['RetreatAfter'])
        self.combat_mysteries.set(eval(config_dict['[Combat]']['FocusOnMysteryNodes']))
        self.combat_clearing_mode.set(eval(config_dict['[Combat]']['ClearingMode']))
        self.combat_hide_sub_range.set(eval(config_dict['[Combat]']['HideSubsHuntingRange']))
        self.combat_small_boss.set(eval(config_dict['[Combat]']['SmallBossIcon']))
        self.combat_siren_elite.set(eval(config_dict['[Combat]']['SirenElites']))
        self.combat_ignore_morale.set(eval(config_dict['[Combat]']['IgnoreMorale']))
        self.combat_low_mood_sleep_time.set(config_dict['[Combat]']['LowMoodSleepTime'])
        self.combat_searchmode.current(eval(config_dict['[Combat]']['SearchMode']))
        self.headquarters_enabled.set(True)
        self.headquarters_dorm_enabled.set(eval(config_dict['[Headquarters]']['Dorm']))
        self.headquarters_academy_enabled.set(eval(config_dict['[Headquarters]']['Academy']))
        self.headquarters_skillbook_input.set('T' + config_dict['[Headquarters]']['SkillBookTier'])
        self.commissions_enabled.set(eval(config_dict['[Modules]']['Commissions']))
        self.missions_enabled.set(eval(config_dict['[Modules]']['Missions']))
        self.enhancement_enabled.set(eval(config_dict['[Enhancement]']['Enabled']))
        self.enhancement_single.set(eval(config_dict['[Enhancement]']['SingleEnhancement']))
        self.retire_enabled.set(eval(config_dict['[Retirement]']['Enabled']))
        self.retire_rare.set(eval(config_dict['[Retirement]']['Rares']))
        self.retire_common.set(eval(config_dict['[Retirement]']['Commons']))
        self.research_enabled.set(eval(config_dict['[Research]']['Enabled']))
        self.research_free_project.set(eval(config_dict['[Research]']['AllowFreeProjects']))
        self.research_use_coins.set(eval(config_dict['[Research]']['AllowConsumingCoins']))
        self.research_use_cubes.set(eval(config_dict['[Research]']['AllowConsumingCubes']))
        self.research_no_requirements.set(eval(config_dict['[Research]']['WithoutRequirements']))
        self.research_have_blueprint.set(eval(config_dict['[Research]']['AwardMustContainPRBlueprint']))
        self.research_30m.set(eval(config_dict['[Research]']['30Minutes']))
        self.research_1h.set(eval(config_dict['[Research]']['1Hour']))
        self.research_1h30m.set(eval(config_dict['[Research]']['1Hour30Minutes']))
        self.research_2h.set(eval(config_dict['[Research]']['2Hours']))
        self.research_2h30m.set(eval(config_dict['[Research]']['2Hours30Minutes']))
        self.research_4h.set(eval(config_dict['[Research]']['4Hours']))
        self.research_5h.set(eval(config_dict['[Research]']['5Hours']))
        self.research_6h.set(eval(config_dict['[Research]']['6Hours']))
        self.research_8h.set(eval(config_dict['[Research]']['8Hours']))
        self.research_12h.set(eval(config_dict['[Research]']['12Hours']))
        self.events_enabled.set(eval(config_dict['[Events]']['Enabled']))
        self.events_selected.set(config_dict['[Events]']['Event'].replace('_', ' '))
        self.apply_eventlevel(config_dict['[Events]']['Levels'])
        self.events_ignore_rateup.set(eval(config_dict['[Events]']['IgnoreRateUp']))
        self.logger_debugging.set(eval(config_dict['[GUI]']['Debugging']))
        self.combat_onchange()
        self.enhancement_onchange()
        self.events_onchange()
        self.headquarters_onchange()
        self.research_onchange()
        self.retire_onchange()
        self.logger_ondebugchange()

    def prettify_config(self):
        self.pretty_config = []
        for section, options in self.raw_config.items():
            self.pretty_config.append(section)
            for option, value in options.items():
                self.pretty_config.append('{}: {}'.format(option, value))
            self.pretty_config.append('')

    def write_config(self):
        with open('generated.ini', 'w') as f:
            for line in self.pretty_config:
                f.write(line + '\n')
            


"""
    Generic function to disable childrens of parent
    Source: https://stackoverflow.com/questions/24942760/is-there-a-way-to-gray-out-disable-a-tkinter-frame
"""
def disableChildren(parent):
    for child in parent.winfo_children():
        wtype = child.winfo_class()
        if wtype not in ('Frame','Labelframe'):
            child.configure(state='disable')
        else:
            disableChildren(child)

def enableChildren(parent):
    for child in parent.winfo_children():
        wtype = child.winfo_class()
        if wtype not in ('Frame','Labelframe'):
            child.configure(state='normal')
        else:
            enableChildren(child)

def setChildren(parent, val):
    for child in parent.winfo_children():
        wtype = child.winfo_class()
        if wtype not in ('Frame','Labelframe'):
            child.configure(state=('normal' if val and wtype != 'TCombobox' else ('readonly' if wtype == 'TCombobox' and val else 'disable')))
        else:
            enableChildren(child)

def ignore_interrupt(signum, frame):
    pass

def main():
    signal.signal(signal.SIGINT, ignore_interrupt)
    app = Application('AL GUI', '900x700')
    app.mainloop()

if __name__ == '__main__':
    main()