import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from math import sqrt
# --------------- CONFIG ----------------
CSV_DIARIO = "ia/ml/ventas_sinteticas.csv"      # tu CSV diario
MODELO_PKL = "ia/ml/modelo_random_forest_ventas_mensuales.pkl"  # nombre del archivo del modelo
TEST_SIZE = 0.2
RANDOM_STATE = 42

# --------------- LEER CSV Y AGRUPAR POR MES ----------------
df = pd.read_csv(CSV_DIARIO, parse_dates=["fecha"])

# Extraer mes y año
df['anio'] = df['fecha'].dt.year
df['mes'] = df['fecha'].dt.month

# Agrupar por mes
df_mes = df.groupby(['anio', 'mes']).agg(
    total_ventas_mes=('total_ventas', 'sum'),
    num_pedidos_mes=('num_pedidos', 'sum'),
    promedio_pedido_mes=('promedio_pedido', 'mean'),
    porcentaje_credito_mes=('porcentaje_credito', 'mean'),
    porcentaje_contado_mes=('porcentaje_contado', 'mean')
).reset_index()

# Agregar temporada
df_mes['temporada'] = df_mes['mes'].apply(lambda x: 1 if x in [1,6,11,12] else 0)

# --------------- PREPARAR DATOS PARA EL MODELO ----------------
# X: características
X = df_mes[['num_pedidos_mes', 'promedio_pedido_mes', 'porcentaje_credito_mes',
            'porcentaje_contado_mes', 'mes', 'temporada']].values

# y: objetivo (total de ventas por mes)
y = df_mes['total_ventas_mes'].values

# Dividir en entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)

# --------------- ENTRENAR RANDOM FOREST ----------------
modelo_rf = RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE)
modelo_rf.fit(X_train, y_train)

# --------------- EVALUAR MODELO ----------------
y_pred = modelo_rf.predict(X_test)
rmse = sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("✅ Entrenamiento completado")
print(f"RMSE: {rmse:.2f}")
print(f"R²: {r2:.2f}")

# --------------- GUARDAR MODELO ----------------
joblib.dump(modelo_rf, MODELO_PKL)
print(f"Modelo guardado en: {MODELO_PKL}")
