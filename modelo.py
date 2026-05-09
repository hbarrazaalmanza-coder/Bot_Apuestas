import requests
import pandas as pd
from scipy.stats import poisson

API_KEY = "056292c78dde690c700ed063c3289d08129b3969da05c2f52c3d64bb06d5fa5d"
url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}"

print("🧠 Iniciando el Motor Matemático (Poisson)...")

respuesta = requests.get(url)

if respuesta.status_code == 200:
    datos = respuesta.json()
    partidos = datos.get('data', [])
    
    # 1. Filtramos solo partidos con cuotas (Ligas Profesionales)
    partidos_profesionales = [p for p in partidos if p.get('odds_ft_over25', 0) > 1.0]
    
    lista_resultados = []

    print(f"⚽ Analizando {len(partidos_profesionales)} partidos profesionales...")
    print("-" * 60)

    for partido in partidos_profesionales:
        local = partido.get('home_name', 'Local')
        visitante = partido.get('away_name', 'Visitante')
        
        # Extraemos los Goles Esperados (xG)
        xg_local = float(partido.get('team_a_xg_prematch', 0))
        xg_visitante = float(partido.get('team_b_xg_prematch', 0))
        
        # Extraemos la cuota real de la casa de apuestas
        cuota_casa_over25 = float(partido.get('odds_ft_over25', 0))

        # Solo analizamos si hay datos de xG válidos (mayores a 0)
        if xg_local > 0 and xg_visitante > 0:
            
            # --- MODELO DE POISSON ---
            # Calculamos la probabilidad de los resultados "Under 2.5" (0, 1 o 2 goles en total)
            prob_under_25 = 0
            
            # Combinaciones posibles para Under 2.5: (0-0), (1-0), (0-1), (1-1), (2-0), (0-2)
            for goles_local in range(3):
                for goles_visitante in range(3):
                    if (goles_local + goles_visitante) <= 2:
                        # Calculamos la probabilidad de este marcador exacto usando Poisson
                        prob_marcador = poisson.pmf(goles_local, xg_local) * poisson.pmf(goles_visitante, xg_visitante)
                        prob_under_25 += prob_marcador
            
            # La probabilidad de Over 2.5 es lo contrario al Under 2.5
            prob_over_25 = 1 - prob_under_25
            
            # Convertimos esa probabilidad a "Cuota Justa" (Nuestra cuota matemática)
            cuota_justa_over25 = 1 / prob_over_25 if prob_over_25 > 0 else 0
            
            # --- CÁLCULO DE EDGE (VALOR) ---
            # Comparamos nuestra Cuota Justa vs la Cuota de la Casa
            edge = 0
            hay_valor = "❌ NO"
            
            # Solo hay EDGE si nuestra probabilidad es MAYOR a la probabilidad de la casa
            # Es decir, si la Casa de Apuestas paga MÁS de lo que debería.
            if cuota_casa_over25 > cuota_justa_over25 and cuota_justa_over25 > 0:
                 # Fórmula de Edge = (Probabilidad Real * Cuota Casa) - 1
                 edge = (prob_over_25 * cuota_casa_over25) - 1
                 edge_porcentaje = edge * 100
                 hay_valor = f"✅ SÍ (+{edge_porcentaje:.1f}%)"
            
            # Guardamos los resultados
            resultado = {
                'Partido': f"{local} vs {visitante}",
                'xG Local': xg_local,
                'xG Visit': xg_visitante,
                'Prob. Over 2.5': f"{prob_over_25*100:.1f}%",
                'Nuestra Cuota': round(cuota_justa_over25, 2),
                'Cuota Casa': cuota_casa_over25,
                '¿Hay Valor?': hay_valor
            }
            lista_resultados.append(resultado)

    # Creamos la tabla final
    df_resultados = pd.DataFrame(lista_resultados)
    
    # Ordenamos la tabla para que los que tienen "✅ SÍ" aparezcan primero
    df_resultados = df_resultados.sort_values(by='¿Hay Valor?', ascending=False)
    
    print(df_resultados.head(10).to_string(index=False))
    print("-" * 60)
    
    # Exportamos a Excel
    df_resultados.to_csv('analisis_over25.csv', index=False, encoding='utf-8')
    print("📈 Análisis guardado en 'analisis_over25.csv'. ¡Abre ese archivo en Excel!")

else:
    print("❌ ERROR al conectar.")
