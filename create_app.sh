#!/bin/bash
# 创建 macOS .app 应用包
APP_NAME="LoanCalculator"
SCRIPT_FILE="loan_calculator.py"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 创建 .app 目录结构
APP_DIR="$APP_NAME.app"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# 创建 Info.plist
cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleExecutable</key>
    <string>run.sh</string>
    <key>CFBundleIdentifier</key>
    <string>com.yourdomain.$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
</dict>
</plist>
EOF

# 创建启动脚本
cat > "$APP_DIR/Contents/MacOS/run.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../../.. && pwd )
cd "$SCRIPT_DIR"
python3 "$SCRIPT_DIR/loan_calculator.py"
EOF

chmod +x "$APP_DIR/Contents/MacOS/run.sh"

echo "✅ macOS 应用包创建完成: $APP_DIR"
echo "你可以双击 $APP_NAME.app 在 Launchpad 中运行"
