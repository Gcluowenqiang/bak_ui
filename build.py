import PyInstaller.__main__
import os

if __name__ == '__main__':
    # 确保在脚本所在目录执行
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("开始打包 BakUI...")
    
    PyInstaller.__main__.run([
        'BakUI.spec',
        '--clean',
        '--noconfirm'
    ])
    
    print("打包完成！请查看 dist 目录。")

