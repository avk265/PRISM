"""Compare all 499 printed numeric cells in the supplied PDF with audited tables."""
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
TABLES=[('official_idle.tex',3),('live_idle.tex',4),('cpu_pressure.tex',6),('tenant_sharing.tex',9),('components.tex',1)]
METHODS=r'(?:Static-[1-4]|Spark DRA|Input-size rule|Lyu rule|RIOS rule|Ernest|CherryPick|Count-only control|Oracle \(hindsight\)|PRISM-[CL]-(?:LGBM|Ridge|XGB|MLP|SVR|RF)|Training expansion|Safety margin enabled|Runtime correction enabled|Idle capacity cap enabled)'
NUMBER=r'[+\-]?\d+(?:\.\d+)?'

def verify():
    parser=shutil.which('pdftotext')
    text=subprocess.check_output([parser,'-layout',str(ROOT/'paper/prism_spark_sql.pdf'),'-'],text=True) if parser else (ROOT/'paper/prism_spark_sql.txt').read_text()
    text=text.replace('\u2212','-');cells=0;rows=0
    for number,(filename,width) in enumerate(TABLES,1):
        start=text.index(f'Table {number}.');end=text.index(f'Table {number+1}.') if number<5 else text.index('Fig. 2.',start)
        actual={};pattern=re.compile(r'('+METHODS+r')\s+('+NUMBER+(r'\s+'+NUMBER)*(width-1)+r')(?=\s|$)')
        for match in pattern.finditer(text[start:end]):
            name=match[1];values=[float(v) for v in match[2].split()]
            if name in actual:raise AssertionError(f'Duplicate PDF row: Table {number} {name}')
            actual[name]=values
        expected={}
        for line in (ROOT/'results/tables'/filename).read_text().splitlines():
            line=line.strip()
            if ' & ' not in line or not line.endswith(r'\\'):continue
            fields=line[:-2].split(' & ')
            try:values=[float(re.sub(r'\\textbf\{([^}]+)\}',r'\1',v).strip()) for v in fields[1:]]
            except ValueError:continue
            if len(values)==width:expected[fields[0].strip()]=values
        assert set(actual)==set(expected),(number,'PDF/source row mismatch',sorted(set(actual)^set(expected)))
        for name,values in expected.items():
            assert all(abs(a-b)<1e-9 for a,b in zip(actual[name],values)),(number,name,actual[name],values)
            cells+=len(values);rows+=1
    assert cells==499,cells
    return dict(passed=True,printed_numeric_cells=cells,table_rows=rows,pdf_reextracted=bool(parser),canonical_pdf='paper/prism_spark_sql.pdf')

if __name__=='__main__':print(json.dumps(verify(),indent=2))
