"""Recover byte-identical private kernel tables from the official 1.4.3 addon.

The upstream repository excludes these generated headers. This build helper
preserves the reviewed release payloads instead of regenerating different CUDA
machine code. Generated headers and the source addon must not be committed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from build_thin_geometry_variants import emit_header, fingerprint_elf

RELEASE_SHA256 = '18636063cc4a762c24e2f2c25fef248058509986caae5becee65b5075fbe5e90'

def recover(addon, output):
    data = addon.read_bytes()
    if hashlib.sha256(data).hexdigest() != RELEASE_SHA256:
        raise ValueError('Expected the exact upstream 1.4.3 release addon')
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    count = struct.unpack_from('<H', data, pe+6)[0]
    optional = struct.unpack_from('<H', data, pe+20)[0]
    imagebase = struct.unpack_from('<Q', data, pe+24+24)[0]
    sections=[]
    for index in range(count):
        pos=pe+24+optional+index*40
        size,rva,rawsize,raw=struct.unpack_from('<IIII',data,pos+8)
        sections.append((rva,rawsize,raw))
    def offset(pointer):
        rva=pointer-imagebase
        for start,size,raw in sections:
            if start<=rva<start+size:return raw+rva-start
        raise ValueError('Pointer is outside file-backed sections')
    def payload(pointer,size):
        pos=offset(pointer)
        blob=data[pos:pos+size]
        if len(blob)!=size or blob[:4]!=b'\x7fELF':raise ValueError('Invalid cubin')
        fingerprint_elf(blob)
        return blob
    base=[];thin=[]
    for pos in range(0,len(data)-48,8):
        text,shared,regs,slot=struct.unpack_from('<IIII',data,pos)
        if shared not in (7776,3920,784) or not 5000<text<100000 or not 1<=regs<=64 or not text<slot<100000:continue
        try:
            size=struct.unpack_from('<I',data,pos+16)[0]
            if 1000<size<=slot:
                blob=payload(struct.unpack_from('<Q',data,pos+24)[0],size)
                base.append((text,shared,regs,slot,blob))
        except ValueError:pass
        try:
            sourcehash=struct.unpack_from('<Q',data,pos+16)[0]
            size=struct.unpack_from('<I',data,pos+24)[0]
            if not 1000<size<100000:continue
            blob=payload(struct.unpack_from('<Q',data,pos+32)[0],size)
            namepos=offset(struct.unpack_from('<Q',data,pos+40)[0])
            name=data[namepos:data.index(0,namepos)].decode('ascii')
            if not (name.startswith(('adaptive_','geometry_')) or name=='intermediate_scatter'):continue
            thin.append(dict(source_fingerprint=(text,shared,regs),slot_size=slot,source_hash=sourcehash,replacement=blob,mechanism=name))
        except (ValueError,UnicodeError):pass
    if len(base)!=6 or len(thin)!=13:raise ValueError(f'Unexpected release tables: {len(base)} base, {len(thin)} variants')
    output.mkdir(parents=True,exist_ok=True)
    lines=['// Recovered byte-identically from official Mavis 1.4.3. Do not commit.', '#pragma once',
        'struct CubinPatch { unsigned text, shared, regs, orig_size, size; const unsigned char* data; };',
        'inline constexpr const char* kCubinsBuiltFor="upstream 1.4.3 exact kernels";']
    rows=[]
    for i,(t,s,r,slot,blob) in enumerate(base):
        symbol=f'kReleaseCubin{i}'
        lines.append(f'static const unsigned char {symbol}[] = {{')
        lines.extend('  '+','.join(f'0x{x:02x}' for x in blob[p:p+16])+',' for p in range(0,len(blob),16))
        lines.append('};')
        rows.append(f'  {{{t}u,{s}u,{r}u,{slot}u,sizeof({symbol}),{symbol}}},')
    lines+=['static const CubinPatch kCubinPatches[] = {',*rows,'};']
    (output/'blackwell_cubins.generated.hpp').write_text('\n'.join(lines)+'\n',encoding='ascii',newline='\n')
    for name in ['thin_geometry_cubins.generated.hpp','thin_geometry_stability.generated.hpp']:
        emit_header(thin,output/name,[addon])
        path=output/name
        path.write_text('#define MFGUNLOCK_TABLE_RELEASE143 1\n'+path.read_text(),encoding='ascii',newline='\n')
    report=dict(source_sha256=RELEASE_SHA256,base_count=len(base),variant_count=len(thin),
        base=[dict(fingerprint=[t,s,r],slot=slot,sha256=hashlib.sha256(blob).hexdigest()) for t,s,r,slot,blob in base],
        variants=[dict(mechanism=r['mechanism'],sha256=hashlib.sha256(r['replacement']).hexdigest()) for r in thin])
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--addon',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args()
    result=recover(args.addon,args.output)
    args.receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(f"Preserved {result['base_count']} base kernels and {result['variant_count']} quality variants byte-identically")
