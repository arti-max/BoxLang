import os
import sys


def wr(disk, file, N):
    with open(disk, 'rb+') as disk:
        disk.seek(N)  # смещение (адрес) в байтах
        with open(file, 'rb') as f:
            disk.write(f.read())

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python/py wtd.py disk.img file.bin address")
        sys.exit(1)

    wr(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    print("binrary succefully writed to disk!")