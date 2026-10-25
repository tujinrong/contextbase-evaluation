"""Inventory already acquired local host tools; do not install or download."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
packages=json.loads((ROOT/'.tmp/toolchain/msys2/packages.lock.json').read_text(encoding='utf-8'))
toolchain=ROOT/'.tmp/toolchain'
data={'schema':'dependencies-lock/1.0','host':{'profile':'Windows x86_64 UCRT host evidence','compiler':{'name':'GnuCOBOL','version':'3.2.0','package':'1~3.2-10','path':'.tmp/toolchain/msys2/ucrt64/bin/cobc.exe'},'cCompiler':{'name':'Zig','version':'0.14.1','path':'.tmp/toolchain/zig-x86_64-windows-0.14.1/zig.exe','sha256':sha(toolchain/'zig-x86_64-windows-0.14.1/zig.exe')},'unicode':{'name':'ICU','packageVersion':'78.3-4','runtime':'libicuuc78.dll'},'crypto':{'name':'OpenSSL','packageVersion':'3.6.5-1','runtime':'libcrypto-3-x64.dll'},'packagesLock':'.tmp/toolchain/msys2/packages.lock.json','packages':packages,'GNUArchive':{'url':'https://ftp.gnu.org/gnu/gnucobol/gnucobol-3.2_win.7z','sha256':sha(toolchain/'gnucobol-3.2_win.7z'),'use':'source archive, not the active host compiler'}},'linux':{'profile':'Linux x86_64 little-endian CGI + Microsoft ODBC Driver18 + SQLServer2022','status':'UNRESOLVED_NOT_INSTALLED_NOT_BUILT','required':['GnuCOBOL3.2','C11 compiler','ICU','OpenSSL','unixODBC (2-byte SQLWCHAR)','Microsoft ODBC Driver18 for SQLServer','pkg-config','Python3','Node (generation only)'],'actualPackages':[],'reproducibilityStatus':'Linux exact package versions and SHA256 must be frozen on the deployment host; no Linux pass is recorded.'}}
(ROOT/'dependencies.lock.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded actual local host package hashes; Linux is unresolved, not inferred.')
