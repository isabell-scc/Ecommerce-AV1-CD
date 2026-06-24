import pandas as pd
import numpy as np

from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
)
from prophet import Prophet
import logging

logging.getLogger("prophet").setLevel(logging.WARNING)


def preparar_dados_temporais(df_dados):

    df = pd.DataFrame(df_dados)
    df["data"] = pd.to_datetime(df["data"])

    df_diario = df.groupby("data")["valor_total"].sum().reset_index()
    df_diario = df_diario.sort_values("data").reset_index(drop=True)

    df_diario["dia_num"] = (df_diario["data"] - df_diario["data"].min()).dt.days
    df_diario["mes"] = df_diario["data"].dt.month
    df_diario["dia_semana"] = df_diario["data"].dt.dayofweek   
    df_diario["trimestre"] = df_diario["data"].dt.quarter
    df_diario["semana_ano"] = df_diario["data"].dt.isocalendar().week.astype(int)

    df_diario["lag_1"] = df_diario["valor_total"].shift(1)  
    df_diario["lag_7"] = df_diario["valor_total"].shift(7)   

    df_diario["media_7"] = df_diario["valor_total"].shift(1).rolling(7, min_periods=1).mean()
    df_diario["media_30"] = df_diario["valor_total"].shift(1).rolling(30, min_periods=1).mean()

    df_diario["lag_1"] = df_diario["lag_1"].fillna(df_diario["media_7"])
    df_diario["lag_7"] = df_diario["lag_7"].fillna(df_diario["media_7"])

    return df_diario


def _preparar_futuro_rf(df_diario, df_treino, datas_futuras, features):

    futuro = pd.DataFrame({"data": datas_futuras})
    futuro["dia_num"] = (futuro["data"] - df_diario["data"].min()).dt.days
    futuro["mes"] = futuro["data"].dt.month
    futuro["dia_semana"] = futuro["data"].dt.dayofweek       
    futuro["trimestre"] = futuro["data"].dt.quarter
    futuro["semana_ano"] = futuro["data"].dt.isocalendar().week.astype(int)

    historico = df_treino[["data", "valor_total"]].copy().reset_index(drop=True)

    previsoes_acumuladas = []
    modelo_temp = None 

    for i, row in futuro.iterrows():
        data_atual = row["data"]

        # lag_1: ontem
        dia_anterior = historico[historico["data"] == data_atual - pd.Timedelta(days=1)]
        lag_1 = dia_anterior["valor_total"].values[0] if not dia_anterior.empty else historico["valor_total"].iloc[-1]

        # lag_7: semana passada
        dia_semana_passada = historico[historico["data"] == data_atual - pd.Timedelta(days=7)]
        lag_7 = dia_semana_passada["valor_total"].values[0] if not dia_semana_passada.empty else historico["valor_total"].iloc[-7:].mean()

        # media_7: média dos últimos 7 dias 
        media_7 = historico["valor_total"].iloc[-7:].mean()
        media_30 = historico["valor_total"].iloc[-30:].mean()

        futuro.at[i, "lag_1"] = lag_1
        futuro.at[i, "lag_7"] = lag_7
        futuro.at[i, "media_7"] = media_7
        futuro.at[i, "media_30"] = media_30


    return futuro


def treinar_e_prever(df_diario, data_corte, tipo_modelo, horizonte_dias=30):

    data_corte = pd.to_datetime(data_corte)

    df_treino = df_diario[df_diario["data"] <= data_corte].copy()
    df_teste = df_diario[df_diario["data"] > data_corte].copy()

    if df_treino.empty or df_teste.empty:
        return None, None, 0, 0, 0, []


   
    # RANDOM FOREST 
    if tipo_modelo == "Random Forest":

        features_rf = [
            "dia_num",
            "mes",
            "dia_semana",
            "trimestre",
            "semana_ano",
            "lag_1",
            "lag_7",
            "media_7",
            "media_30",
        ]

        X_treino = df_treino[features_rf]
        y_treino = df_treino["valor_total"]

        #GRID-SEARCH
        param_grid = {
            "n_estimators": [100, 250],
            "max_depth": [5, 10, 15],
            "min_samples_split": [2, 5] 
        }

        rf_base = RandomForestRegressor(random_state=42)
        grid_search = GridSearchCV(rf_base, param_grid, cv=3, scoring="neg_mean_absolute_error" ,n_jobs=-1)
        grid_search.fit(X_treino, y_treino)
    
        modelo = grid_search.best_estimator_
        print(f"🎯 Melhores parâmetros RF: {grid_search.best_params_}")

        X_teste = df_teste[features_rf]
        y_pred_teste = modelo.predict(X_teste)

        # Monta futuro com lags propagados iterativamente
        datas_futuras = pd.date_range(
            start=df_treino["data"].max() + pd.Timedelta(days=1),
            periods=horizonte_dias,
        )
        futuro = _preparar_futuro_rf(df_diario, df_treino, datas_futuras, features_rf)
        previsoes_futuras = modelo.predict(futuro[features_rf])

    # PROPHET 
    else:

        df_prophet_train = (
            df_treino[["data", "valor_total"]]
            .rename(columns={"data": "ds", "valor_total": "y"})
        )

        modelo = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=1,
            seasonality_mode="multiplicative", 
        )

        # Adiciona feriados brasileiros
        modelo.add_country_holidays(country_name="BR")
        modelo.add_seasonality(
            name="monthly",
            period=30.5,
            fourier_order=8
        )

        modelo.fit(df_prophet_train)

        df_prophet_test = df_teste[["data"]].rename(columns={"data": "ds"})
        previsao_teste = modelo.predict(df_prophet_test)
        y_pred_teste = previsao_teste["yhat"].values

        futuro = modelo.make_future_dataframe(periods=horizonte_dias, freq="D")
        futuro = futuro[futuro["ds"] > df_treino["data"].max()]
        previsao_futura = modelo.predict(futuro)

        datas_futuras = previsao_futura["ds"].values
        previsoes_futuras = previsao_futura["yhat"].values


    # MÉTRICAS
    y_pred_teste = np.clip(y_pred_teste, 0, None)
    previsoes_futuras = np.clip(previsoes_futuras, 0, None)

    limite = min(len(df_teste), len(y_pred_teste))

    mae = mean_absolute_error(
        df_teste["valor_total"].iloc[:limite],
        y_pred_teste[:limite],
    )
    rmse = np.sqrt(
        mean_squared_error(
            df_teste["valor_total"].iloc[:limite],
            y_pred_teste[:limite],
        )
    )
    mape = (
        mean_absolute_percentage_error(
            df_teste["valor_total"].iloc[:limite],
            y_pred_teste[:limite],
        )
        * 100
    )

    df_previsao = pd.DataFrame({"data": datas_futuras, "previsao": previsoes_futuras})

    return (
        df_previsao,
        df_teste,
        round(mae, 2),
        round(rmse, 2),
        round(mape, 2),
        y_pred_teste,
    )