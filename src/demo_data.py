from pathlib import Path
from datetime import date,timedelta
import struct,zlib
def create_demo(folder):
    # Generated local examples only; never overwrite files.
    today=date.today();mon=today-timedelta(days=today.weekday());created=[]
    def png():
        block=lambda kind,data:struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
        raw=b''.join(b'\x00'+bytes([30,140,165])*64 for _ in range(64))
        return b'\x89PNG\r\n\x1a\n'+block(b'IHDR',struct.pack('>IIBBBBB',64,64,8,2,0,0,0))+block(b'IDAT',zlib.compress(raw))+block(b'IEND',b'')
    examples={f'晴日新品_{mon:%Y%m%d}_主視覺.png':png(),f'晴日新品_{mon:%Y%m%d}_促銷文案.txt':'活動：晴日新品\n優惠：第二件九折\n核對碼：APP-DEMO-31\n'.encode('utf-8'),f'晴日新品_{mon-timedelta(days=1):%Y%m%d}_上週文案.txt':'上週示範，不是本週素材。'.encode('utf-8'),f'晴日新品_{mon:%Y%m%d}_成效.csv':b'name,value\ndemo,3\n'}
    folder.mkdir(parents=True,exist_ok=True)
    for name,content in examples.items():
        p=folder/name
        if not p.exists():
            with p.open('xb') as f:f.write(content)
            created.append(name)
    return created
