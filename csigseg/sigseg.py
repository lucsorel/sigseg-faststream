from ctypes import cdll

DLL_TYPE = cdll.LoadLibrary('csigseg/libsigseg.so')

print('a segmentation fault should have occurred when importing libtest.so')
