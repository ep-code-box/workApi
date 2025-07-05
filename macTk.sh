# brew install tcl-tk


# Python과 tkinter 인터페이스 설치
# brew reinstall python@3.13.1 --with-tcl-tk
brew install python@3.13 python-tk@3.13

# 셸에서 Tcl/Tk 경로를 우선 참조하도록 환경변수 설정
echo 'export PATH="$(brew --prefix tcl-tk)/bin:$PATH"' >> ~/.zshrc
echo 'export LDFLAGS="-L$(brew --prefix tcl-tk)/lib"'      >> ~/.zshrc
echo 'export CPPFLAGS="-I$(brew --prefix tcl-tk)/include"' >> ~/.zshrc
echo 'export PKG_CONFIG_PATH="$(brew --prefix tcl-tk)/lib/pkgconfig"' >> ~/.zshrc

# 설정 반영
source ~/.zshrc

# 설치된 Python 확인 (3.13.1)
python3 --version

# tkinter 테스트
python3 -m tkinter
