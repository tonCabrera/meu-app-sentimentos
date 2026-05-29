import os
import psycopg2
import spacy
import streamlit as st

# 1. Configuração do SpaCy (Carrega o modelo em português)
@st.cache_resource
def load_spacy():
    return spacy.load("pt_core_news_sm")


nlp = load_spacy()


# 2. Análise de Sentimento (Heurística simples para o SpaCy)
def analisar_sentimento(texto):
    doc = nlp(texto.lower())

    # Palavras-chave simples para determinar o sentimento
    # Em produção, você pode integrar com a biblioteca LeIA (VADER para PT) ou treinar o SpaCy
    palavras_positivas = [
        "bom",
        "boa",
        "ótimo",
        "otimo",
        "excelente",
        "gostei",
        "adorou",
        "amei",
        "feliz",
        "top",
        "legal",
        "maravilhoso",
    ]
    palavras_negativas = [
        "ruim",
        "pessimo",
        "péssimo",
        "odiei",
        "horrível",
        "horrivel",
        "triste",
        "chato",
        "difícil",
        "bosta",
        "merda",
        "mal",
    ]

    score = 0
    for token in doc:
        if token.text in palavras_positivas:
            score += 1
        elif token.text in palavras_negativas:
            score -= 1

    return "Positivo" if score >= 0 else "Negativo"


# 3. Conexão com o Banco de Dados Neon (PostgreSQL)
def get_db_connection():
    # Pega a URL de conexão das variáveis de ambiente (Configuração do Render)
    # Se não encontrar, usa uma string padrão (substitua pela sua para testes locais)
    DATABASE_URL = os.environ.get(
        "DATABASE_URL", "SUA_DATABASE_URL_DO_NEON_AQUI"
    )
    conn = psycopg2.connect(DATABASE_URL)
    return conn


# Cria a tabela caso ela não exista
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS avaliacoes_sentimento (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            cpf VARCHAR(14) NOT NULL,
            texto_sentimento TEXT NOT NULL,
            resultado_analise VARCHAR(10) NOT NULL
        );
    """
    )
    conn.commit()
    cur.close()
    conn.close()


# Inicializa o banco de dados
try:
    init_db()
except Exception as e:
    st.error(f"Erro ao conectar ao Neon Tech: {e}")

# 4. Interface UI - Streamlit (Design Moderno para Jovens/Adultos)
st.set_page_config(page_title="Feedback Analyzer", page_icon="🧠", layout="centered")

st.title("🧠 Sentiment AI Analyzer")
st.write(
    "Deixe seu feedback abaixo. Nossa IA vai analisar o tom do seu comentário!"
)

# Formulário de Input
with st.form(key="sentiment_form", clear_on_submit=True):
    nome = st.text_input("Nome Completo", placeholder="Digite seu nome...")
    cpf = st.text_input("CPF", placeholder="000.000.000-00")
    sentimento_texto = st.text_area(
        "O que você está achando? (Sua opinião)",
        placeholder="Escreva aqui seu feedback...",
    )

    submit_button = st.form_submit_button(label="Analisar e Salvar")

# Lógica de Submissão
if submit_button:
    if nome and cpf and sentimento_texto:
        with st.spinner("Analisando sentimento com SpaCy..."):
            # Executa a análise de NLP
            resultado = analisar_sentimento(sentimento_texto)

            # Salva no Neon Tech
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO avaliacoes_sentimento (nome, cpf, texto_sentimento, resultado_analise)
                    VALUES (%s, %s, %s, %s);
                """,
                    (nome, cpf, sentimento_texto, resultado),
                )
                conn.commit()
                cur.close()
                conn.close()

                # Exibe o resultado estilizado na tela
                st.success("Dados salvos com sucesso no Neon Tech!")

                if resultado == "Positivo":
                    st.balloons()
                    st.success(f"Análise da IA: O sentimento é **{resultado}**!  😃")
                else:
                    st.warning(f"Análise da IA: O sentimento é **{resultado}**.  😔")

            except Exception as e:
                st.error(f"Erro ao salvar no banco de dados: {e}")
    else:
        st.error("Por favor, preencha todos os campos antes de enviar!")

# Exibição dos dados salvos (Histórico recente)
st.markdown("---")
st.subheader("📊 Últimas Análises Realizadas")
if st.checkbox("Mostrar histórico do banco de dados"):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nome, resultado_analise FROM avaliacoes_sentimento ORDER BY id DESC LIMIT 5;"
        )
        dados = cur.fetchall()
        cur.close()
        conn.close()

        if dados:
            for linha in dados:
                cor = "🟢" if linha[2] == "Positivo" else "🔴"
                st.write(f"{cor} **ID {linha[0]}**: {linha[1]} -> {linha[2]}")
        else:
            st.info("Nenhum registro encontrado.")
    except Exception as e:
        st.error("Não foi possível carregar o histórico.")