"""
MarkeTTalento - Entry point para Streamlit Cloud
Todo en un solo proceso: Dashboard + API Docs
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import main

if __name__ == "__main__":
    main()