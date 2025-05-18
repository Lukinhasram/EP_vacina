# Importação de bibliotecas necessárias para manipulação de dados, visualização e estatísticas
import io, pathlib, requests, pandas as pd
import seaborn as sns, matplotlib.pyplot as plt, statsmodels.api as sm

# Caminho do arquivo Parquet contendo os dados
PARQUET_FILE = pathlib.Path("immunization-master-data.parquet")

# Colunas de interesse no arquivo de dados
COLS = ["LOCAL_NAME", "YEAR", "PC_COVERAGE", "MHDI_I", "MHDI_E"]

# Ano alvo para análise (modifique conforme necessário)
TARGET_YEAR = 2016

# Diretório de saída para salvar os gráficos gerados
OUT_DIR = pathlib.Path(f"plots_normalidade_{TARGET_YEAR}")
OUT_DIR.mkdir(exist_ok=True)  # Cria o diretório, se não existir


# Função para gerar e salvar um gráfico QQ-plot
def qq_plot(series, title, path):
    sm.qqplot(series.dropna(), line="s")  # Gera o QQ-plot
    plt.title(title)  # Define o título do gráfico
    plt.tight_layout()  # Ajusta o layout
    plt.savefig(path)  # Salva o gráfico no caminho especificado
    plt.close()  # Fecha o gráfico para liberar memória

# Função para gerar e salvar um histograma com curva KDE
def hist_plot(series, title, path):
    sns.histplot(series.dropna(), kde=True)  # Gera o histograma com KDE
    plt.title(title)  # Define o título do gráfico
    plt.tight_layout()  # Ajusta o layout
    plt.savefig(path)  # Salva o gráfico no caminho especificado
    plt.close()  # Fecha o gráfico para liberar memória

# Bloco principal do script
if __name__ == "__main__":
    # Carrega o arquivo Parquet com as colunas especificadas
    df_full = pd.read_parquet(PARQUET_FILE, columns=COLS)

    # Filtra os dados para o ano alvo
    df = df_full[df_full["YEAR"] == TARGET_YEAR]

    # Verifica se há dados para o ano especificado
    if df.empty:
        raise ValueError(f"Year {TARGET_YEAR} not found.")  # Lança um erro se não houver dados

    # Gera gráficos para cada variável de interesse
    for var in ["PC_COVERAGE", "MHDI_I", "MHDI_E"]:
        # Gera e salva o histograma
        hist_plot(df[var],
                  f"Histograma — {var} ({TARGET_YEAR})",
                  OUT_DIR / f"{var}_hist.png")
        # Gera e salva o QQ-plot
        qq_plot(df[var],
                f"QQ-plot — {var} ({TARGET_YEAR})",
                OUT_DIR / f"{var}_qq.png")
        # Exibe mensagem de sucesso para cada variável
        print(f"✔  Gráficos para {var} salvos em {OUT_DIR}")

    # Mensagem final indicando que todos os gráficos foram gerados
    print("\nTodos os PNGs gerados para o ano", TARGET_YEAR)
