import sys
import requests
import os
import datetime # For greeting
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QGraphicsDropShadowEffect, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QSize
from PyQt5.QtGui import QColor, QMovie, QPixmap, QPalette, QBrush
from PyQt5.QtGui import QIcon

load_dotenv()

class WeatherWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, city, api_key):
        super().__init__()
        self.city = city
        self.api_key = api_key

    def run(self):
        url = f"https://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.api_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data['cod'] == 200:
                self.finished.emit(data)
            else:
                self.error.emit(data.get("message", "Unknown Error"))
        except requests.exceptions.HTTPError:
            match response.status_code:
                case 400: self.error.emit("Bad request\nPlease Check Your Input")
                case 401: self.error.emit("Unauthorized\nCheck Your API Key")
                case 403: self.error.emit("Forbidden\nCheck Your API Key")
                case 404: self.error.emit("Not Found\nCity Not Found")
                case 500: self.error.emit("Internal Server Error\nTry Again Later")
                case 502: self.error.emit("Bad Gateway\nTry Again Later")
                case 503: self.error.emit("Service Unavailable\nTry Again Later")
                case 504: self.error.emit("Gateway Timeout\nTry Again Later")
                case _: self.error.emit("Unknown Error")
        except requests.exceptions.ConnectionError:
            self.error.emit("Connection Error\nCheck Your Internet Connection")
        except requests.exceptions.Timeout:
            self.error.emit("Timeout Error\nTry Again Later")
        except requests.exceptions.RequestException:
            self.error.emit("An Error Occurred\nPlease Try Again")
        except requests.exceptions.TooManyRedirects:
            self.error.emit("Too Many Redirects\nPlease Try Again Later")
        except Exception as e:
            self.error.emit(f"An unexpected error occurred: {e}")

class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Weather App")
        self.setGeometry(100, 100, 450, 650)

        # Background Animation Label
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, 450, 650)
        self.background_label.setScaledContents(True)
        self.current_movie = None
        
        # Set default background
        self.set_background_movie("assets/backgrounds/default.gif")

        # Main Layout (Centering the card)
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        self.setLayout(main_layout)

        # Weather Card
        self.card = QFrame()
        self.card.setObjectName("Card")
        self.card.setFixedSize(400, 600)
        
        # Card Layout
        card_layout = QGridLayout(self.card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(25, 25, 25, 25)

        # Drop Shadow for Card
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.card.setGraphicsEffect(shadow)

        # Greeting
        self.greeting_label = QLabel(self.get_greeting())
        self.greeting_label.setObjectName("Greeting")
        self.greeting_label.setAlignment(Qt.AlignCenter)

        # Title
        title = QLabel("Weather App")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)

        # Input Field & Button Layout
        input_layout = QHBoxLayout()
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Enter City Name")
        
        self.get_weather_button = QPushButton("Check Weather 🌦")
        self.get_weather_button.setCursor(Qt.PointingHandCursor)

        input_layout.addWidget(self.city_input)
        input_layout.addWidget(self.get_weather_button)

        # Weather Info Container (To be animated)
        self.weather_container = QFrame()
        self.weather_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        weather_layout = QVBoxLayout(self.weather_container)
        weather_layout.setAlignment(Qt.AlignCenter)
        weather_layout.setSpacing(5)

        # Icon Label
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(120, 120) 
        self.icon_label.setScaledContents(True)

        # Temperature Label
        self.temperature = QLabel()
        self.temperature.setObjectName("Temperature")
        self.temperature.setAlignment(Qt.AlignCenter)

        # Description Label
        self.description_label = QLabel()
        self.description_label.setObjectName("Description")
        self.description_label.setAlignment(Qt.AlignCenter)
        
        # Friendly Message Label
        self.message_label = QLabel()
        self.message_label.setObjectName("Message")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)

        # Extended Detail Grid (Humidity, Wind, etc)
        self.details_frame = QFrame()
        self.details_grid = QGridLayout(self.details_frame)
        self.details_grid.setSpacing(10)

        # Placeholders for details
        self.lbl_humidity = QLabel("Humidity: --%")
        self.lbl_wind = QLabel("Wind: -- m/s")
        self.lbl_pressure = QLabel("Pressure: -- hPa")
        self.lbl_feels_like = QLabel("Feels Like: --°C")
        
        for lbl in [self.lbl_humidity, self.lbl_wind, self.lbl_pressure, self.lbl_feels_like]:
            lbl.setObjectName("DetailLabel")
            lbl.setAlignment(Qt.AlignCenter)
        
        self.details_grid.addWidget(self.lbl_feels_like, 0, 0)
        self.details_grid.addWidget(self.lbl_humidity, 0, 1)
        self.details_grid.addWidget(self.lbl_wind, 1, 0)
        self.details_grid.addWidget(self.lbl_pressure, 1, 1)

        # Loading Spinner
        self.loading_label = QLabel(self.card)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.resize(100, 100)
        self.loading_movie = QMovie("assets/loading.gif")
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setVisible(False)
        self.loading_movie.setScaledSize(self.loading_label.size())

        # Add widgets to weather layout
        # Using a centralized VBox for main info
        info_vbox = QVBoxLayout()
        info_vbox.setAlignment(Qt.AlignCenter)
        info_vbox.addWidget(self.icon_label)
        info_vbox.addWidget(self.temperature)
        info_vbox.addWidget(self.description_label)
        info_vbox.addWidget(self.message_label)
        
        # Center horizontally
        # Just add directly to grid for better control or nested VBox
        weather_layout.addLayout(info_vbox)
        weather_layout.addWidget(self.details_frame)


        # Add everything to card layout using Grid coordinates
        # Greeting
        card_layout.addWidget(self.greeting_label, 0, 0, 1, 2, alignment=Qt.AlignCenter)
        # Title
        # card_layout.addWidget(title, 1, 0, 1, 2, alignment=Qt.AlignCenter) # Optional if Greeting is enough
        
        # Input row
        card_layout.addLayout(input_layout, 1, 0, 1, 2)
        
        # Loading spinner
        card_layout.addWidget(self.loading_label, 2, 0, 1, 2, alignment=Qt.AlignCenter)
        
        # Weather container
        card_layout.addWidget(self.weather_container, 3, 0, 1, 2)
        
        # Push content up/center by adding stretch
        card_layout.setRowStretch(3, 1)

        main_layout.addWidget(self.card)

        # Styling
        self.apply_styles()

        # Connect Button
        self.get_weather_button.clicked.connect(self.get_weather)
        self.city_input.returnPressed.connect(self.get_weather)

        # Initial State
        self.weather_container.hide()

    def resizeEvent(self, event):
        # Keep background label covering the whole window
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def set_background_movie(self, gif_path):
        if not os.path.exists(gif_path):
            return
        
        if self.current_movie:
            self.current_movie.stop()
            
        self.current_movie = QMovie(gif_path)
        self.background_label.setMovie(self.current_movie)
        self.current_movie.start()
        self.background_label.lower() # Ensure it stays behind everything inside the Window but wait..
        # Since self.card is added to main_layout which is on self (WeatherApp), 
        # and background_label is children of self.
        # layout items are usually drawn on top.
        # To strictly ensure background is behind, we might need to ensure stacking order.
        self.background_label.lower() 

    def get_greeting(self):
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            return "Good Morning ☀️"
        elif 12 <= hour < 18:
            return "Good Afternoon 🌤"
        else:
            return "Good Evening 🌙"

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', sans-serif;
            }
            QFrame#Card {
                background-color: rgba(20, 20, 30, 0.75); 
                border-radius: 25px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QLabel#Greeting {
                font-size: 24px;
                font-weight: 600;
                color: #ffffff;
                margin-bottom: 10px;
                background: transparent;
            }
            QLabel#Title {
                font-size: 20px;
                font-weight: bold;
                color: #dddddd;
                background: transparent;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 10px 15px;
                color: white;
                font-size: 16px;
            }
            QLineEdit:focus {
                border: 2px solid #4facfe;
                background-color: rgba(255, 255, 255, 0.15);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4facfe, stop:1 #00f2fe);
                color: #ffffff;
                border-radius: 15px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 15px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #43e97b, stop:1 #38f9d7);
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #0083b0;
                margin-top: 2px;
            }
            QLabel#Temperature {
                font-size: 56px;
                font-weight: 300;
                color: white;
                background: transparent;
            }
            QLabel#Description {
                font-size: 22px;
                color: #e0e0e0;
                font-style: italic;
                background: transparent;
                text-transform: capitalize;
                margin-bottom: 5px;
            }
            QLabel#Message {
                font-size: 16px;
                color: #aaddff;
                font-weight: bold;
                background: transparent;
            }
            QLabel#DetailLabel {
                font-size: 14px;
                color: #cccccc;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 5px;
            }
            QLabel {
                background: transparent; 
            }
        """)

    def get_weather(self):
        city = self.city_input.text().strip()
        if not city:
            return

        api_key = os.getenv("API_KEY")
        if not api_key:
            self.display_error("API Key Missing")
            return

        # UI State: Loading
        self.weather_container.hide()
        self.loading_label.setVisible(True)
        self.loading_movie.start()
        self.get_weather_button.setEnabled(False)
        self.city_input.setEnabled(False)
        
        # Reset background to default while loading?? Optional. 
        # self.set_background_movie("assets/backgrounds/default.gif")

        # Worker Thread
        self.worker = WeatherWorker(city, api_key)
        self.worker.finished.connect(self.handle_response)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def handle_response(self, data):
        self.stop_loading()
        self.display_weather(data)

    def handle_error(self, message):
        self.stop_loading()
        self.display_error(message)

    def stop_loading(self):
        self.loading_movie.stop()
        self.loading_label.setVisible(False)
        self.get_weather_button.setEnabled(True)
        self.city_input.setEnabled(True)

    def display_error(self, message):
        self.temperature.setText("")
        self.description_label.setText(message)
        self.icon_label.clear()
        self.message_label.clear()
        self.details_frame.hide() # Hide details on error
        self.weather_container.show()
        self.fade_in_animation()

    def display_weather(self, data):
        # Basic Data
        temp_k = data['main']['temp']
        temp_c = temp_k - 273.15
        temp_f = (temp_k * 9/5) - 459.67
        description = data['weather'][0]['description']
        weather_id = data['weather'][0]['id']
        
        # Extended Data
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']
        wind_speed = data['wind']['speed']
        feels_like_k = data['main']['feels_like']
        feels_like_c = feels_like_k - 273.15

        # Update Labels
        self.temperature.setText(f"{temp_c:.0f}°C")
        self.description_label.setText(description)
        self.lbl_humidity.setText(f"💧 Humidity: {humidity}%")
        self.lbl_wind.setText(f"🌬 Wind: {wind_speed} m/s")
        self.lbl_pressure.setText(f"🌡 Pressure: {pressure} hPa")
        self.lbl_feels_like.setText(f"🤔 Feels Like: {feels_like_c:.0f}°C")
        
        self.details_frame.show()

        # Update Icon
        icon_path = self.get_weather_icon_path(weather_id)
        if os.path.exists(icon_path):
             pixmap = QPixmap(icon_path)
             self.icon_label.setPixmap(pixmap)
        else:
             self.icon_label.setText("No Icon")

        # Update Background & Friendly Message
        self.update_environment(weather_id)

        self.weather_container.show()
        self.fade_in_animation()

    def update_environment(self, weather_id):
        # Determine background and message
        bg_file = "assets/backgrounds/default.gif"
        message = ""

        if 200 <= weather_id <= 232: 
            bg_file = "assets/backgrounds/rainy.gif" # Thunder uses rain bg for now
            message = "Stay safe! There's a thunderstorm outside. ⛈️"
        elif 300 <= weather_id <= 531: 
            bg_file = "assets/backgrounds/rainy.gif"
            message = "Don't forget your umbrella! ☔"
        elif 600 <= weather_id <= 622: 
            bg_file = "assets/backgrounds/default.gif" # Snow (using default for now, could act cloudy)
            message = "It's freezing! Wear a warm coat. ❄️"
        elif 700 <= weather_id <= 781: 
            bg_file = "assets/backgrounds/cloudy.gif" # Mist/Fog
            message = "Visibility is low, drive carefully! 🌫"
        elif weather_id == 800: 
            bg_file = "assets/backgrounds/sunny.gif"
            message = "It's a beautiful day! Enjoy the sun. ☀️"
        elif 801 <= weather_id <= 804: 
            bg_file = "assets/backgrounds/cloudy.gif"
            message = "A bit cloudy today. Good weather for a walk. ☁️"
        
        self.set_background_movie(bg_file)
        self.message_label.setText(message)

    def get_weather_icon_path(self, weather_id):
        # Using the assets generated by generate_assets.py
        if 200 <= weather_id <= 232: return "assets/icons/thunder.png"
        if 300 <= weather_id <= 321: return "assets/icons/rain.png" # Drizzle
        if 500 <= weather_id <= 531: return "assets/icons/rain.png"
        if 600 <= weather_id <= 622: return "assets/icons/snow.png"
        if 700 <= weather_id <= 781: return "assets/icons/mist.png"
        if weather_id == 800: return "assets/icons/sun.png"
        if 801 <= weather_id <= 804: return "assets/icons/cloud.png"
        return "assets/icons/sun.png" # Default

    def fade_in_animation(self):
        from PyQt5.QtWidgets import QGraphicsOpacityEffect
        
        # Check if effect already exists to avoid piling up
        effect = self.weather_container.graphicsEffect()
        if not effect:
            effect = QGraphicsOpacityEffect(self.weather_container)
            self.weather_container.setGraphicsEffect(effect)
        
        self.anim = QPropertyAnimation(effect, b"opacity")
        self.anim.setDuration(800)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    weather_app = WeatherApp()
    weather_app.show()
    sys.exit(app.exec_())
 