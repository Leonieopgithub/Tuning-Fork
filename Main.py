#imports
import sys
import random
import time
import numpy as np
import matplotlib.pyplot as plt

#devices
from PySide6 import QtCore, QtWidgets
from mitutoyo import Mitutoyo
from SR830 import SR830
from PL125T2 import PL125T2
from Rigol import Rigol
from rigol_dg1022 import RigolDG
from PIE625 import PIE625
from calibration import calibrateAir


#for questions: leonie.scholte@gmail.com


class UserInterface(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        #nothing connected yet 
        self.mitutoyo = None 
        self.normal_lockin = None
        self.shear_lockin = None
        self.temperature_logger = None
        self.rigol = None
        self.piezo = None
        self.setWindowTitle("Tuning Fork GUI")
        self.resize(800, 500)

        #central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        #main lay-out
        main_layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(main_layout)
        main_layout.setAlignment(QtCore.Qt.AlignTop)

        #title
        title_label = QtWidgets.QLabel("Tuning Fork Measurement")
        main_layout.addWidget(title_label)

        #live values
        values_group = QtWidgets.QGroupBox("Live values")
        values_layout = QtWidgets.QGridLayout()
        values_group.setLayout(values_layout)

        self.temperature_label = QtWidgets.QLabel("Temperature: -- °C")
        self.height_label = QtWidgets.QLabel("Height: -- mm")
        self.frequency_label = QtWidgets.QLabel("Frequency: -- Hz")
        self.amplitude_label = QtWidgets.QLabel("Amplitude: -- V")
        self.phase_label = QtWidgets.QLabel("Phase: -- °")
        self.q_label = QtWidgets.QLabel("Q-factor: --")

        values_layout.addWidget(self.temperature_label, 0, 0)
        values_layout.addWidget(self.height_label, 0, 1)
        values_layout.addWidget(self.frequency_label, 1, 0)
        values_layout.addWidget(self.amplitude_label, 1, 1)
        values_layout.addWidget(self.phase_label, 2, 0)
        values_layout.addWidget(self.q_label, 2, 1)

        main_layout.addWidget(values_group)

        self.tabs = QtWidgets.QTabWidget()

        self.devices_tab = QtWidgets.QWidget()
        self.calibration_tab = QtWidgets.QWidget()
        self.live_tab = QtWidgets.QWidget()
    
        #devices tab layout
        devices_tab_layout = QtWidgets.QVBoxLayout()
        self.devices_tab.setLayout(devices_tab_layout)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_content = QtWidgets.QWidget()
        devices_layout = QtWidgets.QVBoxLayout()
        scroll_content.setLayout(devices_layout)

        scroll_area.setWidget(scroll_content)

        devices_tab_layout.addWidget(scroll_area)

        self.connect_all_button = QtWidgets.QPushButton("Connect All")
        self.connect_all_button.clicked.connect(self.connect_all_devices)
        devices_layout.addWidget(self.connect_all_button)

        #mitutoyo
        self.mitutoyo_group = QtWidgets.QGroupBox("Mitutoyo Height Gauge")
        mitutoyo_layout = QtWidgets.QVBoxLayout()
        self.mitutoyo_group.setLayout(mitutoyo_layout)

        self.mitutoyo_status_label = QtWidgets.QLabel("Status: Disconnected")
        self.mitutoyo_height_label = QtWidgets.QLabel("Current height: -- mm")

        self.mitutoyo_connect_button = QtWidgets.QPushButton("Connect Mitutoyo")

        mitutoyo_layout.addWidget(self.mitutoyo_status_label)
        mitutoyo_layout.addWidget(self.mitutoyo_height_label)
        mitutoyo_layout.addWidget(self.mitutoyo_connect_button)

        self.mitutoyo_connect_button.clicked.connect(
            self.connect_mitutoyo
            )

        devices_layout.addWidget(self.mitutoyo_group)
        
        #normal SR830
        self.normal_lockin_group = QtWidgets.QGroupBox("Normal SR830")
        normal_layout = QtWidgets.QVBoxLayout()
        self.normal_lockin_group.setLayout(normal_layout)

        self.normal_lockin_status_label = QtWidgets.QLabel("Status: Disconnected")
        self.normal_lockin_amplitude_label = QtWidgets.QLabel("Amplitude: -- V")
        self.normal_lockin_phase_label = QtWidgets.QLabel("Phase: -- °")
        self.normal_lockin_connect_button = QtWidgets.QPushButton("Connect Lock in - Normal")
        
        normal_layout.addWidget(self.normal_lockin_status_label)
        normal_layout.addWidget(self.normal_lockin_amplitude_label)
        normal_layout.addWidget(self.normal_lockin_phase_label)
        normal_layout.addWidget(self.normal_lockin_connect_button)
        
        self.normal_lockin_connect_button.clicked.connect(self.connect_normal_lockin)
        
        devices_layout.addWidget(self.normal_lockin_group)

        #shear SR830
        self.shear_lockin_group = QtWidgets.QGroupBox("Shear SR830")
        shear_layout = QtWidgets.QVBoxLayout()
        self.shear_lockin_group.setLayout(shear_layout)

        self.shear_lockin_status_label = QtWidgets.QLabel("Status: Disconnected")
        self.shear_lockin_amplitude_label = QtWidgets.QLabel("Amplitude: -- V")
        self.shear_lockin_phase_label = QtWidgets.QLabel("Phase: -- °")
        self.shear_lockin_connect_button = QtWidgets.QPushButton("Connect Lock in - Shear")

        shear_layout.addWidget(self.shear_lockin_status_label)
        shear_layout.addWidget(self.shear_lockin_amplitude_label)
        shear_layout.addWidget(self.shear_lockin_phase_label)
        shear_layout.addWidget(self.shear_lockin_connect_button)
        
        self.shear_lockin_connect_button.clicked.connect(self.connect_shear_lockin)
        devices_layout.addWidget(self.shear_lockin_group)

        #temperature logger
        self.temperature_group = QtWidgets.QGroupBox("PL-125-T2 Temperature Logger")
        temperature_layout = QtWidgets.QVBoxLayout()
        self.temperature_group.setLayout(temperature_layout)

        self.temperature_status_label = QtWidgets.QLabel("Status: Disconnected")
        self.temperature_t1_label = QtWidgets.QLabel("T1: -- °C")
        self.temperature_t2_label = QtWidgets.QLabel("T2: -- °C")
        self.temperature_connect_button = QtWidgets.QPushButton("Connect Temperature")

        temperature_layout.addWidget(self.temperature_status_label)
        temperature_layout.addWidget(self.temperature_t1_label)

        temperature_layout.addWidget(self.temperature_t2_label)
        temperature_layout.addWidget(self.temperature_connect_button)
        self.temperature_connect_button.clicked.connect(self.connect_temperature_logger)
        devices_layout.addWidget(self.temperature_group)

        #rigol function generator
        self.rigol_group = QtWidgets.QGroupBox("Rigol Function Generator")

        rigol_layout = QtWidgets.QVBoxLayout()
        self.rigol_group.setLayout(rigol_layout)
       
        self.rigol_status_label = QtWidgets.QLabel("Status: Disconnected")

        self.rigol_normal_frequency_label = QtWidgets.QLabel("Normal frequency: -- Hz")
        self.rigol_shear_frequency_label = QtWidgets.QLabel("Shear frequency: -- Hz")
        self.rigol_ch1_output_label = QtWidgets.QLabel("CH1 output: Off")

        self.rigol_ch2_output_label = QtWidgets.QLabel("CH2 output: Off")
        self.rigol_connect_button = QtWidgets.QPushButton("Connect Rigol")

        rigol_layout.addWidget(self.rigol_status_label)
        rigol_layout.addWidget(self.rigol_normal_frequency_label)
        rigol_layout.addWidget(self.rigol_shear_frequency_label)
        rigol_layout.addWidget(self.rigol_ch1_output_label)
        rigol_layout.addWidget(self.rigol_ch2_output_label)
        rigol_layout.addWidget(self.rigol_connect_button)

        self.rigol_connect_button.clicked.connect(self.connect_rigol)
        devices_layout.addWidget(self.rigol_group)

        #piezo controller

        self.piezo_group = QtWidgets.QGroupBox("PI E-625 Piezo Controller")

        piezo_layout = QtWidgets.QVBoxLayout()
        self.piezo_group.setLayout(piezo_layout)

        self.piezo_status_label = QtWidgets.QLabel("Status: Disconnected")
        self.piezo_voltage_label = QtWidgets.QLabel("Current voltage: -- V")
        self.piezo_connect_button = QtWidgets.QPushButton("Connect PI E-625")

        piezo_layout.addWidget(self.piezo_status_label)
        piezo_layout.addWidget(self.piezo_voltage_label)
        piezo_layout.addWidget(self.piezo_connect_button)

        self.piezo_connect_button.clicked.connect(self.connect_piezo)
        devices_layout.addWidget(self.piezo_group)

        #calibration tab
        calibration_layout = QtWidgets.QVBoxLayout()
        self.calibration_tab.setLayout(calibration_layout)

        self.air_calibration_group = QtWidgets.QGroupBox("Air Calibration")
        
        air_layout = QtWidgets.QVBoxLayout()
        self.air_calibration_group.setLayout(air_layout)

        #air calibration inputs
        self.start_frequency_input = QtWidgets.QDoubleSpinBox()
        self.start_frequency_input.setRange(1.0, 10000.0)
        self.start_frequency_input.setDecimals(3)
        self.start_frequency_input.setValue(796.0)
        self.start_frequency_input.setSuffix(" Hz")

        self.stop_frequency_input = QtWidgets.QDoubleSpinBox()
        self.stop_frequency_input.setRange(1.0, 10000.0)
        self.stop_frequency_input.setDecimals(3)
        self.stop_frequency_input.setValue(803.0)
        self.stop_frequency_input.setSuffix(" Hz")

        self.points_input = QtWidgets.QSpinBox()
        self.points_input.setRange(2, 1000)
        self.points_input.setValue(50)

        self.drive_amplitude_input = QtWidgets.QDoubleSpinBox()
        self.drive_amplitude_input.setRange(0.0, 1.0)
        self.drive_amplitude_input.setDecimals(3)
        self.drive_amplitude_input.setSingleStep(0.005)
        self.drive_amplitude_input.setValue(0.010)
        self.drive_amplitude_input.setSuffix(" V")

        self.start_air_calibration_button = QtWidgets.QPushButton("Start Air Calibration")

        self.autoscale_checkbox = QtWidgets.QCheckBox("Autoscale amplitude")
        self.autoscale_checkbox.setChecked(True)

        self.test_frequency_input = QtWidgets.QDoubleSpinBox()
        self.test_frequency_input.setRange(1.0, 10000.0)
        self.test_frequency_input.setDecimals(3)
        self.test_frequency_input.setValue(800.0)
        self.test_frequency_input.setSuffix(" Hz")

        self.send_test_signal_button = QtWidgets.QPushButton("Send test signal")
        self.test_amplitude_label = QtWidgets.QLabel("Measured amplitude: -- V")
        self.test_phase_label = QtWidgets.QLabel("Measured phase: -- °")

        air_layout.addWidget(QtWidgets.QLabel("Test frequency:"))
        air_layout.addWidget(self.test_frequency_input)

        air_layout.addWidget(self.send_test_signal_button)
        air_layout.addWidget(self.test_amplitude_label)
        air_layout.addWidget(self.test_phase_label)

        air_layout.addWidget(QtWidgets.QLabel("Drive amplitude:"))
        air_layout.addWidget(self.drive_amplitude_input)

        air_layout.addWidget(QtWidgets.QLabel("Start frequency:"))
        air_layout.addWidget(self.start_frequency_input)

        air_layout.addWidget(QtWidgets.QLabel("Start frequency:"))
        air_layout.addWidget(self.start_frequency_input)
        air_layout.addWidget(QtWidgets.QLabel("Stop frequency:"))
        air_layout.addWidget(self.stop_frequency_input)
        air_layout.addWidget(QtWidgets.QLabel("Number of points:"))
        air_layout.addWidget(self.points_input)

        air_layout.addWidget(self.start_air_calibration_button)

        self.send_test_signal_button.clicked.connect(self.send_test_signal)
        #test
        #self.send_test_signal_button.clicked.connect(self.test_rigol_output)
                
        calibration_layout.addWidget(self.air_calibration_group)
        calibration_layout.addStretch()
        calibration_layout.addWidget(self.autoscale_checkbox)

        self.start_air_calibration_button.clicked.connect(self.start_air_calibration)

        #tabs
        devices_layout.addStretch()
        
        self.tabs.addTab(self.devices_tab, "Devices")
        self.tabs.addTab(self.calibration_tab, "Calibration")
        self.tabs.addTab(self.live_tab, "Live data")

        main_layout.addWidget(self.tabs)

        #start/stop buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.start_button = QtWidgets.QPushButton("Start measurement")
        self.stop_button = QtWidgets.QPushButton("Stop measurement")
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        main_layout.addLayout(button_layout)

        #status
        self.status_label = QtWidgets.QLabel("Status: Ready")
        main_layout.addWidget(self.status_label)

        #timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)

        #connect buttons
        self.start_button.clicked.connect(self.start_measurement)
        self.stop_button.clicked.connect(self.stop_measurement)

        #stop button off at start
        self.stop_button.setEnabled(False)
 #defs
    def plot_air_calibration(self, result):
        frequencies = result["frequencies"]
        amplitudes = result["amplitudes"]
        phases = result["phases"]
        f0 = result["f0"]

        fig1, ax1 = plt.subplots()

        ax1.plot(
            frequencies,
            amplitudes,
            marker=".",
            label="Measured response"
        )

        ax1.axvline(
            f0,
            linestyle="--",
            label=f"f0 = {f0:.2f} Hz"
        )

        ax1.set_xlabel("Frequency (Hz)")
        ax1.set_ylabel("Amplitude (V)")
        ax1.set_title("Normal tuning fork frequency response")

        ax1.grid(True)
        ax1.legend()

        # Autoscale checkbox
        if self.autoscale_checkbox.isChecked():
            ax1.relim()
            ax1.autoscale_view()

        else:
            ax1.set_ylim(0, 0.20)

        # -------------------------------------------------
        # Phase plot
        # -------------------------------------------------

        fig2, ax2 = plt.subplots()

        ax2.plot(
            frequencies,
            phases,
            marker=".",
            label="Measured phase"
        )

        ax2.axhline(
            0,
            linestyle="--"
        )

        ax2.axvline(
            f0,
            linestyle="--",
            label=f"f0 = {f0:.2f} Hz"
        )

        ax2.set_xlabel("Frequency (Hz)")
        ax2.set_ylabel("Phase (degrees)")
        ax2.set_title("Normal tuning fork phase response")

        ax2.grid(True)
        ax2.legend()

        plt.show()

   
    def start_air_calibration(self):
    #check devices
        if self.rigol is None or not self.rigol.is_connected():
            print("Rigol is not connected.")
            return

        if (self.normal_lockin is None
            or not self.normal_lockin.is_connected()):

            print("Normal SR830 is not connected.")
            return

        if (self.shear_lockin is None
            or not self.shear_lockin.is_connected()):

            print("Shear SR830 is not connected.")
            return

        # Set normal SR830 sine-out amplitude
        drive_amplitude = self.drive_amplitude_input.value()
        self.normal_lockin.set_sine_out_amplitude(drive_amplitude)
        print(f"Normal drive amplitude set to {drive_amplitude:.3f} V")
        
        #stop normal live measurement during calibration
        if self.timer.isActive():
            self.timer.stop()

        self.status_label.setText("Status: Air calibration")

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)

        start_frequency = self.start_frequency_input.value()
        stop_frequency = self.stop_frequency_input.value()

        #configure Rigol like original calibration code
        self.rigol.set_waveform(1, "SIN")
        self.rigol.set_waveform(2, "SIN")

        self.rigol.set_output(1, True)
        self.rigol.set_output(2, True)

        #starting positions
        self.rigol.set_frequency(1, (start_frequency + stop_frequency) / 2)

        self.rigol.set_frequency(2, 460.0)

        try:

            result = calibrateAir(
                ctrlNormal=self.normal_lockin,
                ctrlShear=self.shear_lockin,
                freqGen=self.rigol.device,

                freqNormalRange=[
                    start_frequency,
                    stop_frequency
                ],

                freqShearRange=[
                    450.0,
                    470.0
                ],)

            print("Calibration result:", result)

            self.plot_air_calibration(result)

            self.status_label.setText("Status: Air calibration finished")

        except Exception as error:

            print("Air calibration error:", error)

            self.status_label.setText("Status: Air calibration failed")

        finally:

            self.normal_lockin.set_sine_out_amplitude(0.0)

            self.rigol.set_output(1, False)
            self.rigol.set_output(2, False)

            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        
        '''
        for frequency in frequencies:

            self.rigol.set_frequency(1, frequency) #rigol CH1
            time.sleep(0.5) #geef rigol tijd om te reageren

            amplitude = self.normal_lockin.read_amplitude()
            phase = self.normal_lockin.read_phase()

            measured_amplitudes.append(amplitude)
            measured_phases.append(phase)

            print(
                f"{frequency:.3f} Hz -> "
                f"Amplitude: {amplitude:.6f} V, "
                f"Phase: {phase:.2f} °")
        '''
        self.status_label.setText("Status: Air calibration finished")

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def send_test_signal(self):

        if self.rigol is None or not self.rigol.is_connected():
            print("Rigol is not connected.")
            return

        if (self.normal_lockin is None
            or not self.normal_lockin.is_connected()):

            print("Normal SR830 is not connected.")
            return

        #test1234
        self.normal_lockin.set_sine_out_amplitude(0.1)

        print("Rigol CH1 amplitude setting:",self.rigol.get_amplitude(1))
        print("Rigol CH2 amplitude setting:", self.rigol.get_amplitude(2))

        frequency = self.test_frequency_input.value()
        #CH1 aan
        self.rigol.set_output(1, True)

        #frequentie instellen
        self.rigol.set_frequency(1, frequency)
        
        #amp instellen #test
        self.rigol.set_amplitude(1, 1.5)

        print(
            "CH1 output:",
            self.rigol.get_output_state(1)
        )

        # even wachten tot het signaal/sturing is gestabiliseerd
        time.sleep(2)

        amplitude = self.normal_lockin.read_amplitude()
        phase = self.normal_lockin.read_phase()

        self.test_amplitude_label.setText(f"Measured amplitude: {amplitude:.6f} V")
        self.test_phase_label.setText(f"Measured phase: {phase:.2f} °")

        print(
            f"f={frequency:.3f} Hz | "
            f"A={amplitude:.9f} V | "
            f"phase={phase:.3f}°"
        )

        # CH1 weer uit na de test
        self.rigol.set_output(1, False)
        

    def test_rigol_output(self):

        frequency = 799.7

        self.rigol.set_frequency(
            1,
            frequency
        )

        # -------------------------
        # Output OFF
        # -------------------------
        self.rigol.set_output(1, False)

        time.sleep(2)

        amplitude_off = self.normal_lockin.read_amplitude()
        phase_off = self.normal_lockin.read_phase()

        print(
            "OFF:",
            amplitude_off,
            phase_off
        )

        # -------------------------
        # Output ON
        # -------------------------
        self.rigol.set_output(1, True)

        time.sleep(2)

        amplitude_on = self.normal_lockin.read_amplitude()
        phase_on = self.normal_lockin.read_phase()

        print(
            "ON:",
            amplitude_on,
            phase_on
        )

        # -------------------------
        # Output OFF again
        # -------------------------
        self.rigol.set_output(1, False)

        time.sleep(2)

        amplitude_off_again = self.normal_lockin.read_amplitude()
        phase_off_again = self.normal_lockin.read_phase()

        print(
            "OFF again:",
            amplitude_off_again,
            phase_off_again
        )
    def connect_all_devices(self):

        self.connect_mitutoyo()
        self.connect_normal_lockin()
        self.connect_shear_lockin()
        self.connect_temperature_logger()
        self.connect_rigol()
        self.connect_piezo()

        all_connected = (
            self.mitutoyo is not None
            and self.mitutoyo.is_connected()
            and self.normal_lockin is not None
            and self.normal_lockin.is_connected()
            and self.shear_lockin is not None
            and self.shear_lockin.is_connected()
            and self.temperature_logger is not None
            and self.temperature_logger.is_connected()
            and self.rigol is not None
            and self.rigol.is_connected()
            and self.piezo is not None
            and self.piezo.is_connected())

        if all_connected:

            self.connect_all_button.setText("All Devices Connected")
            self.connect_all_button.setStyleSheet("color: green; font-weight: bold;")

    def connect_mitutoyo(self):

        if self.mitutoyo is not None and self.mitutoyo.is_connected():
            self.mitutoyo_status_label.setText("Status: Connected")
            return

        try:
            self.mitutoyo = Mitutoyo()

            self.mitutoyo_status_label.setText("Status: Connected")

            self.mitutoyo_connect_button.setText("Mitutoyo Connected")
            self.mitutoyo_connect_button.setStyleSheet("color: green; font-weight: bold;")
            self.mitutoyo_connect_button.setEnabled(False)

            height = self.mitutoyo.measurement()

            self.mitutoyo_height_label.setText(f"Current height: {height:.3f} mm")

        except Exception as error:

            self.mitutoyo_status_label.setText("Status: Connection failed")

            print("Mitutoyo connection error:", error)

    def connect_piezo(self):

        if (
            self.piezo is not None
            and self.piezo.is_connected()
        ):
            return

        try:
            self.piezo = PIE625()

            self.piezo_status_label.setText("Status: Connected")
            self.piezo_connect_button.setText("PI E-625 Connected")
            self.piezo_connect_button.setStyleSheet("color: green; font-weight: bold;")
            self.piezo_connect_button.setEnabled(False)

            voltage = self.piezo.get_voltage()

            self.piezo_voltage_label.setText(
                f"Current voltage: {voltage:.3f} V"
            )

        except Exception as error:

            self.piezo_status_label.setText("Status: Connection failed")

            print("PI E-625 connection error:", error)

    def connect_rigol(self):

        if (self.rigol is not None
            and self.rigol.is_connected()):
            return

        try:
            self.rigol = Rigol()
            self.rigol_status_label.setText("Status: Connected")
            self.rigol_connect_button.setText(" Rigol Connected")
            self.rigol_connect_button.setStyleSheet("color: green; font-weight: bold;")
            self.rigol_connect_button.setEnabled(False)

        except Exception as error:

            self.rigol_status_label.setText("Status: Connection failed")
            print("Rigol connection error:", error)

    def connect_temperature_logger(self):

        if (
            self.temperature_logger is not None
            and self.temperature_logger.is_connected()
        ):
            return

        try:
            self.temperature_logger = PL125T2()

            self.temperature_status_label.setText("Status: Connected")
            self.temperature_connect_button.setText("Temperature Connected")
            self.temperature_connect_button.setStyleSheet("color: green; font-weight: bold;")
            self.temperature_connect_button.setEnabled(False)
            t1, t2 = self.temperature_logger.read_temperature()

            if t1 is not None:
                self.temperature_t1_label.setText(f"T1: {t1:.1f} °C")
            if t2 is not None:
                self.temperature_t2_label.setText(f"T2: {t2:.1f} °C")

        except Exception as error:

            self.temperature_status_label.setText("Status: Connection failed")

            print("Temperature logger connection error:", error)

    def connect_normal_lockin(self):

        if (
            self.normal_lockin is not None
            and self.normal_lockin.is_connected()
            ):

            return

        try:
            self.normal_lockin = SR830("A9JSTXTQA")
            self.normal_lockin_status_label.setText("Status: Connected")
            self.normal_lockin_connect_button.setText("Lock in - Normal Connected")
            self.normal_lockin_connect_button.setStyleSheet("color: green; font-weight: bold;")
            self.normal_lockin_connect_button.setEnabled(False)

        except Exception as error:

            self.normal_lockin_status_label.setText(
                "Status: Connection failed")

            print(
                "Normal SR830 connection error:",
                error)

    def connect_shear_lockin(self):

        if (
            self.shear_lockin is not None
            and self.shear_lockin.is_connected()
        ):
            return

        try:
            self.shear_lockin = SR830("A9TQAG5OA")
            self.shear_lockin_status_label.setText("Status: Connected")
            self.shear_lockin_connect_button.setText("Lock in - Shear Connected")
            self.shear_lockin_connect_button.setStyleSheet("color: green; font-weight: bold;")
            self.shear_lockin_connect_button.setEnabled(False)

        except Exception as error:

            self.shear_lockin_status_label.setText(
                "Status: Connection failed")

            print(
                "Shear SR830 connection error:",
            error)
    

    def start_measurement(self):

        self.status_label.setText("Status: Measuring")

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.timer.start(1000)

    def stop_measurement(self):

        self.timer.stop()

        self.status_label.setText("Status: Stopped")

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_data(self):

        #fake data
        q_factor = random.uniform(1200, 1300)

        #default values
        height = None
        normal_amplitude = None
        normal_phase = None
        shear_amplitude = None
        shear_phase = None
        temperature_t1 = None
        temperature_t2 = None
        frequency = None
        normal_frequency = None
        shear_frequency = None
        piezo_voltage = None

        #devices for live data
        #------------------------------------

        #mitutoyo
        if self.mitutoyo is not None and self.mitutoyo.is_connected():
            height = self.mitutoyo.measurement()

        #normal SR830
        if (
            self.normal_lockin is not None
            and self.normal_lockin.is_connected()
        ):
            normal_amplitude = self.normal_lockin.read_amplitude()
            normal_phase = self.normal_lockin.read_phase()

        #shear SR830
        if (
            self.shear_lockin is not None
            and self.shear_lockin.is_connected()
        ):
            shear_amplitude = self.shear_lockin.read_amplitude()
            shear_phase = self.shear_lockin.read_phase()

        #temperatuur
        if (
            self.temperature_logger is not None
            and self.temperature_logger.is_connected()
            
        ):
        
            temperature_t1, temperature_t2 = (self.temperature_logger.read_temperature())

        #rigol
        if self.rigol is not None and self.rigol.is_connected():

            normal_frequency = self.rigol.get_frequency(1)
            shear_frequency = self.rigol.get_frequency(2)

            #CH1 = normal mode - used for now
            frequency = normal_frequency
            self.rigol_normal_frequency_label.setText(f"Normal frequency: {normal_frequency:.3f} Hz")

            self.rigol_shear_frequency_label.setText(f"Shear frequency: {shear_frequency:.3f} Hz")

            ch1_on = self.rigol.get_output_state(1)
            ch2_on = self.rigol.get_output_state(2)

            self.rigol_ch1_output_label.setText(f"CH1 output: {'On' if ch1_on else 'Off'}")

            self.rigol_ch2_output_label.setText(f"CH2 output: {'On' if ch2_on else 'Off'}")

        #PIE-625
        if (
            self.piezo is not None
            and self.piezo.is_connected()
        ):
            piezo_voltage = self.piezo.get_voltage()

   
        #main live values
        #---------------------------------
        if piezo_voltage is not None:

            self.piezo_voltage_label.setText(
                f"Current voltage: {piezo_voltage:.3f} V"
            )

        else:

            self.piezo_voltage_label.setText(
                "Current voltage: -- V"
            )        

        
        if temperature_t1 is not None:

            self.temperature_label.setText(
                f"Temperature (Real): {temperature_t1:.1f} °C"
            )

            self.temperature_t1_label.setText(
                f"T1: {temperature_t1:.1f} °C"
            )

        else:

            self.temperature_label.setText(
                "Temperature (Real): -- °C"
            )

            self.temperature_t1_label.setText(
                "T1: -- °C"
            )

        if temperature_t2 is not None:

            self.temperature_t2_label.setText(
                f"T2: {temperature_t2:.1f} °C"
            )

        else:

            self.temperature_t2_label.setText(
                "T2: -- °C"
            )

        #rigol
        if frequency is not None:
            self.frequency_label.setText(
                f"Frequency (Real): {frequency:.3f} Hz"
            )
        else:
            self.frequency_label.setText(
                "Frequency (Real): -- Hz"
    )

        self.q_label.setText(
            f"Q-factor (Fake): {q_factor:.1f}"
        )

    
        #height
        if height is not None:

            self.height_label.setText(
                f"Height (Real): {height:.3f} mm"
            )

            self.mitutoyo_height_label.setText(
                f"Current height: {height:.3f} mm"
            )

        else:

            self.height_label.setText(
                "Height (Real): -- mm"
            )

            self.mitutoyo_height_label.setText(
                "Current height: -- mm"
            )

        #normal amplitude + phase
        if normal_amplitude is not None:

            self.amplitude_label.setText(
                f"Amplitude (Real): {normal_amplitude:.6f} V"
            )

            self.phase_label.setText(
                f"Phase (Real): {normal_phase:.2f} °"
            )

            self.normal_lockin_amplitude_label.setText(
                f"Amplitude: {normal_amplitude:.6f} V"
            )

            self.normal_lockin_phase_label.setText(
                f"Phase: {normal_phase:.2f} °"
            )

        else:

            self.amplitude_label.setText(
                "Amplitude (Real): -- V"
            )

            self.phase_label.setText(
                "Phase (Real): -- °"
            )

            self.normal_lockin_amplitude_label.setText(
                "Amplitude: -- V"
            )

            self.normal_lockin_phase_label.setText(
                "Phase: -- °"
            )

        #shear amplitude + phase
        if shear_amplitude is not None:

            self.shear_lockin_amplitude_label.setText(
                f"Amplitude: {shear_amplitude:.6f} V"
            )

            self.shear_lockin_phase_label.setText(
                f"Phase: {shear_phase:.2f} °"
            )

        else:

            self.shear_lockin_amplitude_label.setText(
                "Amplitude: -- V"
            )

            self.shear_lockin_phase_label.setText(
                "Phase: -- °"
            )

def main():

    app = QtWidgets.QApplication(sys.argv)

    ui = UserInterface()
    ui.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()