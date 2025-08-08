# 🏇 Umamusume Auto Trainer (Global Server Edition)

**Uma Musume Pretty Derby Global Server Automatic Career Tool**

> **From China server automation to global server compatibility** - A complete transformation with enhanced features, improved UI, and robust automation capabilities.
>
> ***This project is for educational purpose only, [use it at your own risk](https://umamusume.com/news/100029/)***


## 📄 **License & Credits**

This project is a **Global Server adaptation** of the original China Server version by [@shiokaze](https://github.com/shiokaze/UmamusumeAutoTrainer).

### **Original Project**
- **Original Author**: [@shiokaze](https://github.com/shiokaze/UmamusumeAutoTrainer)
- **Original Repository**: [UmamusumeAutoTrainer](https://github.com/shiokaze/UmamusumeAutoTrainer) (China Server)

### **This Project**
- **Global Server Adaptation**: [UAT-Global-Server](https://github.com/BrayAlter/UAT-Global-Server)
- **Based on**: Original China Server version
- **Enhancements**: 70% translation, improved UI, Global Server compatibility

**Please respect the original author's work while contributing improvements.**


---


## 🌟 **What's New in Global Server Edition**

### 🎯 **Major Improvements**
- **🌍 Global Server Migration**: 70% translation and asset updates for Global Server compatibility
- **🎨 Enhanced Web Interface**: Advanced race filtering, skill choice system, and improved user experience
- **🤖 Robust Bot System**: Dual detection (image + OCR) for reliable race fail handling
- **⚡ Performance Optimization**: JSON-based data loading for faster operation
- **📱 Smart Device Detection**: Automatic ADB device detection and selection when start the program (emulator must open the game first)

### 🆕 **New Features**
- **Advanced Race Filtering**: Filter by race type, distance, terrain, and event character
- **Skill Choice System**: Intelligent skill selection interface in web application
- **Event Choice Picker**: Smart event selection for optimal training
- **70% English Translation**: Major UI and system text translated to English
- **Auto Device Selection**: Interactive ADB device detection and selection
- **🎮 Manual Skill Purchase**: New feature allowing manual skill selection at the end of career while maintaining automatic skill learning during normal training

### 🔄 **Current Limitations**
- **Uma Musume Selection**: Must be done manually in-game (not yet automated)
- **Support Card Selection**: Manual selection in-game required
- **Character Race Filter**: Race character filtering is implemented, the filter has been adjusted to the position and terrain of the field that the character masters, and has also been adjusted to the character's free schedule.

## 🚀 **Features**

### **Core Automation**
- ✅ **Automatic Training**: Complete training scenarios for all Uma Musume
- ✅ **Customizable Targets**: Training attributes, racing tactics, additional races
- ✅ **Skill Learning**: Optimized skill acquisition for 3-star spark farming
- ✅ **Manual Skill Purchase**: Option to manually select skills at career end while keeping auto-learning during training
- ✅ **Inheritance Compatibility**: Improved training strategy support

### **Advanced Web Interface**
- 🎛️ **Race Management**: Advanced filtering and selection tools
- 📊 **Real-time Monitoring**: Live task status and progress tracking
- ⚙️ **Easy Configuration**: Intuitive settings and preset management
- 🎯 **Character Filter**: Filter races based on selected character (manual select on UAT web)
- 🔔 **Web Notifications**: Modern notification system for manual skill purchase

## 📦 **Installation & Setup**

### **Option 1: Download Release (Recommended)**
1. Go to [Releases](https://github.com/BrayAlter/UAT-Global-Server/releases)
2. Download the latest release zip file
3. Extract and run `UmamusumeAutoTrainer.exe`

### **Option 2: Build from Source**

#### **Clone Repository**
```bash
git clone https://github.com/BrayAlter/UAT-Global-Server.git
cd UAT-Global-Server
```

#### **Install Dependencies**
1. Install Python 3.10.9: [Download Link](https://www.python.org/downloads/release/python-3109/)
2. Run `install.ps1` (Right-click → "Run with PowerShell")
3. Ensure no `venv` folder exists in current directory

### **Emulator Setup**
- **Resolution**: 720 × 1280 (Portrait mode)
- **DPI**: 180
- **Graphics**: Standard (not Simple)
- **ADB**: Must be enabled in emulator settings
- **IMPORTANT**: Open umamusume app before launch

### **Launch**
```bash
# Run the application
./run.ps1
```

The application will automatically:
1. 🔍 **Scan for ADB devices**
2. 📱 **Show available devices**
3. 🎮 **Detect devices with Umamusume running**
4. ✅ **Let you select your preferred device**
5. ⚙️ **Auto-update configuration**
6. 🚀 **Start the web interface**

**Success indicator:**
```
🚀 UAT running on http://127.0.0.1:8071
```

Access the web interface at `http://127.0.0.1:8071` to configure and start tasks.

![Main Web Interface](docs/1.png)

### **Race Selection Interface**
![Race Selection](docs/2.png)

### **Skill Selection Interface**
![Skill Selection](docs/3.png)

## ⚠️ **Important Notes**

### **Game Settings**
1. **Graphics**: Must be set to "Standard", not "Basic"
2. **Training Setup**: **Manually select** Uma Musume, Legacy, and Support Cards in-game before starting
3. **Support Cards**: Avoid friend cards (no specific outing strategy)
4. **Starting Position**: Be at Career Menu (where the UI Shows Training, Race, Recreation) 

### **Website Settings RECOMENDED**
- **Attribute Setting**: Set you desire attributes in the UAT interface, if you have no idea then try manual training first and put the result attribute value in the UAT interface
- **Race Selection RECOMENDED**: Configure you race schedule, this is very necessary to avoid lack of fans in the next goal, consider using the character filter in the race menu, Don't worry when using the character filter, because the filter has been adjusted to the position and terrain of the field that the character masters, and has also been adjusted to the character's free schedule.
- **Skill Optimization**: Set your desire skill, consider the priority 0 = the bot will buy the desire skill first
- **Manual Skill Purchase**: Check "Purchase skill manually at the end of career" to manually select final skills while keeping auto-learning during training

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Fan Goals Fail**
- **Failed to the next goal races because lack of Fans**: Configure the race selection first in the UAT website to avoid lack of Fans

#### **ADB Device Detection**
- **No devices found**: Ensure emulator is running and ADB is enabled and open the umamusume app
- **ADB server issues**: The app automatically restarts ADB server if needed
- **Device not detected**: Check emulator's ADB settings

#### **PowerShell Script Issues**
- **Script crashes**: Open console first to see error messages
- **Execution policy**: Reference: [PowerShell Execution Policy](https://www.jianshu.com/p/4eaad2163567)

#### **Connection Problems**
- **ADB connection fails**: Close accelerators, kill adb.exe, restart emulator
- **Recognition errors**: Manual operation to next turn, reset task in WebUI

#### **Web Interface Issues**
- **Module loading fails**: Ensure proper file permissions and paths

### **Error Recovery**
1. **Stuck interfaces**: Take screenshot, attach error logs
2. **Recognition failures**: Manual intervention, then restart
3. **Connection resets**: Restart both emulator and script

## 🛠️ **Technical Details**

### **System Requirements**
- **OS**: Windows 10/11
- **Python**: 3.10.9 (for source builds)
- **Emulator**: Android emulator with ADB support
- **Memory**: 4GB+ RAM recommended

### **Dependencies**
- **Computer Vision**: OpenCV for image recognition
- **Machine Learning**: PaddleOCR for text detection
- **Web Framework**: FastAPI + Vue.js
- **Automation**: UIAutomator2 for Android control

## 🎯 **Roadmap**

### **Planned Features**
- [ ] **Repeatable Tasks**: Automated execution at specific repeatable times
- [ ] **AI Training Logic**: Enhanced decision-making algorithms
- [ ] **Event Configuration**: Advanced event choice options
- [ ] **Daily Automation**: Auto-complete daily tasks (daily races, fans farming, event)
- [ ] **Uma Musume Auto-Selection**: Automated character, legacy, and support card selection
- [ ] **Card Name Translation**: Complete English translation for support card names
- [ ] **Accurate Translation**: Complete English accurate translation

### **Recent Updates**
- ✅ **Global Server Migration**: Complete compatibility update
- ✅ **Web Interface Enhancement**: Advanced filtering and controls
- ✅ **Performance Optimization**: JSON-based data loading
- ✅ **Error Handling**: Robust fail-safe mechanisms
- ✅ **Smart Device Detection**: Automatic ADB device selection
- ✅ **Manual Skill Purchase**: New feature for manual skill selection at career end

## 🤝 **Contributing**

We welcome contributions! If you find issues or have improvements:

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Submit a pull request**

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements.txt

# Run in development mode
python main.py
```

---
