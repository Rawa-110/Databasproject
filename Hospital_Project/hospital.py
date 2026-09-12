import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date

DB_NAME = "hospital.db"


def connect_db():
    connection = sqlite3.connect(DB_NAME)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS departments (
        department_id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_name TEXT NOT NULL UNIQUE,
        location TEXT
    );

    CREATE TABLE IF NOT EXISTS doctors (
        doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_name TEXT NOT NULL,
        specialization TEXT,
        phone TEXT,
        department_id INTEGER NOT NULL,
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
    );

    CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        gender TEXT,
        date_of_birth TEXT,
        phone TEXT,
        address TEXT
    );

    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        reason TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
    );

    CREATE TABLE IF NOT EXISTS medical_records (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        record_date TEXT NOT NULL,
        diagnosis TEXT,
        symptoms TEXT,
        notes TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
    );

    CREATE TABLE IF NOT EXISTS rooms (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT NOT NULL UNIQUE,
        room_type TEXT,
        beds_count INTEGER NOT NULL,
        status TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS admissions (
        admission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        room_id INTEGER NOT NULL,
        admission_date TEXT NOT NULL,
        discharge_date TEXT,
        reason TEXT,
        status TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY (room_id) REFERENCES rooms(room_id)
    );

    CREATE TABLE IF NOT EXISTS medications (
        medication_id INTEGER PRIMARY KEY AUTOINCREMENT,
        medication_name TEXT NOT NULL UNIQUE,
        description TEXT,
        quantity_available INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS prescriptions (
        prescription_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        medication_id INTEGER NOT NULL,
        prescription_date TEXT NOT NULL,
        dosage TEXT,
        duration TEXT,
        instructions TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
        FOREIGN KEY (medication_id) REFERENCES medications(medication_id)
    );

    CREATE TABLE IF NOT EXISTS bills (
        bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        bill_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        paid_amount REAL DEFAULT 0,
        payment_status TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    );

    CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_id INTEGER NOT NULL,
        payment_date TEXT NOT NULL,
        amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        FOREIGN KEY (bill_id) REFERENCES bills(bill_id)
    );
    """)

    departments = [
        ("الطوارئ", "الدور الأرضي"),
        ("الجراحة", "الدور الأول"),
        ("الباطنية", "الدور الثاني"),
        ("الأطفال", "الدور الثاني"),
    ]
    for row in departments:
        cursor.execute(
            "INSERT OR IGNORE INTO departments (department_name, location) VALUES (?, ?)",
            row,
        )

    doctors = [
        ("أحمد محمد", "جراحة عامة", "0500000001", "الجراحة"),
        ("سارة علي", "باطنية", "0500000002", "الباطنية"),
        ("خالد عبدالله", "طوارئ", "0500000003", "الطوارئ"),
    ]
    for name, spec, phone, dep_name in doctors:
        cursor.execute("SELECT department_id FROM departments WHERE department_name=?", (dep_name,))
        dep = cursor.fetchone()
        if dep:
            cursor.execute(
                "SELECT doctor_id FROM doctors WHERE doctor_name=? AND phone=?",
                (name, phone),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO doctors (doctor_name, specialization, phone, department_id) VALUES (?, ?, ?, ?)",
                    (name, spec, phone, dep[0]),
                )

    patients = [
        ("محمد أحمد", "ذكر", "1995-05-10", "0550000001", "جدة"),
        ("نورة خالد", "أنثى", "2000-08-20", "0550000002", "جدة"),
        ("عبدالله علي", "ذكر", "1988-12-15", "0550000003", "مكة"),
    ]
    for row in patients:
        cursor.execute("SELECT patient_id FROM patients WHERE patient_name=? AND phone=?", (row[0], row[3]))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO patients (patient_name, gender, date_of_birth, phone, address) VALUES (?, ?, ?, ?, ?)",
                row,
            )

    rooms = [
        ("101", "غرفة عادية", 2, "متاحة"),
        ("102", "غرفة عادية", 2, "متاحة"),
        ("201", "غرفة خاصة", 1, "مشغولة"),
        ("202", "غرفة عناية", 1, "متاحة"),
    ]
    for row in rooms:
        cursor.execute("INSERT OR IGNORE INTO rooms (room_number, room_type, beds_count, status) VALUES (?, ?, ?, ?)", row)

    medications = [
        ("باراسيتامول", "مسكن للألم وخافض للحرارة", 100),
        ("أموكسيسيلين", "مضاد حيوي", 50),
        ("أوميبرازول", "لعلاج حموضة المعدة", 75),
        ("فيتامين د", "مكمل غذائي", 60),
    ]
    for row in medications:
        cursor.execute(
            "INSERT OR IGNORE INTO medications (medication_name, description, quantity_available) VALUES (?, ?, ?)",
            row,
        )

    connection.commit()
    connection.close()


def combo_id(value):
    try:
        return int(str(value).split(" - ", 1)[0])
    except (ValueError, TypeError):
        return None


def make_window(parent, title, geometry="1200x700"):
    window = tk.Toplevel(parent)
    window.title(title)
    window.geometry(geometry)
    window.resizable(True, True)
    window.transient(parent)
    return window


class CRUDWindow:
    def __init__(self, parent, config):
        self.config = config
        self.window = make_window(parent, config["title"], config.get("geometry", "1200x700"))
        self.vars = {}
        self.widgets = {}
        self.current_id = None
        self.build()
        self.load_data()

    def build(self):
        title = tk.Label(self.window, text=self.config["title"], font=("Arial", 22, "bold"))
        title.pack(pady=10)

        form = tk.LabelFrame(self.window, text="البيانات", font=("Arial", 11, "bold"), padx=10, pady=10)
        form.pack(fill="x", padx=15, pady=5)

        fields = self.config["fields"]
        for i, field in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            key, label, kind = field[:3]
            tk.Label(form, text=label, width=18, anchor="e").grid(row=row, column=col, padx=5, pady=6)
            var = tk.StringVar()
            self.vars[key] = var

            if kind == "combo":
                values = field[3]
                widget = ttk.Combobox(form, textvariable=var, state="readonly", width=34)
                widget._source = values
                self.widgets[key] = widget
                self.refresh_combo(key)
            elif kind == "readonly":
                widget = tk.Entry(form, textvariable=var, state="readonly", width=36)
                self.widgets[key] = widget
            else:
                widget = tk.Entry(form, textvariable=var, width=36)
                self.widgets[key] = widget
            widget.grid(row=row, column=col + 1, padx=5, pady=6)

        buttons = tk.Frame(self.window)
        buttons.pack(pady=8)
        for text, command in [
            ("إضافة", self.add),
            ("تعديل", self.update),
            ("حذف", self.delete),
            ("مسح الحقول", self.clear),
            ("تحديث", self.load_data),
        ]:
            tk.Button(buttons, text=text, width=14, command=command).pack(side="left", padx=4)

        search_frame = tk.Frame(self.window)
        search_frame.pack(fill="x", padx=15, pady=5)
        tk.Label(search_frame, text="بحث:").pack(side="right", padx=5)
        self.search_var = tk.StringVar()
        search = tk.Entry(search_frame, textvariable=self.search_var, width=45)
        search.pack(side="right")
        self.search_var.trace_add("write", lambda *_: self.load_data())

        table_frame = tk.Frame(self.window)
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)
        self.tree = ttk.Treeview(table_frame, columns=self.config["columns"], show="headings")
        for col, heading, width in self.config["headings"]:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="center")
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.bind("<<TreeviewSelect>>", self.select_row)

    def refresh_combo(self, key):
        widget = self.widgets.get(key)
        if widget is None or not hasattr(widget, "_source"):
            return
        source = widget._source
        if isinstance(source, list):
            values = source
        else:
            table, id_col, name_col = source
            conn = connect_db()
            cur = conn.cursor()
            cur.execute(f"SELECT {id_col}, {name_col} FROM {table} ORDER BY {name_col}")
            values = [f"{r[0]} - {r[1]}" for r in cur.fetchall()]
            conn.close()
        widget["values"] = values

    def validate(self):
        for field in self.config["fields"]:
            key, label, kind = field[:3]
            value = self.vars[key].get().strip()
            if field[4] if len(field) > 4 else False:
                if not value:
                    messagebox.showwarning("تنبيه", f"الرجاء إدخال {label}")
                    return False
            if value and kind == "int":
                try:
                    int(value)
                except ValueError:
                    messagebox.showwarning("تنبيه", f"{label} يجب أن يكون رقمًا صحيحًا")
                    return False
            if value and kind == "real":
                try:
                    float(value)
                except ValueError:
                    messagebox.showwarning("تنبيه", f"{label} يجب أن يكون رقمًا")
                    return False
        return True

    def values_for_db(self):
        result = []
        for field in self.config["fields"]:
            key, _, kind = field[:3]
            value = self.vars[key].get().strip()
            if kind == "combo" and not isinstance(field[3], list):
                value = combo_id(value)
            elif kind == "int" and value:
                value = int(value)
            elif kind == "real" and value:
                value = float(value)
            result.append(value if value != "" else None)
        return result

    def add(self):
        if not self.validate():
            return
        conn = None
        try:
            conn = connect_db()
            cur = conn.cursor()
            cols = [f[0] for f in self.config["fields"]]
            placeholders = ",".join("?" for _ in cols)
            cur.execute(
                f"INSERT INTO {self.config['table']} ({','.join(cols)}) VALUES ({placeholders})",
                self.values_for_db(),
            )
            conn.commit()
            messagebox.showinfo("نجاح", f"تمت إضافة {self.config['singular']} بنجاح")
            self.clear()
            self.load_data()
        except sqlite3.IntegrityError as e:
            messagebox.showerror("لا يمكن الحفظ", f"تحقق من البيانات والروابط بين الجداول.\n\n{e}")
        except sqlite3.Error as e:
            messagebox.showerror("خطأ في قاعدة البيانات", str(e))
        finally:
            if conn:
                conn.close()

    def update(self):
        if not self.current_id:
            messagebox.showwarning("تنبيه", "اختر سجلًا من الجدول أولًا")
            return
        if not self.validate():
            return
        conn = None
        try:
            conn = connect_db()
            cur = conn.cursor()
            cols = [f[0] for f in self.config["fields"]]
            set_sql = ",".join(f"{c}=?" for c in cols)
            cur.execute(
                f"UPDATE {self.config['table']} SET {set_sql} WHERE {self.config['pk']}=?",
                self.values_for_db() + [self.current_id],
            )
            conn.commit()
            messagebox.showinfo("نجاح", f"تم تعديل {self.config['singular']} بنجاح")
            self.clear()
            self.load_data()
        except sqlite3.IntegrityError as e:
            messagebox.showerror("لا يمكن التعديل", str(e))
        except sqlite3.Error as e:
            messagebox.showerror("خطأ", str(e))
        finally:
            if conn:
                conn.close()

    def delete(self):
        if not self.current_id:
            messagebox.showwarning("تنبيه", "اختر سجلًا من الجدول أولًا")
            return
        if not messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف السجل المحدد؟"):
            return
        conn = None
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {self.config['table']} WHERE {self.config['pk']}=?", (self.current_id,))
            conn.commit()
            messagebox.showinfo("نجاح", "تم الحذف بنجاح")
            self.clear()
            self.load_data()
        except sqlite3.IntegrityError:
            messagebox.showerror("لا يمكن الحذف", "لا يمكن حذف السجل لأنه مرتبط ببيانات في جداول أخرى.")
        except sqlite3.Error as e:
            messagebox.showerror("خطأ", str(e))
        finally:
            if conn:
                conn.close()

    def clear(self):
        self.current_id = None
        for var in self.vars.values():
            var.set("")
        self.tree.selection_remove(self.tree.selection())

    def load_data(self):
        if not hasattr(self, "tree"):
            return
        for key in self.widgets:
            self.refresh_combo(key)
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = None
        try:
            conn = connect_db()
            cur = conn.cursor()
            search = self.search_var.get().strip() if hasattr(self, "search_var") else ""
            sql = self.config["select_sql"]
            params = []
            if search and self.config.get("search_sql"):
                terms = self.config["search_sql"]
                sql += " WHERE " + " OR ".join(f"{term} LIKE ?" for term in terms)
                params = [f"%{search}%"] * len(terms)
            sql += self.config.get("order_sql", "")
            cur.execute(sql, params)
            for row in cur.fetchall():
                self.tree.insert("", "end", values=row)
        except sqlite3.Error as e:
            messagebox.showerror("خطأ", f"تعذر تحميل البيانات:\n{e}")
        finally:
            if conn:
                conn.close()

    def select_row(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if not values:
            return
        self.current_id = values[0]
        # config row_mapping tells which displayed value maps to each field.
        for key, index in self.config["row_mapping"].items():
            value = values[index]
            self.vars[key].set(value)


def cfg_department():
    return {
        "title": "إدارة الأقسام", "singular": "القسم", "table": "departments", "pk": "department_id",
        "fields": [("department_name", "اسم القسم", "text", None, True), ("location", "الموقع", "text", None, False)],
        "columns": ("id", "name", "location"),
        "headings": (("id", "الرقم", 80), ("name", "اسم القسم", 250), ("location", "الموقع", 250)),
        "select_sql": "SELECT department_id, department_name, COALESCE(location,'') FROM departments",
        "search_sql": ["department_name", "location"], "order_sql": " ORDER BY department_id DESC",
        "row_mapping": {"department_name": 1, "location": 2},
    }


def cfg_doctor():
    return {
        "title": "إدارة الأطباء", "singular": "الطبيب", "table": "doctors", "pk": "doctor_id",
        "fields": [("doctor_name", "اسم الطبيب", "text", None, True), ("specialization", "التخصص", "text", None, False),
                   ("phone", "الجوال", "text", None, False), ("department_id", "القسم", "combo", ("departments", "department_id", "department_name"), True)],
        "columns": ("id", "name", "spec", "phone", "department"),
        "headings": (("id", "الرقم", 70), ("name", "الطبيب", 190), ("spec", "التخصص", 180), ("phone", "الجوال", 130), ("department", "القسم", 180)),
        "select_sql": "SELECT d.doctor_id,d.doctor_name,COALESCE(d.specialization,''),COALESCE(d.phone,''),CAST(dep.department_id AS TEXT)||' - '||dep.department_name FROM doctors d JOIN departments dep ON d.department_id=dep.department_id",
        "search_sql": ["d.doctor_name", "d.specialization", "d.phone", "dep.department_name"], "order_sql": " ORDER BY d.doctor_id DESC",
        "row_mapping": {"doctor_name": 1, "specialization": 2, "phone": 3, "department_id": 4},
    }


def cfg_patient():
    return {
        "title": "إدارة المرضى", "singular": "المريض", "table": "patients", "pk": "patient_id",
        "fields": [("patient_name", "اسم المريض", "text", None, True), ("gender", "الجنس", "combo", ["ذكر", "أنثى"], False),
                   ("date_of_birth", "تاريخ الميلاد", "text", None, False), ("phone", "الجوال", "text", None, False),
                   ("address", "العنوان", "text", None, False)],
        "columns": ("id", "name", "gender", "birth", "phone", "address"),
        "headings": (("id", "الرقم", 70), ("name", "المريض", 180), ("gender", "الجنس", 90), ("birth", "الميلاد", 110), ("phone", "الجوال", 130), ("address", "العنوان", 180)),
        "select_sql": "SELECT patient_id,patient_name,COALESCE(gender,''),COALESCE(date_of_birth,''),COALESCE(phone,''),COALESCE(address,'') FROM patients",
        "search_sql": ["patient_name", "phone", "address"], "order_sql": " ORDER BY patient_id DESC",
        "row_mapping": {"patient_name": 1, "gender": 2, "date_of_birth": 3, "phone": 4, "address": 5},
    }


def cfg_appointment():
    return {
        "title": "إدارة المواعيد", "singular": "الموعد", "table": "appointments", "pk": "appointment_id",
        "fields": [("patient_id", "المريض", "combo", ("patients", "patient_id", "patient_name"), True),
                   ("doctor_id", "الطبيب", "combo", ("doctors", "doctor_id", "doctor_name"), True),
                   ("appointment_date", "التاريخ", "text", None, True), ("appointment_time", "الوقت", "text", None, True),
                   ("reason", "السبب", "text", None, False)],
        "columns": ("id", "patient", "doctor", "date", "time", "reason"),
        "headings": (("id", "الرقم", 70), ("patient", "المريض", 180), ("doctor", "الطبيب", 180), ("date", "التاريخ", 110), ("time", "الوقت", 90), ("reason", "السبب", 220)),
        "select_sql": "SELECT a.appointment_id,CAST(p.patient_id AS TEXT)||' - '||p.patient_name,CAST(d.doctor_id AS TEXT)||' - '||d.doctor_name,a.appointment_date,a.appointment_time,COALESCE(a.reason,'') FROM appointments a JOIN patients p ON a.patient_id=p.patient_id JOIN doctors d ON a.doctor_id=d.doctor_id",
        "search_sql": ["p.patient_name", "d.doctor_name", "a.appointment_date", "a.reason"], "order_sql": " ORDER BY a.appointment_date DESC,a.appointment_time DESC",
        "row_mapping": {"patient_id": 1, "doctor_id": 2, "appointment_date": 3, "appointment_time": 4, "reason": 5},
    }


def cfg_record():
    return {
        "title": "إدارة السجل الطبي", "singular": "السجل الطبي", "table": "medical_records", "pk": "record_id",
        "fields": [("patient_id", "المريض", "combo", ("patients", "patient_id", "patient_name"), True),
                   ("doctor_id", "الطبيب", "combo", ("doctors", "doctor_id", "doctor_name"), True),
                   ("record_date", "التاريخ", "text", None, True), ("diagnosis", "التشخيص", "text", None, False),
                   ("symptoms", "الأعراض", "text", None, False), ("notes", "الملاحظات", "text", None, False)],
        "columns": ("id", "patient", "doctor", "date", "diagnosis", "symptoms", "notes"),
        "headings": (("id", "الرقم", 60), ("patient", "المريض", 150), ("doctor", "الطبيب", 150), ("date", "التاريخ", 100), ("diagnosis", "التشخيص", 180), ("symptoms", "الأعراض", 180), ("notes", "الملاحظات", 200)),
        "select_sql": "SELECT r.record_id,CAST(p.patient_id AS TEXT)||' - '||p.patient_name,CAST(d.doctor_id AS TEXT)||' - '||d.doctor_name,r.record_date,COALESCE(r.diagnosis,''),COALESCE(r.symptoms,''),COALESCE(r.notes,'') FROM medical_records r JOIN patients p ON r.patient_id=p.patient_id JOIN doctors d ON r.doctor_id=d.doctor_id",
        "search_sql": ["p.patient_name", "d.doctor_name", "r.diagnosis", "r.symptoms"], "order_sql": " ORDER BY r.record_id DESC",
        "row_mapping": {"patient_id": 1, "doctor_id": 2, "record_date": 3, "diagnosis": 4, "symptoms": 5, "notes": 6},
    }


def cfg_room():
    return {
        "title": "إدارة الغرف", "singular": "الغرفة", "table": "rooms", "pk": "room_id",
        "fields": [("room_number", "رقم الغرفة", "text", None, True), ("room_type", "نوع الغرفة", "combo", ["غرفة عادية", "غرفة خاصة", "غرفة عناية"], False),
                   ("beds_count", "عدد الأسرة", "int", None, True), ("status", "الحالة", "combo", ["متاحة", "مشغولة", "صيانة"], True)],
        "columns": ("id", "number", "type", "beds", "status"),
        "headings": (("id", "الرقم", 70), ("number", "الغرفة", 120), ("type", "النوع", 180), ("beds", "الأسرة", 90), ("status", "الحالة", 120)),
        "select_sql": "SELECT room_id,room_number,COALESCE(room_type,''),beds_count,status FROM rooms",
        "search_sql": ["room_number", "room_type", "status"], "order_sql": " ORDER BY room_id DESC",
        "row_mapping": {"room_number": 1, "room_type": 2, "beds_count": 3, "status": 4},
    }


def cfg_admission():
    return {
        "title": "إدارة التنويم", "singular": "عملية التنويم", "table": "admissions", "pk": "admission_id",
        "fields": [("patient_id", "المريض", "combo", ("patients", "patient_id", "patient_name"), True),
                   ("room_id", "الغرفة", "combo", ("rooms", "room_id", "room_number"), True),
                   ("admission_date", "تاريخ الدخول", "text", None, True), ("discharge_date", "تاريخ الخروج", "text", None, False),
                   ("reason", "السبب", "text", None, False), ("status", "الحالة", "combo", ["منوّم", "خرج"], True)],
        "columns": ("id", "patient", "room", "in", "out", "reason", "status"),
        "headings": (("id", "الرقم", 60), ("patient", "المريض", 150), ("room", "الغرفة", 120), ("in", "الدخول", 110), ("out", "الخروج", 110), ("reason", "السبب", 180), ("status", "الحالة", 100)),
        "select_sql": "SELECT a.admission_id,CAST(p.patient_id AS TEXT)||' - '||p.patient_name,CAST(r.room_id AS TEXT)||' - '||r.room_number,a.admission_date,COALESCE(a.discharge_date,''),COALESCE(a.reason,''),a.status FROM admissions a JOIN patients p ON a.patient_id=p.patient_id JOIN rooms r ON a.room_id=r.room_id",
        "search_sql": ["p.patient_name", "r.room_number", "a.status", "a.reason"], "order_sql": " ORDER BY a.admission_id DESC",
        "row_mapping": {"patient_id": 1, "room_id": 2, "admission_date": 3, "discharge_date": 4, "reason": 5, "status": 6},
    }


def cfg_medication():
    return {
        "title": "إدارة الأدوية", "singular": "الدواء", "table": "medications", "pk": "medication_id",
        "fields": [("medication_name", "اسم الدواء", "text", None, True), ("description", "الوصف", "text", None, False),
                   ("quantity_available", "الكمية المتوفرة", "int", None, True)],
        "columns": ("id", "name", "description", "quantity"),
        "headings": (("id", "الرقم", 70), ("name", "الدواء", 200), ("description", "الوصف", 300), ("quantity", "الكمية", 110)),
        "select_sql": "SELECT medication_id,medication_name,COALESCE(description,''),COALESCE(quantity_available,0) FROM medications",
        "search_sql": ["medication_name", "description"], "order_sql": " ORDER BY medication_id DESC",
        "row_mapping": {"medication_name": 1, "description": 2, "quantity_available": 3},
    }


def cfg_prescription():
    return {
        "title": "إدارة الوصفات الطبية", "singular": "الوصفة", "table": "prescriptions", "pk": "prescription_id",
        "fields": [("patient_id", "المريض", "combo", ("patients", "patient_id", "patient_name"), True),
                   ("doctor_id", "الطبيب", "combo", ("doctors", "doctor_id", "doctor_name"), True),
                   ("medication_id", "الدواء", "combo", ("medications", "medication_id", "medication_name"), True),
                   ("prescription_date", "التاريخ", "text", None, True), ("dosage", "الجرعة", "text", None, False),
                   ("duration", "المدة", "text", None, False), ("instructions", "التعليمات", "text", None, False)],
        "columns": ("id", "patient", "doctor", "medication", "date", "dosage", "duration", "instructions"),
        "headings": (("id", "الرقم", 60), ("patient", "المريض", 150), ("doctor", "الطبيب", 150), ("medication", "الدواء", 150), ("date", "التاريخ", 100), ("dosage", "الجرعة", 110), ("duration", "المدة", 110), ("instructions", "التعليمات", 220)),
        "select_sql": "SELECT pr.prescription_id,CAST(p.patient_id AS TEXT)||' - '||p.patient_name,CAST(d.doctor_id AS TEXT)||' - '||d.doctor_name,CAST(m.medication_id AS TEXT)||' - '||m.medication_name,pr.prescription_date,COALESCE(pr.dosage,''),COALESCE(pr.duration,''),COALESCE(pr.instructions,'') FROM prescriptions pr JOIN patients p ON pr.patient_id=p.patient_id JOIN doctors d ON pr.doctor_id=d.doctor_id JOIN medications m ON pr.medication_id=m.medication_id",
        "search_sql": ["p.patient_name", "d.doctor_name", "m.medication_name", "pr.prescription_date"], "order_sql": " ORDER BY pr.prescription_id DESC",
        "row_mapping": {"patient_id": 1, "doctor_id": 2, "medication_id": 3, "prescription_date": 4, "dosage": 5, "duration": 6, "instructions": 7},
    }


def cfg_bill():
    return {
        "title": "إدارة الفواتير", "singular": "الفاتورة", "table": "bills", "pk": "bill_id",
        "fields": [("patient_id", "المريض", "combo", ("patients", "patient_id", "patient_name"), True),
                   ("bill_date", "التاريخ", "text", None, True), ("total_amount", "الإجمالي", "real", None, True),
                   ("paid_amount", "المدفوع", "real", None, True), ("payment_status", "حالة الدفع", "combo", ["مدفوعة", "مدفوعة جزئيًا", "غير مدفوعة"], True)],
        "columns": ("id", "patient", "date", "total", "paid", "status"),
        "headings": (("id", "الرقم", 70), ("patient", "المريض", 180), ("date", "التاريخ", 110), ("total", "الإجمالي", 110), ("paid", "المدفوع", 110), ("status", "الحالة", 150)),
        "select_sql": "SELECT b.bill_id,CAST(p.patient_id AS TEXT)||' - '||p.patient_name,b.bill_date,b.total_amount,b.paid_amount,b.payment_status FROM bills b JOIN patients p ON b.patient_id=p.patient_id",
        "search_sql": ["p.patient_name", "b.bill_date", "b.payment_status"], "order_sql": " ORDER BY b.bill_id DESC",
        "row_mapping": {"patient_id": 1, "bill_date": 2, "total_amount": 3, "paid_amount": 4, "payment_status": 5},
    }


def cfg_payment():
    return {
        "title": "إدارة المدفوعات", "singular": "الدفعة", "table": "payments", "pk": "payment_id",
        "fields": [("bill_id", "الفاتورة", "combo", ("bills", "bill_id", "bill_date"), True),
                   ("payment_date", "تاريخ الدفع", "text", None, True), ("amount", "المبلغ", "real", None, True),
                   ("payment_method", "طريقة الدفع", "combo", ["نقدي", "بطاقة", "تحويل بنكي"], True)],
        "columns": ("id", "bill", "date", "amount", "method"),
        "headings": (("id", "الرقم", 70), ("bill", "الفاتورة", 160), ("date", "التاريخ", 110), ("amount", "المبلغ", 110), ("method", "طريقة الدفع", 150)),
        "select_sql": "SELECT pay.payment_id,CAST(b.bill_id AS TEXT)||' - '||b.bill_date,pay.payment_date,pay.amount,pay.payment_method FROM payments pay JOIN bills b ON pay.bill_id=b.bill_id",
        "search_sql": ["b.bill_date", "pay.payment_date", "pay.payment_method"], "order_sql": " ORDER BY pay.payment_id DESC",
        "row_mapping": {"bill_id": 1, "payment_date": 2, "amount": 3, "payment_method": 4},
    }


def open_config(parent, config):
    CRUDWindow(parent, config)


def open_payments(parent):
    open_config(parent, cfg_payment())


def dashboard(parent):
    window = make_window(parent, "لوحة المعلومات", "900x550")
    tk.Label(window, text="لوحة معلومات المستشفى", font=("Arial", 24, "bold")).pack(pady=20)
    frame = tk.Frame(window)
    frame.pack(fill="both", expand=True, padx=30, pady=20)
    tables = [
        ("المرضى", "patients"), ("الأطباء", "doctors"), ("الأقسام", "departments"),
        ("المواعيد", "appointments"), ("السجلات الطبية", "medical_records"), ("الغرف", "rooms"),
        ("التنويم", "admissions"), ("الأدوية", "medications"), ("الوصفات", "prescriptions"),
        ("الفواتير", "bills"), ("المدفوعات", "payments")
    ]
    conn = connect_db()
    cur = conn.cursor()
    for i, (label, table) in enumerate(tables):
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        box = tk.LabelFrame(frame, text=label, font=("Arial", 11, "bold"), width=220, height=90)
        box.grid(row=i // 3, column=i % 3, padx=15, pady=15, sticky="nsew")
        box.grid_propagate(False)
        tk.Label(box, text=str(count), font=("Arial", 22, "bold")).pack(expand=True)
    conn.close()
    for i in range(3):
        frame.columnconfigure(i, weight=1)


def main_window():
    root = tk.Tk()
    root.title("نظام إدارة المستشفى")
    root.geometry("1150x720")
    root.resizable(False, False)

    tk.Label(root, text="نظام إدارة المستشفى", font=("Arial", 28, "bold")).pack(pady=20)
    tk.Label(root, text="Hospital Management System", font=("Arial", 13)).pack()

    buttons_frame = tk.Frame(root)
    buttons_frame.pack(pady=25)

    buttons = [
        ("📊 لوحة المعلومات", lambda: dashboard(root)),
        ("👤 المرضى", lambda: open_config(root, cfg_patient())),
        ("👨‍⚕️ الأطباء", lambda: open_config(root, cfg_doctor())),
        ("🏥 الأقسام", lambda: open_config(root, cfg_department())),
        ("📅 المواعيد", lambda: open_config(root, cfg_appointment())),
        ("🩺 السجل الطبي", lambda: open_config(root, cfg_record())),
        ("🛏️ التنويم", lambda: open_config(root, cfg_admission())),
        ("🚪 الغرف", lambda: open_config(root, cfg_room())),
        ("💊 الأدوية", lambda: open_config(root, cfg_medication())),
        ("💊 الوصفات الطبية", lambda: open_config(root, cfg_prescription())),
        ("💰 الفواتير", lambda: open_config(root, cfg_bill())),
        ("💳 المدفوعات", lambda: open_payments(root)),
        ("❌ خروج", root.destroy),
    ]

    for i, (text, command) in enumerate(buttons):
        tk.Button(
            buttons_frame, text=text, width=22, height=2,
            font=("Arial", 11), command=command
        ).grid(row=i // 3, column=i % 3, padx=8, pady=8)

    tk.Label(
        root,
        text="جميع الجداول مرتبطة بقاعدة بيانات SQLite باسم hospital.db",
        font=("Arial", 11)
    ).pack(pady=15)

    root.mainloop()


if __name__ == "__main__":
    try:
        initialize_database()
        main_window()
    except sqlite3.Error as error:
        messagebox.showerror("خطأ في قاعدة البيانات", str(error))
