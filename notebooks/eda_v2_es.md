# Tickets de Soporte Polaris — Dataset Sintético v2 · EDA (español)

**~24.000 tickets de soporte sintéticos** para *Polaris*, un SaaS de analítica
multicanal ficticio. Generados con un pipeline (catálogo de escenarios → sampler →
LLM), y encima una **capa temporal de eventos**: **caídas de servicio** (outages,
picos agudos) y **lanzamientos** de conectores (olas graduales), repartidos entre
**enero 2024 y junio 2026**.

Este notebook verifica que el dataset tiene una *firma temporal* realista — no solo
etiquetas balanceadas, sino el agrupamiento y la estacionalidad que muestra una cola
de soporte real — que es lo que lo hace útil para triage, deflexión con RAG **y**
series de tiempo (pronóstico de volumen, detección de anomalías).

> **Nota:** versión en español para estudio. El artefacto de portafolio es el
> notebook en inglés (`eda_v2.ipynb`).


```python
import json, sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
sys.path.insert(0, "..")
from src.sampler import aligned_category  # la categoría 'correcta' del picklist por (topic, type)

pd.set_option("display.max_rows", 60)
plt.rcParams.update({"figure.dpi": 110, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10})
ACCENT, BASE_C, EVT_C = "#2E5A87", "#9db8d2", "#d9534f"

rows = [json.loads(l) for l in open("../data/tickets_v2.jsonl")]
df = pd.DataFrame(rows)
df["created_at"] = pd.to_datetime(df["created_at"])
df["month"] = df["created_at"].dt.to_period("M").dt.to_timestamp()
df["is_event"] = df["event_id"].notna()
len(df), df["created_at"].min().date(), df["created_at"].max().date()
```




    (23994, datetime.date(2024, 1, 1), datetime.date(2026, 6, 30))



## El dataset de un vistazo


```python
n = len(df)
ev = df["is_event"].sum()
print(f"tickets            : {n:,}")
print(f"rango de fechas    : {df.created_at.min().date()} -> {df.created_at.max().date()}")
print(f"por evento         : {ev:,} ({ev/n*100:.1f}%)   flujo base: {n-ev:,} ({(n-ev)/n*100:.1f}%)")
print(f"etiquetas únicas   : topic={df.topic.nunique()}  type={df.type.nunique()}  "
      f"priority={df.priority.nunique()}  routing={df.routing.nunique()}  sentiment={df.sentiment.nunique()}")
print("\npor año:")
print(df.groupby(df.created_at.dt.year).size().to_string())
```

    tickets            : 23,994
    rango de fechas    : 2024-01-01 -> 2026-06-30
    por evento         : 6,000 (25.0%)   flujo base: 17,994 (75.0%)
    etiquetas únicas   : topic=8  type=8  priority=4  routing=5  sentiment=6
    
    por año:
    created_at
    2024     6017
    2025    11979
    2026     5998


### Catálogo de eventos

Cada evento de la capa, con su tipo, ventana y cuántos tickets generó.


```python
cat = (df[df.is_event].groupby(["event_id", "event_type"])
       .agg(tickets=("ticket_id", "size"),
            primero=("created_at", "min"), ultimo=("created_at", "max"))
       .reset_index())
cat["primero"] = cat["primero"].dt.date
cat["ultimo"] = cat["ultimo"].dt.date
cat.sort_values("primero").reset_index(drop=True)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>event_id</th>
      <th>event_type</th>
      <th>tickets</th>
      <th>primero</th>
      <th>ultimo</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>launch_constant_contact_connector</td>
      <td>launch</td>
      <td>450</td>
      <td>2024-02-18</td>
      <td>2024-08-10</td>
    </tr>
    <tr>
      <th>1</th>
      <td>outage_ga4_sync_2024q1</td>
      <td>outage</td>
      <td>200</td>
      <td>2024-02-20</td>
      <td>2024-02-24</td>
    </tr>
    <tr>
      <th>2</th>
      <td>outage_dashboards_2024q3</td>
      <td>outage</td>
      <td>200</td>
      <td>2024-07-09</td>
      <td>2024-07-12</td>
    </tr>
    <tr>
      <th>3</th>
      <td>launch_klaviyo_connector</td>
      <td>launch</td>
      <td>450</td>
      <td>2024-07-25</td>
      <td>2025-01-05</td>
    </tr>
    <tr>
      <th>4</th>
      <td>outage_hubspot_sync_2024q4</td>
      <td>outage</td>
      <td>200</td>
      <td>2024-11-05</td>
      <td>2024-11-09</td>
    </tr>
    <tr>
      <th>5</th>
      <td>launch_salesforce_connector</td>
      <td>launch</td>
      <td>700</td>
      <td>2024-12-10</td>
      <td>2025-06-01</td>
    </tr>
    <tr>
      <th>6</th>
      <td>launch_tiktok_connector</td>
      <td>launch</td>
      <td>900</td>
      <td>2025-02-18</td>
      <td>2025-08-10</td>
    </tr>
    <tr>
      <th>7</th>
      <td>outage_dashboards_2025q1</td>
      <td>outage</td>
      <td>400</td>
      <td>2025-03-12</td>
      <td>2025-03-15</td>
    </tr>
    <tr>
      <th>8</th>
      <td>launch_zoho_connector</td>
      <td>launch</td>
      <td>700</td>
      <td>2025-06-21</td>
      <td>2025-12-14</td>
    </tr>
    <tr>
      <th>9</th>
      <td>outage_ga4_sync_2025q3</td>
      <td>outage</td>
      <td>400</td>
      <td>2025-08-19</td>
      <td>2025-08-23</td>
    </tr>
    <tr>
      <th>10</th>
      <td>outage_dashboards_2025q4</td>
      <td>outage</td>
      <td>400</td>
      <td>2025-11-04</td>
      <td>2025-11-07</td>
    </tr>
    <tr>
      <th>11</th>
      <td>outage_dashboards_2026q1</td>
      <td>outage</td>
      <td>500</td>
      <td>2026-02-17</td>
      <td>2026-02-20</td>
    </tr>
    <tr>
      <th>12</th>
      <td>outage_ga4_sync_2026q2</td>
      <td>outage</td>
      <td>500</td>
      <td>2026-05-06</td>
      <td>2026-05-10</td>
    </tr>
  </tbody>
</table>
</div>



### Resumen por año


```python
yr = (df.assign(anio=df.created_at.dt.year).groupby("anio")
      .agg(tickets=("ticket_id", "size"), por_evento=("is_event", "sum")))
yr["base"] = yr["tickets"] - yr["por_evento"]
yr["evento_%"] = (yr["por_evento"] / yr["tickets"] * 100).round(1)
yr
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>tickets</th>
      <th>por_evento</th>
      <th>base</th>
      <th>evento_%</th>
    </tr>
    <tr>
      <th>anio</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2024</th>
      <td>6017</td>
      <td>1517</td>
      <td>4500</td>
      <td>25.2</td>
    </tr>
    <tr>
      <th>2025</th>
      <td>11979</td>
      <td>3483</td>
      <td>8496</td>
      <td>29.1</td>
    </tr>
    <tr>
      <th>2026</th>
      <td>5998</td>
      <td>1000</td>
      <td>4998</td>
      <td>16.7</td>
    </tr>
  </tbody>
</table>
</div>



### Metadata (canal · plan · rol)


```python
meta = {}
for col in ["channel", "plan", "user_role"]:
    vc = df[col].value_counts()
    meta[col] = (vc / len(df) * 100).round(1)
pd.DataFrame(meta).rename_axis("valor").fillna("")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>channel</th>
      <th>plan</th>
      <th>user_role</th>
    </tr>
    <tr>
      <th>valor</th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>admin</th>
      <td></td>
      <td></td>
      <td>40.1</td>
    </tr>
    <tr>
      <th>analyst</th>
      <td></td>
      <td></td>
      <td>36.5</td>
    </tr>
    <tr>
      <th>chat</th>
      <td>35.0</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>email</th>
      <td>49.9</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>enterprise</th>
      <td></td>
      <td>15.0</td>
      <td></td>
    </tr>
    <tr>
      <th>growth</th>
      <td></td>
      <td>35.0</td>
      <td></td>
    </tr>
    <tr>
      <th>in_app</th>
      <td>15.1</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>starter</th>
      <td></td>
      <td>50.0</td>
      <td></td>
    </tr>
    <tr>
      <th>viewer</th>
      <td></td>
      <td></td>
      <td>23.4</td>
    </tr>
  </tbody>
</table>
</div>



## 1. La firma temporal — el punto del v2

Volumen mensual, separado en el **flujo base** (parejo) y los tickets **por evento**
encima. Un generador plano y sin memoria daría una banda horizontal aburrida; en
cambio vemos crecimiento año a año, **picos de outage** agudos y **olas de
lanzamiento** más anchas.


```python
piv = (df.groupby(["month", "is_event"]).size()
         .unstack(fill_value=0).rename(columns={False: "base", True: "evento"}))
# etiquetas de mes como texto: un índice datetime en un bar plot dispara un bug de pandas (Period/freq)
piv.index = piv.index.strftime("%Y-%m")
ax = piv[["base", "evento"]].plot(kind="bar", stacked=True, figsize=(14, 5),
                                  color=[BASE_C, EVT_C], width=0.9)
ax.set_title("Volumen mensual de tickets — base vs por evento", fontweight="bold")
ax.set_xlabel(""); ax.set_ylabel("tickets")
ax.tick_params(axis="x", labelrotation=90); ax.tick_params(axis="x", labelsize=7)
ax.legend(title="")
plt.tight_layout(); plt.show()
```


    
![png](eda_v2_es_files/eda_v2_es_11_0.png)
    


**Cómo leerlo:** la banda clara (base) crece ~2x de 2024 a 2025 al escalar la
empresa, y sigue hacia 2026-H1. Los picos rojos son **outages** (un conector o los
dashboards se rompen → estallido de tickets en días). Los cúmulos rojos más anchos
son **olas de lanzamiento** (sale un conector nuevo → semanas de preguntas de "cómo
lo conecto"). Ese agrupamiento es lo que muestra una cola real — y lo que un modelo
de pronóstico o de anomalías necesita aprender.

## 2. El arco de lanzamiento — pedidos que desaparecen el día del launch

Antes de que exista un conector, los clientes preguntan *"¿cuándo van a agregar X?"*
(un `feature_request`). En cuanto sale, esos pedidos paran y se vuelven *"¿cómo
conecto X?"* (`how_to`). Graficando los **feature-requests de conectores por mes**
con cada fecha de lanzamiento marcada, se ve la demanda subir y luego caer.


```python
fr = df[(df.type == "feature_request") & (df.topic == "connectors")]
monthly_fr = fr.groupby("month").size()
launches = {"Constant Contact": "2024-05-13", "Klaviyo": "2024-10-07",
            "Salesforce": "2025-03-03", "TikTok Ads": "2025-05-12",
            "Zoho CRM": "2025-09-15"}
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(monthly_fr.index, monthly_fr.values, marker="o", color=ACCENT, lw=2)
ax.set_title("Feature-requests de conectores por mes, con fechas de lanzamiento",
             fontweight="bold")
ax.set_ylabel("feature-requests"); ax.set_xlabel("")
for name, d in launches.items():
    ts = pd.Timestamp(d)
    ax.axvline(ts, color=EVT_C, ls="--", alpha=0.7)
    ax.text(ts, ax.get_ylim()[1]*0.95, name, rotation=90, va="top",
            ha="right", fontsize=8, color=EVT_C)
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
plt.xticks(rotation=90, fontsize=7); plt.tight_layout(); plt.show()
```


    
![png](eda_v2_es_files/eda_v2_es_14_0.png)
    


**Cómo leerlo (ojo, es al revés de lo que parece):** cada línea punteada es un
conector saliendo a producción. El volumen de *pedidos* **sube acercándose** al
lanzamiento y **cae justo después** — o sea, los picos son la gente *pidiendo* el
conector ANTES de que exista, y la demanda se apaga cuando lo entregas (ya nadie
pide lo que ya está). El pico = "lo quiero", no "ya lo tienen". La línea mezcla todos
los feature-requests de conectores (por eso es un poco ruidosa); la versión nítida de
esta señal es la tabla de antes/después por conector.

## 3. Distribución de etiquetas — los objetivos del modelo (ML)


```python
fig, axes = plt.subplots(2, 2, figsize=(13, 8))
specs = [("priority", ["low", "medium", "high", "critical"]),
         ("routing", None), ("topic", None), ("type", None)]
for ax, (col, order) in zip(axes.ravel(), specs):
    vc = df[col].value_counts()
    if order:
        vc = vc.reindex(order)
    (vc / len(df) * 100).plot(kind="bar", ax=ax, color=ACCENT, width=0.8)
    ax.set_title(col, fontweight="bold"); ax.set_ylabel("% de tickets")
    ax.set_xlabel(""); ax.tick_params(axis="x", rotation=30)
plt.tight_layout(); plt.show()
```


    
![png](eda_v2_es_files/eda_v2_es_17_0.png)
    


**Cómo leerlo:** **priority** sigue una cola larga realista (casi todo es
rutina, poco es crítico), sesgada un poco hacia high/critical por los outages.
**routing** lo domina `kb_autoresolve` — la oportunidad de deflexión que ataca el
RAG. **topic** y **type** quedan repartidos por todo el producto, así que ninguna
clase domina trivialmente al clasificador.

### Frecuencias exactas — los números detrás de las barras


```python
def freq_table(col, order=None):
    vc = df[col].value_counts()
    if order:
        vc = vc.reindex(order)
    return pd.DataFrame({"conteo": vc, "pct_%": (vc / len(df) * 100).round(1)})

pd.concat({c: freq_table(c) for c in ["topic", "type", "routing"]}, names=["campo", "valor"])
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th></th>
      <th>conteo</th>
      <th>pct_%</th>
    </tr>
    <tr>
      <th>campo</th>
      <th>valor</th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="8" valign="top">topic</th>
      <th>connectors</th>
      <td>8827</td>
      <td>36.8</td>
    </tr>
    <tr>
      <th>dashboards</th>
      <td>4600</td>
      <td>19.2</td>
    </tr>
    <tr>
      <th>alerts</th>
      <td>3065</td>
      <td>12.8</td>
    </tr>
    <tr>
      <th>reports</th>
      <td>1940</td>
      <td>8.1</td>
    </tr>
    <tr>
      <th>attribution</th>
      <td>1777</td>
      <td>7.4</td>
    </tr>
    <tr>
      <th>billing</th>
      <td>1666</td>
      <td>6.9</td>
    </tr>
    <tr>
      <th>users_workspace</th>
      <td>1515</td>
      <td>6.3</td>
    </tr>
    <tr>
      <th>northstar</th>
      <td>604</td>
      <td>2.5</td>
    </tr>
    <tr>
      <th rowspan="8" valign="top">type</th>
      <th>how_to</th>
      <td>10591</td>
      <td>44.1</td>
    </tr>
    <tr>
      <th>bug</th>
      <td>4644</td>
      <td>19.4</td>
    </tr>
    <tr>
      <th>misconfiguration</th>
      <td>3498</td>
      <td>14.6</td>
    </tr>
    <tr>
      <th>feature_request</th>
      <td>2237</td>
      <td>9.3</td>
    </tr>
    <tr>
      <th>feedback</th>
      <td>1288</td>
      <td>5.4</td>
    </tr>
    <tr>
      <th>billing</th>
      <td>895</td>
      <td>3.7</td>
    </tr>
    <tr>
      <th>outage</th>
      <td>764</td>
      <td>3.2</td>
    </tr>
    <tr>
      <th>security</th>
      <td>77</td>
      <td>0.3</td>
    </tr>
    <tr>
      <th rowspan="5" valign="top">routing</th>
      <th>kb_autoresolve</th>
      <td>14089</td>
      <td>58.7</td>
    </tr>
    <tr>
      <th>engineering</th>
      <td>6881</td>
      <td>28.7</td>
    </tr>
    <tr>
      <th>sales_success</th>
      <td>1924</td>
      <td>8.0</td>
    </tr>
    <tr>
      <th>security_incident</th>
      <td>841</td>
      <td>3.5</td>
    </tr>
    <tr>
      <th>retention</th>
      <td>259</td>
      <td>1.1</td>
    </tr>
  </tbody>
</table>
</div>




```python
freq_table("priority", ["low", "medium", "high", "critical"])
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>conteo</th>
      <th>pct_%</th>
    </tr>
    <tr>
      <th>priority</th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>low</th>
      <td>14116</td>
      <td>58.8</td>
    </tr>
    <tr>
      <th>medium</th>
      <td>5935</td>
      <td>24.7</td>
    </tr>
    <tr>
      <th>high</th>
      <td>3051</td>
      <td>12.7</td>
    </tr>
    <tr>
      <th>critical</th>
      <td>892</td>
      <td>3.7</td>
    </tr>
  </tbody>
</table>
</div>



### Cruce: topic × type

Qué *tipos* de ticket aparecen en qué *áreas* del producto — conteos, con totales.


```python
pd.crosstab(df.topic, df.type, margins=True, margins_name="Total")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>type</th>
      <th>billing</th>
      <th>bug</th>
      <th>feature_request</th>
      <th>feedback</th>
      <th>how_to</th>
      <th>misconfiguration</th>
      <th>outage</th>
      <th>security</th>
      <th>Total</th>
    </tr>
    <tr>
      <th>topic</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>alerts</th>
      <td>0</td>
      <td>571</td>
      <td>908</td>
      <td>0</td>
      <td>901</td>
      <td>685</td>
      <td>0</td>
      <td>0</td>
      <td>3065</td>
    </tr>
    <tr>
      <th>attribution</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>859</td>
      <td>918</td>
      <td>0</td>
      <td>0</td>
      <td>1777</td>
    </tr>
    <tr>
      <th>billing</th>
      <td>895</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>771</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1666</td>
    </tr>
    <tr>
      <th>connectors</th>
      <td>0</td>
      <td>2031</td>
      <td>1329</td>
      <td>0</td>
      <td>4614</td>
      <td>853</td>
      <td>0</td>
      <td>0</td>
      <td>8827</td>
    </tr>
    <tr>
      <th>dashboards</th>
      <td>0</td>
      <td>1468</td>
      <td>0</td>
      <td>1288</td>
      <td>1080</td>
      <td>0</td>
      <td>764</td>
      <td>0</td>
      <td>4600</td>
    </tr>
    <tr>
      <th>northstar</th>
      <td>0</td>
      <td>51</td>
      <td>0</td>
      <td>0</td>
      <td>553</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>604</td>
    </tr>
    <tr>
      <th>reports</th>
      <td>0</td>
      <td>523</td>
      <td>0</td>
      <td>0</td>
      <td>890</td>
      <td>527</td>
      <td>0</td>
      <td>0</td>
      <td>1940</td>
    </tr>
    <tr>
      <th>users_workspace</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>923</td>
      <td>515</td>
      <td>0</td>
      <td>77</td>
      <td>1515</td>
    </tr>
    <tr>
      <th>Total</th>
      <td>895</td>
      <td>4644</td>
      <td>2237</td>
      <td>1288</td>
      <td>10591</td>
      <td>3498</td>
      <td>764</td>
      <td>77</td>
      <td>23994</td>
    </tr>
  </tbody>
</table>
</div>



### Cruce: routing × priority


```python
ct = pd.crosstab(df.routing, df.priority, margins=True, margins_name="Total")
ct[["low", "medium", "high", "critical", "Total"]]
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>priority</th>
      <th>low</th>
      <th>medium</th>
      <th>high</th>
      <th>critical</th>
      <th>Total</th>
    </tr>
    <tr>
      <th>routing</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>engineering</th>
      <td>2237</td>
      <td>2437</td>
      <td>2156</td>
      <td>51</td>
      <td>6881</td>
    </tr>
    <tr>
      <th>kb_autoresolve</th>
      <td>10591</td>
      <td>3498</td>
      <td>0</td>
      <td>0</td>
      <td>14089</td>
    </tr>
    <tr>
      <th>retention</th>
      <td>0</td>
      <td>0</td>
      <td>259</td>
      <td>0</td>
      <td>259</td>
    </tr>
    <tr>
      <th>sales_success</th>
      <td>1288</td>
      <td>0</td>
      <td>636</td>
      <td>0</td>
      <td>1924</td>
    </tr>
    <tr>
      <th>security_incident</th>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>841</td>
      <td>841</td>
    </tr>
    <tr>
      <th>Total</th>
      <td>14116</td>
      <td>5935</td>
      <td>3051</td>
      <td>892</td>
      <td>23994</td>
    </tr>
  </tbody>
</table>
</div>



## 4. Sentiment — señal operativa de priorización


```python
order = ["neutral", "confused", "overwhelmed", "frustrated", "angry", "anxious"]
vc = (df["sentiment"].value_counts().reindex(order) / len(df) * 100)
ax = vc.plot(kind="bar", figsize=(9, 4), color=ACCENT, width=0.8)
ax.set_title("Distribución de sentiment", fontweight="bold")
ax.set_ylabel("% de tickets"); ax.set_xlabel(""); ax.tick_params(axis="x", rotation=30)
plt.tight_layout(); plt.show()
```


    
![png](eda_v2_es_files/eda_v2_es_27_0.png)
    


**Cómo leerlo:** el sentiment se trata como señal **operativa**, no como verdad
sobre la emoción — alimenta la *priorización* (llegar más rápido al cliente furioso o
ansioso) y la adaptación del tono. Por eso la métrica que importa es el recall en las
emociones que disparan acción, no el accuracy crudo.

## 5. Ruido de intake — por qué el clasificador de triage vale la pena

`reported_category` es la casilla que el propio cliente elige al enviar el ticket —
gruesa y a menudo equivocada. `aligned_category(topic, type)` es la casilla que
*debería* haber elegido si se auto-clasificara bien. La brecha entre las dos es el
margen que un modelo recupera leyendo el texto.


```python
df["aligned"] = [aligned_category(t, ty) for t, ty in zip(df.topic, df.type)]
df["intake_ok"] = df.reported_category == df.aligned
print(f"desajuste de intake global: {(~df.intake_ok).mean()*100:.1f}% de los tickets "
      f"eligen una categoría que NO coincide con las etiquetas reales")
```

    desajuste de intake global: 35.1% de los tickets eligen una categoría que NO coincide con las etiquetas reales


Tasa de desajuste por topic real — dónde más se equivoca el usuario:


```python
g = df.groupby("topic")["intake_ok"]
noise = pd.DataFrame({"n": g.size(), "desajuste_%": ((1 - g.mean()) * 100).round(1)})
noise.sort_values("desajuste_%", ascending=False)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>n</th>
      <th>desajuste_%</th>
    </tr>
    <tr>
      <th>topic</th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>reports</th>
      <td>1940</td>
      <td>37.8</td>
    </tr>
    <tr>
      <th>attribution</th>
      <td>1777</td>
      <td>36.8</td>
    </tr>
    <tr>
      <th>billing</th>
      <td>1666</td>
      <td>35.8</td>
    </tr>
    <tr>
      <th>dashboards</th>
      <td>4600</td>
      <td>35.6</td>
    </tr>
    <tr>
      <th>connectors</th>
      <td>8827</td>
      <td>34.5</td>
    </tr>
    <tr>
      <th>users_workspace</th>
      <td>1515</td>
      <td>34.1</td>
    </tr>
    <tr>
      <th>alerts</th>
      <td>3065</td>
      <td>33.9</td>
    </tr>
    <tr>
      <th>northstar</th>
      <td>604</td>
      <td>32.8</td>
    </tr>
  </tbody>
</table>
</div>



**Cómo leerlo:** cerca de un tercio de los tickets llega mal categorizado por el
usuario. Un modelo que lee el *texto* y predice el topic/type verdadero convierte ese
intake ruidoso en una señal de ruteo confiable — ese es el valor de negocio concreto,
no el accuracy por sí mismo.

## 6. Impacto de los eventos en la severidad

La mezcla de prioridad **dentro de las ventanas de evento** vs el **flujo base** hace
explícito el efecto de la capa de eventos.


```python
sev = pd.DataFrame({
    "base_%": (df[~df.is_event].priority.value_counts(normalize=True) * 100).round(1),
    "evento_%": (df[df.is_event].priority.value_counts(normalize=True) * 100).round(1),
}).reindex(["low", "medium", "high", "critical"])
sev
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>base_%</th>
      <th>evento_%</th>
    </tr>
    <tr>
      <th>priority</th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>low</th>
      <td>60.7</td>
      <td>53.3</td>
    </tr>
    <tr>
      <th>medium</th>
      <td>29.5</td>
      <td>10.4</td>
    </tr>
    <tr>
      <th>high</th>
      <td>8.9</td>
      <td>24.1</td>
    </tr>
    <tr>
      <th>critical</th>
      <td>0.9</td>
      <td>12.1</td>
    </tr>
  </tbody>
</table>
</div>



**Cómo leerlo:** los tickets por evento se cargan notoriamente hacia
high/critical frente a la base tranquila — el pico de severidad que produce un
incidente real, y la señal en la que se fija un detector de anomalías. Fíjate que la
base sola queda ~60/30/9/1 (el objetivo de diseño); toda la desviación global viene
de los eventos.

## 7. Largo del mensaje


```python
df["body_len"] = df["body"].fillna("").str.len()
ax = df["body_len"].plot(kind="hist", bins=60, figsize=(9, 4), color=BASE_C,
                         edgecolor="white")
ax.axvline(df.body_len.median(), color=EVT_C, ls="--",
           label=f"mediana {int(df.body_len.median())} chars")
ax.set_title("Largo del cuerpo del ticket (caracteres)", fontweight="bold")
ax.set_xlabel("caracteres"); ax.legend()
plt.tight_layout(); plt.show()
```


    
![png](eda_v2_es_files/eda_v2_es_38_0.png)
    


**Cómo leerlo:** una distribución sesgada a la derecha — muchos mensajes cortos
de chat, una cola larga de correos detallados — igual que el perfil de largo medido
en datasets públicos reales durante la calibración.

## Qué habilita este dataset

- **Clasificación de triage** — predecir topic / type / priority / routing /
  sentiment desde el texto crudo (etiquetas verdaderas coherentes por construcción).
- **Deflexión con RAG** — la masa `kb_autoresolve` es donde un asistente RAG anclado
  y con rechazo honesto se gana el sueldo.
- **Series de tiempo** — los picos de outage y las olas de lanzamiento hacen
  aprendibles el **pronóstico** de volumen y la **detección de anomalías**, cosa que
  un set sintético plano no soporta.

*Dato sintético, generado con un pipeline real. Sin usuarios reales, sin PII.*
