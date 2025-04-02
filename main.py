import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QComboBox, QDateTimeEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QLabel, QHBoxLayout
)
from PySide6.QtCore import Qt, QDateTime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from database import init_db, insert_entry, get_all_entries
from export import export_to_csv, import_from_csv, export_to_pdf
from datetime import datetime
import json
import os

SETTINGS_FILE = "settings.json"

class HealthTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Erics Diet-Logger 2025")
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
        self.setMinimumSize(900, 700)
        init_db()

        self.settings = self.load_user_settings()
        self.user_height_cm = self.settings.get("height_cm", 0)
        self.init_ui()
        

    def load_user_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_user_settings(settings):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.weight_input = QLineEdit()
        self.sugar_input = QLineEdit()
        self.sleep_input = QLineEdit()
        self.mood_input = QComboBox()
        self.mood_input.addItems(["Gut", "Mittel", "Schlecht"])
        self.notes_input = QTextEdit()
        self.height_input = QLineEdit()
        self.bmi_label = QLabel("BMI: -")

        form_layout.addRow("Datum & Zeit:", self.datetime_edit)
        form_layout.addRow("Gewicht (kg):", self.weight_input)
        form_layout.addRow("Blutzucker (mg/dL):", self.sugar_input)
        form_layout.addRow("Schlafdauer (h):", self.sleep_input)
        form_layout.addRow("Befinden:", self.mood_input)
        form_layout.addRow("Bemerkung:", self.notes_input)
        form_layout.addRow("Größe (cm):", self.height_input)
        form_layout.addRow("BMI:", self.bmi_label)
        
        save_button = QPushButton("Speichern")
        save_button.clicked.connect(self.save_entry)

        button_layout = QHBoxLayout()
        export_button = QPushButton("Export CSV")
        export_button.clicked.connect(self.export_csv)
        import_button = QPushButton("Import CSV")
        import_button.clicked.connect(self.import_csv)
        pdf_button = QPushButton("Export PDF")
        pdf_button.clicked.connect(self.export_pdf)
        average_button = QPushButton("Tagesdurchschnitt")
        average_button.clicked.connect(self.show_daily_averages)

        button_layout.addWidget(export_button)
        button_layout.addWidget(import_button)
        button_layout.addWidget(pdf_button)
        button_layout.addWidget(average_button)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Datum", "Gewicht", "Zucker", "Schlaf", "Befinden", "Bemerkung"])
        self.table.setStyleSheet("background-color: #3c3f41; color: white;")

        #self.canvas = FigureCanvas(Figure(figsize=(5, 3)))
        #self.ax = self.canvas.figure.subplots()
        self.fig = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.fig)

        self.weight_input.textChanged.connect(self.update_bmi)
        self.height_input.textChanged.connect(self.update_bmi)


        layout.addLayout(form_layout)
        layout.addWidget(save_button)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("Einträge:"))
        layout.addWidget(self.table)
        layout.addWidget(QLabel("Diagramm:"))
        layout.addWidget(self.canvas)

        self.setLayout(layout)
        self.load_entries()
        
        if self.user_height_cm:
            self.height_input.setText(str(self.user_height_cm))
      
       


    def update_bmi(self):
        try:
            weight = float(self.weight_input.text())
            height_cm = float(self.height_input.text())
            height_m = height_cm / 100.0
            bmi = weight / (height_m ** 2)
            classification = self.classify_bmi(bmi)
            self.bmi_label.setText(f" {bmi:.2f} ({classification})")
        except ValueError:
            self.bmi_label.setText("-")

    def classify_bmi(self, bmi):
        if bmi < 18.5:
            return "Untergewicht"
        elif bmi < 25:
            return "Normalgewicht"
        elif bmi < 30:
            return "Übergewicht"
        elif bmi < 35:
            return "Adipositas Grad 1"
        elif bmi < 40:
            return "Adipositas Grad 2"
        else:
            return "Adipositas Grad 3"


    def save_entry(self):
        try:
            entry = {
                "timestamp": self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm"),
                "weight": float(self.weight_input.text()),
                "blood_sugar": float(self.sugar_input.text()),
                "sleep_hours": float(self.sleep_input.text()),
                "mood": self.mood_input.currentText(),
                "notes": self.notes_input.toPlainText()
            }
            insert_entry(entry)
            self.load_entries()
            self.clear_form()
            # Körpergröße speichern
            try:
                self.user_height_cm = float(self.height_input.text())
                self.settings["height_cm"] = self.user_height_cm
                self.save_user_settings(self.settings)
            except ValueError:
                pass
        except ValueError:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Fehler", "Bitte gib gültige Zahlen ein.")

    def load_entries(self):
        self.fig.clf()  # Alte Plots löschen
        data = get_all_entries()
        self.table.setRowCount(len(data))

        dates, weights, sugars, bmis = [], [], [], []

        for row_idx, row in enumerate(data):
            for col_idx, value in enumerate(row[1:7]):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            dt = datetime.strptime(row[1], "%Y-%m-%d %H:%M")
            dates.append(dt)
            weights.append(row[2])
            sugars.append(row[3])

            if hasattr(self, 'user_height_cm') and self.user_height_cm > 0:
                height_m = self.user_height_cm / 100.0
                bmi = row[2] / (height_m ** 2)
                bmis.append(bmi)
            else:
                bmis.append(None)

        # Subplots erzeugen (3 Zeilen, 1 Spalte)
        axs = self.fig.subplots(3, 1, sharex=True)

        # Subplot 1: Gewicht
        axs[0].plot(dates, weights, color='blue', label="Gewicht (kg)")
        axs[0].set_ylabel("Gewicht (kg)")
        axs[0].legend()
        axs[0].grid(True)

        # Subplot 2: Blutzucker
        axs[1].plot(dates, sugars, color='green', label="Zucker (mg/dL)")
        axs[1].set_ylabel("Zucker (mg/dL)")
        axs[1].legend()
        axs[1].grid(True)

        # Subplot 3: BMI (wenn vorhanden)
        if any(bmis):
            axs[2].plot(dates, bmis, color='orange', linestyle='--', label="BMI")
            axs[2].set_ylabel("BMI")
            axs[2].grid(True)
            axs[2].legend()

            if self.user_height_cm:
                ideal_min = 18.5
                ideal_max = 24.9
                axs[2].axhspan(ideal_min, ideal_max, color='green', alpha=0.1, label="BMI Idealbereich")
                axs[2].legend()

        axs[2].set_xlabel("Datum")

        self.fig.tight_layout()
        self.canvas.draw()

    def load_entries1(self):
        self.ax.clear()
        data = get_all_entries()
        self.table.setRowCount(len(data))
        dates, weights, sugars = [], [], []
        bmis = []
        for row_idx, row in enumerate(data):
            for col_idx, value in enumerate(row[1:7]):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            dt = datetime.strptime(row[1], "%Y-%m-%d %H:%M")
            dates.append(dt)
            weights.append(row[2])
            sugars.append(row[3])

            # BMI berechnen, wenn Größe bekannt
            if hasattr(self, 'user_height_cm') and self.user_height_cm > 0:
                height_m = self.user_height_cm / 100.0
                bmi = row[2] / (height_m ** 2)
                bmis.append(bmi)
            else:
                bmis.append(None)

     
        color1 = 'blue'
        color2 = 'green'
        color3 = 'orange'

        ax1 = self.ax
        ax2 = ax1.twinx()

        ax1.plot(dates, weights, color=color1, label="Gewicht (kg)")
        ax2.plot(dates, sugars, color=color2, label="Zucker (mg/dL)")

        # BMI als dritte Linie (falls vorhanden)
        if any(bmis):
            ax1.plot(dates, bmis, color=color3, linestyle="--", label="BMI")

        ax1.set_ylabel("Gewicht / BMI", color=color1)
        ax2.set_ylabel("Zucker (mg/dL)", color=color2)

        ax1.tick_params(axis='y', labelcolor=color1)
        ax2.tick_params(axis='y', labelcolor=color2)

        ax1.set_title("Verlauf von Gewicht, Zucker & BMI")
        ax1.legend(loc="upper left")
        # Idealbereich für BMI
        if self.user_height_cm:
            ideal_min = 18.5
            ideal_max = 24.9
            ax1.axhspan(ideal_min, ideal_max, color='green', alpha=0.1, label="BMI Idealbereich")

        self.canvas.draw()


    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "CSV Export", "", "CSV Dateien (*.csv)")
        if path:
            export_to_csv(path)

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "CSV Import", "", "CSV Dateien (*.csv)")
        if path:
            entries = import_from_csv(path)
            for entry in entries:
                insert_entry(entry)
            self.load_entries()
    
    def clear_form(self):
        self.weight_input.clear()
        self.sugar_input.clear()
        self.sleep_input.clear()
        self.notes_input.clear()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.height_input.clear()
        self.bmi_label.setText("BMI: -")
        
    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "PDF Export", "", "PDF Dateien (*.pdf)")
        if path:
            export_to_pdf(path)
            
    def show_daily_averages(self):
        data = get_all_entries()
        from collections import defaultdict
        daily_data = defaultdict(list)

        for row in data:
            date = row[1][:10]  # YYYY-MM-DD
            daily_data[date].append(row)

        latest_day = max(daily_data.keys()) if daily_data else None
        if not latest_day:
            return

        entries = daily_data[latest_day]

        avg_weight = sum(e[2] for e in entries) / len(entries)
        avg_sugar = sum(e[3] for e in entries) / len(entries)
        avg_sleep = sum(e[4] for e in entries) / len(entries)

        text = f"Durchschnitt {latest_day}:\nGewicht: {avg_weight:.1f} kg\nZucker: {avg_sugar:.1f} mg/dL\nSchlaf: {avg_sleep:.1f} h"
        
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Tagesdurchschnitt", text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HealthTracker()
    window.show()
    sys.exit(app.exec())
