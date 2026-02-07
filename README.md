0. Установка скрипта

chmod +x setup.sh
./setup.sh

source venv/bin/activate
python scripts/run_experiments.py

1. 
pip install pybind11

2.
```
rm -rf build
mkdir build
cd build
cmake ..
make
cd ..
```
3. 
```
python scripts/run_experiments.py
```