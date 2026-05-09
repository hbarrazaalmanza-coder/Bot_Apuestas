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
    
    partidos_profesionales = [p for p in partidos if p.get('odds_ft_over25', 0) > 1.0]
    
    lista_resultados = []

    for partido in partidos_profesionales:
        local = partido.get('home_name', 'Local')
        visitante = partido.get('away_name', 'Visitante')
        
        xg_local = float(partido.get('team_a_xg_prematch', 0))
        xg_visitante = float(partido.get('team_b_xg_prematch', 0))
        cuota_casa_over25 = float(partido.get('odds_ft_over25', 0))

        if xg_local > 0 and xg_visitante > 0:
            
            prob_under_25 = 0
            
            for goles_local in range(3):
                for goles_visitante in range(3):
                    if (goles_local + goles_visitante) <= 2:
                        prob_marcador = poisson.pmf(goles_local, xg_local) * poisson.pmf(goles_visitante, xg_visitante)
                        prob_under_25 += prob_marcador
            
            prob_over_25 = 1 - prob_under_25
            cuota_justa_over25 = 1 / prob_over_25 if prob_over_25 > 0 else 0
            
            edge = 0
            hay_valor = "❌ NO"
            
            if cuota_casa_over25 > cuota_justa_over25 and cuota_justa_over25 > 0:
                 edge = (prob_over_25 * cuota_casa_over25) - 1
                 edge_porcentaje = edge * 100
                 hay_valor = f"✅ SÍ (+{edge_porcentaje:.1f}%)".replace('.', ',')
            
            # --- ARREGLO DE FORMATO PARA EXCEL EN ESPAÑOL ---
            xg_local_str = str(round(xg_local, 2)).replace('.', ',')
            xg_visit_str = str(round(xg_visitante, 2)).replace('.', ',')
            prob_over_str = str(round(prob_over_25 * 100, 1)).replace('.', ',') + "%"
            cuota_justa_str = str(round(cuota_justa_over25, 2)).replace('.', ',')
            cuota_casa_str = str(round(cuota_casa_over25, 2)).replace('.', ',')

            resultado = {
                'Partido': f"{local} vs {visitante}",
                'xG Local': xg_local_str,
                'xG Visit': xg_visit_str,
                'Prob. Over 2.5': prob_over_str,
                'Nuestra Cuota': cuota_justa_str,
                'Cuota Casa': cuota_casa_str,
                '¿Hay Valor?': hay_valor
            }
            lista_resultados.append(resultado)

    df_resultados = pd.DataFrame(lista_resultados)
    df_resultados = df_resultados.sort_values(by='¿Hay Valor?', ascending=False)
    
    # IMPORTANTE: Cambiamos el separador a punto y coma (;) para que Excel no confunda las comas de los decimales
    df_resultados.to_csv('analisis_over25.csv', index=False, encoding='utf-8-sig', sep=';')
    print("📈 Análisis guardado con formato para Excel.")

else:
    print("❌ ERROR al conectar.")
