import pandas as pd
from sqlalchemy import create_engine, text

# ============================
# CONEXÃO
# ============================
engine = create_engine(
    'postgresql://postgres:20042004@localhost:5433/Alfabetizacao'
)

CSV_PATH = "br_inep_avaliacao_alfabetizacao_uf.csv"


def processar_etl():
    print("Iniciando ETL INEP...")

    df = pd.read_csv(CSV_PATH)

    # ============================
    # TRANSFORM
    # ============================
    df['ano'] = df['ano'].astype(int)
    df['sigla_uf'] = df['sigla_uf'].astype(str)
    df['serie'] = df['serie'].astype(int)
    df['rede'] = df['rede'].astype(int)

    nivel_cols = [c for c in df.columns if 'proporcao_aluno_nivel' in c]
    df[nivel_cols] = df[nivel_cols].fillna(0)

    with engine.connect() as conn:

        for _, row in df.iterrows():

            # ----------------------------
            # DIM TEMPO
            # ----------------------------
            conn.execute(text("""
                INSERT INTO dim_tempo (id_tempo, ano)
                SELECT :ano, :ano
                WHERE NOT EXISTS (
                    SELECT 1 FROM dim_tempo WHERE id_tempo = :ano
                )
            """), {"ano": row['ano']})

            # ----------------------------
            # DIM UF
            # ----------------------------
            conn.execute(text("""
                INSERT INTO dim_uf (sigla_uf)
                SELECT :uf
                WHERE NOT EXISTS (
                    SELECT 1 FROM dim_uf WHERE sigla_uf = :uf
                )
            """), {"uf": row['sigla_uf']})

            # ----------------------------
            # DIM REDE
            # ----------------------------
            conn.execute(text("""
                INSERT INTO dim_rede (codigo_rede)
                SELECT :rede
                WHERE NOT EXISTS (
                    SELECT 1 FROM dim_rede WHERE codigo_rede = :rede
                )
            """), {"rede": row['rede']})

            # ----------------------------
            # DIM SÉRIE
            # ----------------------------
            conn.execute(text("""
                INSERT INTO dim_serie (serie)
                SELECT :serie
                WHERE NOT EXISTS (
                    SELECT 1 FROM dim_serie WHERE serie = :serie
                )
            """), {"serie": row['serie']})

            # ----------------------------
            # BUSCAR IDS
            # ----------------------------
            id_uf = conn.execute(text("""
                SELECT id_uf FROM dim_uf WHERE sigla_uf = :uf
            """), {"uf": row['sigla_uf']}).fetchone()[0]

            id_rede = conn.execute(text("""
                SELECT id_rede FROM dim_rede WHERE codigo_rede = :rede
            """), {"rede": row['rede']}).fetchone()[0]

            id_serie = conn.execute(text("""
                SELECT id_serie FROM dim_serie WHERE serie = :serie
            """), {"serie": row['serie']}).fetchone()[0]

            # ----------------------------
            # FATO
            # ----------------------------
            conn.execute(text("""
                INSERT INTO fato_avaliacao (
                    id_tempo, id_uf, id_rede, id_serie,
                    taxa_alfabetizacao, media_portugues,
                    prop_nivel_0, prop_nivel_1, prop_nivel_2,
                    prop_nivel_3, prop_nivel_4, prop_nivel_5,
                    prop_nivel_6, prop_nivel_7, prop_nivel_8,
                    arquivo_origem
                )
                VALUES (
                    :ano, :uf, :rede, :serie,
                    :taxa, :media,
                    :n0, :n1, :n2, :n3, :n4,
                    :n5, :n6, :n7, :n8,
                    :arquivo
                )
            """), {
                "ano": row['ano'],
                "uf": id_uf,
                "rede": id_rede,
                "serie": id_serie,
                "taxa": row['taxa_alfabetizacao'],
                "media": row['media_portugues'],
                "n0": row.get('proporcao_aluno_nivel_0', 0),
                "n1": row.get('proporcao_aluno_nivel_1', 0),
                "n2": row.get('proporcao_aluno_nivel_2', 0),
                "n3": row.get('proporcao_aluno_nivel_3', 0),
                "n4": row.get('proporcao_aluno_nivel_4', 0),
                "n5": row.get('proporcao_aluno_nivel_5', 0),
                "n6": row.get('proporcao_aluno_nivel_6', 0),
                "n7": row.get('proporcao_aluno_nivel_7', 0),
                "n8": row.get('proporcao_aluno_nivel_8', 0),
                "arquivo": CSV_PATH
            })

        conn.commit()

    print("✅ ETL INEP FINALIZADO COM SUCESSO!")


if __name__ == "__main__":
    processar_etl()