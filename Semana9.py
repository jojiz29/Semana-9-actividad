import streamlit as st
import psycopg2
import psycopg2.extras as pgx
from datetime import datetime

# =======================
# SECRETS (igual que tu base)
# =======================
USER   = st.secrets["postgres"]["USER"]
PASSWORD = st.secrets["postgres"]["PASSWORD"]
HOST   = st.secrets["postgres"]["HOST"]
PORT   = st.secrets["postgres"]["PORT"]
DBNAME = st.secrets["postgres"]["DBNAME"]

# =======================
# CONFIG PÁGINA
# =======================
st.set_page_config(page_title="🧮 Suma y guarda", page_icon="🧮")

# =======================
# CONEXIÓN A BD (mismo patrón)
# =======================
@st.cache_resource
def get_conn():
    conn = psycopg2.connect(
        user=USER, password=PASSWORD, host=HOST, port=PORT, dbname=DBNAME
    )
    conn.autocommit = True
    return conn

def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sum_operations (
            id BIGSERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            a DOUBLE PRECISION NOT NULL,
            b DOUBLE PRECISION NOT NULL,
            result DOUBLE PRECISION NOT NULL
        );
        """)

try:
    connection = get_conn()
    ensure_table(connection)
    with connection.cursor() as cursor:
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()[0]
    st.sidebar.success("Conectado a la base de datos correctamente ✅")
except Exception as e:
    st.sidebar.error(f"Error de conexión: {e}")
    st.stop()

# =======================
# INTERFAZ (suma simple)
# =======================
st.title("🧮 Suma de números (PostgreSQL)")

col1, col2 = st.columns(2)
with col1:
    a = st.number_input("Primer número (a)", value=0.0, step=1.0, format="%.4f")
with col2:
    b = st.number_input("Segundo número (b)", value=0.0, step=1.0, format="%.4f")

if st.button("Calcular y guardar"):
    try:
        result_val = float(a) + float(b)
        with connection.cursor() as cur:
            cur.execute(
                "INSERT INTO sum_operations (a, b, result) VALUES (%s, %s, %s)",
                (a, b, result_val),
            )
        st.success(f"✅ Resultado: {result_val:.4f} — guardado en BD.")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# =======================
# HISTORIAL
# =======================
st.subheader("🗂️ Historial reciente")
limit = st.slider("Cantidad a mostrar", 1, 50, 10)

try:
    with connection.cursor(cursor_factory=pgx.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT created_at, a, b, result
            FROM sum_operations
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()

    if rows:
        for r in rows:
            ts = r["created_at"].astimezone().strftime("%Y-%m-%d %H:%M:%S")
            st.write(f"• `{ts}` — {r['a']:.4f} + {r['b']:.4f} = **{r['result']:.4f}**")
    else:
        st.caption("Aún no hay operaciones registradas.")
except Exception as e:
    st.error(f"Error al consultar historial: {e}")

