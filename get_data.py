# scripts/get_data.py
import os, pathlib, requests, tqdm, sys

URL = "https://dados-vacinacao-infantil-ep.s3.us-east-2.amazonaws.com/immunization_master_data.csv"
DEST = pathlib.Path("immunization_master_data.csv")

def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print("✔ CSV já existe, pulando download")
        return
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        bar = tqdm.tqdm(total=total, unit="B", unit_scale=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
                bar.update(len(chunk))
    print(f"✔ Download concluído → {dest}")

if __name__ == "__main__":
    try:
        download(URL, DEST)
    except Exception as e:
        print("Erro ao baixar CSV:", e)
        sys.exit(1)
