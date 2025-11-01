"""Test script to verify Selenium imports."""
import sys
print("Python path:", sys.path)

try:
    import selenium
    print("✅ Selenium imported successfully")
    print(f"   Version: {selenium.__version__}")
except ImportError as e:
    print(f"❌ Selenium import failed: {e}")
    sys.exit(1)

try:
    from selenium import webdriver
    print("✅ Selenium webdriver imported")
except ImportError as e:
    print(f"❌ Webdriver import failed: {e}")
    sys.exit(1)

try:
    from selenium.webdriver.chrome.options import Options
    print("✅ Chrome options imported")
except ImportError as e:
    print(f"❌ Chrome options import failed: {e}")
    sys.exit(1)

print("\n✅ All Selenium imports successful!")
