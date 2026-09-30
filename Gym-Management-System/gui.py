import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

from gym_system import Gym


class GymApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gym Management System")
        self.geometry("1100x700")
        self.minsize(950, 600)
        self.gym = Gym()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build_style()
        self._build_layout()
        self.show_dashboard()

    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Card.TLabel", font=("Segoe UI", 15, "bold"), padding=18)
        style.configure("Treeview", rowheight=28)

    def _build_layout(self):
        self.sidebar = ttk.Frame(self, padding=12)
        self.sidebar.pack(side="left", fill="y")
        self.content = ttk.Frame(self, padding=20)
        self.content.pack(side="right", fill="both", expand=True)

        ttk.Label(self.sidebar, text="GYM\nMANAGER", font=("Segoe UI", 18, "bold"), justify="center").pack(pady=(5, 25))
        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Members", self.show_members),
            ("Trainers", self.show_trainers),
            ("Memberships", self.show_memberships),
            ("Payments", self.show_payments),
            ("Attendance", self.show_attendance),
        ]
        for text, command in buttons:
            ttk.Button(self.sidebar, text=text, command=command, width=20).pack(pady=4)
        ttk.Separator(self.sidebar).pack(fill="x", pady=18)
        ttk.Button(self.sidebar, text="Save Data", command=self.save_now, width=20).pack(pady=4)

    def clear(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def heading(self, text):
        ttk.Label(self.content, text=text, style="Title.TLabel").pack(anchor="w", pady=(0, 18))

    def show_dashboard(self):
        self.clear()
        self.heading("Dashboard")
        data = self.gym.dashboard()
        grid = ttk.Frame(self.content)
        grid.pack(fill="x")
        cards = [
            ("Total Members", data["total_members"]),
            ("Total Trainers", data["total_trainers"]),
            ("Active Memberships", data["active_memberships"]),
            ("Expired Memberships", data["expired_memberships"]),
            ("Today's Attendance", data["today_attendance"]),
            ("Total Payments", f"{data['total_payments']:.2f}"),
        ]
        for i, (label, value) in enumerate(cards):
            frame = ttk.LabelFrame(grid, text=label, padding=10)
            frame.grid(row=i // 3, column=i % 3, sticky="nsew", padx=8, pady=8)
            ttk.Label(frame, text=str(value), style="Card.TLabel").pack()
        for c in range(3):
            grid.columnconfigure(c, weight=1)

        ttk.Label(self.content, text="Business rules implemented:").pack(anchor="w", pady=(25, 5))
        rules = [
            "• Attendance requires an active membership.",
            "• A member cannot have two active memberships.",
            "• Payment amounts must be greater than zero.",
            "• IDs must refer to existing members/trainers where required.",
        ]
        for rule in rules:
            ttk.Label(self.content, text=rule).pack(anchor="w", pady=2)

    def _tree(self, columns, headings):
        tree = ttk.Treeview(self.content, columns=columns, show="headings")
        for col, head in zip(columns, headings):
            tree.heading(col, text=head)
            tree.column(col, width=130, anchor="center")
        tree.pack(fill="both", expand=True, pady=12)
        return tree

    def show_members(self):
        self.clear(); self.heading("Members")
        top = ttk.Frame(self.content); top.pack(fill="x")
        search_var = tk.StringVar()
        ttk.Label(top, text="Search:").pack(side="left")
        ttk.Entry(top, textvariable=search_var, width=30).pack(side="left", padx=8)
        tree = self._tree(("id", "name", "phone", "age", "trainer"), ("ID", "Name", "Phone", "Age", "Trainer ID"))

        def refresh(*_):
            tree.delete(*tree.get_children())
            rows = self.gym.search_members(search_var.get()) if search_var.get().strip() else self.gym.members
            for m in rows:
                tree.insert("", "end", values=(m.person_id, m.name, m.phone, m.age, m.trainer_id or "-"))
        ttk.Button(top, text="Add Member", command=lambda: self.member_form(refresh)).pack(side="right")
        ttk.Button(top, text="Update Selected", command=lambda: self.update_selected_member(tree, refresh)).pack(side="right", padx=5)
        ttk.Button(top, text="Assign Trainer", command=lambda: self.assign_trainer_form(tree, refresh)).pack(side="right", padx=5)
        ttk.Button(top, text="Delete Selected", command=lambda: self.delete_selected_member(tree, refresh)).pack(side="right", padx=5)
        search_var.trace_add("write", refresh); refresh()

    def member_form(self, refresh):
        win = tk.Toplevel(self); win.title("Add Member"); win.geometry("350x280"); win.grab_set()
        fields = {}
        for i, label in enumerate(("Name", "Phone", "Age")):
            ttk.Label(win, text=label).grid(row=i, column=0, padx=12, pady=10, sticky="w")
            entry = ttk.Entry(win, width=28); entry.grid(row=i, column=1, padx=12, pady=10); fields[label] = entry
        def save():
            try:
                self.gym.add_member(fields["Name"].get(), fields["Phone"].get(), int(fields["Age"].get()))
                self.gym.save_data(); win.destroy(); refresh(); messagebox.showinfo("Success", "Member added successfully.")
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("Error", str(exc))
        ttk.Button(win, text="Save", command=save).grid(row=3, column=1, pady=15)

    def update_selected_member(self, tree, refresh):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Select a member first."); return
        values = tree.item(selected[0])["values"]
        member_id = int(values[0])
        win = tk.Toplevel(self); win.title("Update Member"); win.geometry("350x300"); win.grab_set()
        fields = {}
        for i, (label, value) in enumerate((("Name", values[1]), ("Phone", values[2]), ("Age", values[3]))):
            ttk.Label(win, text=label).grid(row=i, column=0, padx=12, pady=10, sticky="w")
            e = ttk.Entry(win, width=28); e.insert(0, value); e.grid(row=i, column=1, padx=12, pady=10); fields[label] = e
        def save():
            try:
                self.gym.update_member(member_id, fields["Name"].get(), fields["Phone"].get(), int(fields["Age"].get()))
                self.gym.save_data(); win.destroy(); refresh(); messagebox.showinfo("Success", "Member updated successfully.")
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("Error", str(exc))
        ttk.Button(win, text="Save", command=save).grid(row=3, column=1, pady=15)

    def assign_trainer_form(self, tree, refresh):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Select a member first."); return
        member_id = int(tree.item(selected[0])["values"][0])
        if not self.gym.trainers:
            messagebox.showwarning("No trainers", "Add a trainer first."); return
        win = tk.Toplevel(self); win.title("Assign Trainer"); win.geometry("360x220"); win.grab_set()
        ttk.Label(win, text="Trainer ID").grid(row=0, column=0, padx=12, pady=15)
        entry = ttk.Entry(win, width=25); entry.grid(row=0, column=1, padx=12, pady=15)
        ttk.Label(win, text="Available: " + ", ".join(str(t.person_id) for t in self.gym.trainers)).grid(row=1, column=0, columnspan=2, pady=5)
        def save():
            try:
                self.gym.assign_trainer(member_id, int(entry.get()))
                self.gym.save_data(); win.destroy(); refresh(); messagebox.showinfo("Success", "Trainer assigned.")
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("Error", str(exc))
        ttk.Button(win, text="Assign", command=save).grid(row=2, column=1, pady=15)

    def delete_selected_member(self, tree, refresh):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Select a member first."); return
        member_id = int(tree.item(selected[0])["values"][0])
        try:
            self.gym.delete_member(member_id); self.gym.save_data(); refresh()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Error", str(exc))

    def show_trainers(self):
        self.clear(); self.heading("Trainers")
        ttk.Button(self.content, text="Add Trainer", command=self.trainer_form).pack(anchor="e")
        tree = self._tree(("id", "name", "phone", "specialization"), ("ID", "Name", "Phone", "Specialization"))
        for t in self.gym.trainers:
            tree.insert("", "end", values=(t.person_id, t.name, t.phone, t.specialization))

    def trainer_form(self):
        win = tk.Toplevel(self); win.title("Add Trainer"); win.geometry("380x300"); win.grab_set()
        fields = {}
        for i, label in enumerate(("Name", "Phone", "Specialization")):
            ttk.Label(win, text=label).grid(row=i, column=0, padx=12, pady=10, sticky="w")
            entry = ttk.Entry(win, width=28); entry.grid(row=i, column=1, padx=12, pady=10); fields[label] = entry
        def save():
            try:
                self.gym.add_trainer(fields["Name"].get(), fields["Phone"].get(), fields["Specialization"].get())
                self.gym.save_data(); win.destroy(); self.show_trainers(); messagebox.showinfo("Success", "Trainer added successfully.")
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("Error", str(exc))
        ttk.Button(win, text="Save", command=save).grid(row=3, column=1, pady=15)

    def show_memberships(self):
        self.clear(); self.heading("Memberships")
        top = ttk.Frame(self.content); top.pack(fill="x")
        status = tk.StringVar(value="All")
        ttk.Label(top, text="Filter:").pack(side="left")
        combo = ttk.Combobox(top, textvariable=status, values=("All", "Active", "Expired", "Upcoming"), state="readonly", width=14)
        combo.pack(side="left", padx=8)
        ttk.Button(top, text="Create Membership", command=self.membership_form).pack(side="right")
        tree = self._tree(("id", "member", "start", "end", "price", "status"), ("ID", "Member", "Start", "End", "Price", "Status"))
        def refresh(*_):
            tree.delete(*tree.get_children())
            for m in self.gym.filter_memberships(status.get()):
                tree.insert("", "end", values=(m.membership_id, m.member_id, m.start_date, m.end_date, f"{m.price:.2f}", m.status))
        combo.bind("<<ComboboxSelected>>", refresh); refresh()

    def membership_form(self):
        win = tk.Toplevel(self); win.title("Create Membership"); win.geometry("420x360"); win.grab_set()
        labels = ("Member ID", "Start Date", "End Date", "Price")
        entries = {}
        defaults = ("", date.today().isoformat(), (date.today() + timedelta(days=30)).isoformat(), "500")
        for i, (label, default) in enumerate(zip(labels, defaults)):
            ttk.Label(win, text=label).grid(row=i, column=0, padx=12, pady=10, sticky="w")
            e = ttk.Entry(win, width=28); e.insert(0, default); e.grid(row=i, column=1, padx=12, pady=10); entries[label] = e
        def save():
            try:
                self.gym.create_membership(int(entries["Member ID"].get()), entries["Start Date"].get(), entries["End Date"].get(), float(entries["Price"].get()))
                self.gym.save_data(); win.destroy(); self.show_memberships(); messagebox.showinfo("Success", "Membership created.")
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("Error", str(exc))
        ttk.Button(win, text="Save", command=save).grid(row=4, column=1, pady=15)

    def show_payments(self):
        self.clear(); self.heading("Payments")
        top = ttk.Frame(self.content); top.pack(fill="x")
        ttk.Button(top, text="Add Payment", command=self.payment_form).pack(side="right")
        tree = self._tree(("id", "member", "amount", "date", "type"), ("ID", "Member", "Amount", "Date", "Type"))
        for p in self.gym.payments:
            tree.insert("", "end", values=(p.payment_id, p.member_id, f"{p.amount:.2f}", p.payment_date, p.payment_type()))

    def payment_form(self):
        win = tk.Toplevel(self); win.title("Add Payment"); win.geometry("400x330"); win.grab_set()
        entries = {}
        for i, label in enumerate(("Member ID", "Amount")):
            ttk.Label(win, text=label).grid(row=i, column=0, padx=12, pady=10, sticky="w")
            e = ttk.Entry(win, width=28); e.grid(row=i, column=1, padx=12, pady=10); entries[label] = e
        ttk.Label(win, text="Payment Type").grid(row=2, column=0, padx=12, pady=10, sticky="w")
        ptype = tk.StringVar(value="Cash")
        ttk.Combobox(win, textvariable=ptype, values=("Cash", "Card"), state="readonly", width=25).grid(row=2, column=1, padx=12, pady=10)
        def save():
            try:
                payment = self.gym.add_payment(int(entries["Member ID"].get()), float(entries["Amount"].get()), ptype.get())
                self.gym.save_data(); win.destroy(); self.show_payments(); messagebox.showinfo("Success", payment.process_payment())
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("Error", str(exc))
        ttk.Button(win, text="Save", command=save).grid(row=3, column=1, pady=15)

    def show_attendance(self):
        self.clear(); self.heading("Attendance")
        top = ttk.Frame(self.content); top.pack(fill="x")
        ttk.Button(top, text="Record Attendance", command=self.attendance_form).pack(side="right")
        tree = self._tree(("id", "member", "date"), ("ID", "Member", "Date"))
        for a in self.gym.attendances:
            tree.insert("", "end", values=(a.attendance_id, a.member_id, a.attendance_date))

    def attendance_form(self):
        win = tk.Toplevel(self); win.title("Record Attendance"); win.geometry("350x220"); win.grab_set()
        ttk.Label(win, text="Member ID").grid(row=0, column=0, padx=12, pady=15)
        entry = ttk.Entry(win, width=25); entry.grid(row=0, column=1, padx=12, pady=15)
        def save():
            try:
                self.gym.record_attendance(int(entry.get()))
                self.gym.save_data(); win.destroy(); self.show_attendance(); messagebox.showinfo("Success", "Attendance recorded.")
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("Error", str(exc))
        ttk.Button(win, text="Record", command=save).grid(row=1, column=1, pady=15)

    def save_now(self):
        try:
            self.gym.save_data(); messagebox.showinfo("Saved", "Data saved successfully.")
        except RuntimeError as exc:
            messagebox.showerror("Error", str(exc))

    def on_close(self):
        try:
            self.gym.save_data()
        except RuntimeError:
            pass
        self.destroy()

if __name__ == "__main__":
    app = GymApp()
    app.mainloop()
