import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = str(Path(__file__).parent / 'src')
if src_path not in sys.path:
    sys.path.append(src_path)

from backend.app import app

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5001) 