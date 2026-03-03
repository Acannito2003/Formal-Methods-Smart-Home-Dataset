import streamlit as st
import pandas as pd
import os
import pm4py    #motore process mining
from pm4py.algo.discovery.alpha import algorithm as alpha_miner
from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.algo.evaluation.generalization import algorithm as generalization_evaluator
from pm4py.algo.evaluation.simplicity import algorithm as simplicity_evaluator
import ollama
import tempfile


st.set_page_config(layout="wide", page_title="Process Mining SMART HOME", page_icon="📊")
st.markdown("<h1 style='text-align: center;'>Process Mining SMART HOME</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
st.markdown(
    """
    <div style='text-align: center; margin-top: -10px; margin-bottom: 20px;'>
        <span style='font-size: 50px;'>🏠</span>
        <span style='font-size: 30px; vertical-align: top; color: #FFD700;'>💡</span>
        <p style='color: #666; font-style: italic;'>AI-Powered Smart Home Analytics</p>
    </div>
    """,
    unsafe_allow_html=True
)
if uploaded_file:
    df_varianti = pd.DataFrame(columns=["Variant", "Count"])  # Initial placeholder
    algo_scelto = "Not selected"
    fitness_score = 0.0
    precision_score = 0.0   #per evitare errori di variabili inesistenti per ollama


    # Carichiamo il file originale e mostriamo le prime 20 righe
    df_raw = pd.read_csv(uploaded_file, sep=None, engine='python')
    st.dataframe(df_raw.head(20))
    st.write(f"Total rows: {len(df_raw)} | Total columns: {len(df_raw.columns)}")

    # 1. Identifichiamo il nome della prima colonna
    nome_prima_colonna = df_raw.columns[0]
    # 2. Convertiamo la colonna forzando i valori non numerici a NaN (errori='coerce')
    # Questo evita il crash se Pandas legge stringhe invece di numeri
    valori_numerici = pd.to_numeric(df_raw[nome_prima_colonna], errors='coerce')
    # 3. Trasformiamo in datetime
    temp_dt = pd.to_datetime(valori_numerici, unit='s')
    # 4. Inseriamo le colonne trasformate
    df_raw.insert(0, 'Date', temp_dt.dt.strftime('%Y-%m-%d'))
    df_raw.insert(1, 'Time', temp_dt.dt.strftime('%H:%M:%S'))
    # 5. Rimuoviamo la colonna originale
    df_raw = df_raw.drop(columns=[nome_prima_colonna])

    # Rimuoviamo le colonne se esistono nel file
    colonne_da_cancellare = [
        nome_prima_colonna,
        'Transaction_ID',
        'Month',
        'Day of the Week',
        'Hour of the Day',
        'Offloading Decision'
    ]
    df_raw = df_raw.drop(columns=[c for c in colonne_da_cancellare if c in df_raw.columns])


    #chiedo a utente di inserire quante righe vuole far rimanere
    num_righe = st.number_input(
        "Insert the number of rows (Max 48972):",
        min_value=1,
        max_value=48972,
        value=1000
    )

    # Applica il limite al dataframe
    df_raw = df_raw.iloc[:num_righe]

    # Visualizzaziamo il dataset processato con orario in formato data e ora e limitazione a 1000 righe
    st.success("Dataset Processed Successfully")
    st.dataframe(df_raw, use_container_width=True)
    st.write(f"Total rows: {len(df_raw)} | Total columns: {len(df_raw.columns)}")

    #utente decide quale colonne tenere
    st.write("Columns mapping")
    all_raw_cols = df_raw.columns.tolist()
    cols_to_keep = st.multiselect("Select columns to keep:", options=all_raw_cols, default=all_raw_cols)

    if cols_to_keep:
        new_column_names = {}
        cols_ui = st.columns(len(cols_to_keep))
        for i, col_idx in enumerate(cols_to_keep):
            with cols_ui[i]:
                friendly_name = st.text_input(f" Col {col_idx}", value=f"Data_{col_idx}", key=f"ren_{col_idx}")
                new_column_names[col_idx] = friendly_name

        df_final = df_raw[cols_to_keep].rename(columns=new_column_names)
    #se si vuole rinominare i nomi degli elettrodomestici data+nome nuovo

     # Cerchiamo il nome attuale della colonna Date (se è stata rinominata)
    nome_colonna_data = new_column_names.get('Date', 'Date')

    if nome_colonna_data in df_final.columns:
        # 1. Ricaviamo le date uniche e le convertiamo in stringa per la lista
        date_unice = pd.to_datetime(df_final[nome_colonna_data]).dt.date.unique()
        date_unice.sort()

        # 2. Creiamo una lista di opzioni: la prima è "All Days"
        opzioni_filtro = ["All Days"] + [str(d) for d in date_unice]

        # 3. Widget Selectbox
        scelta = st.selectbox("Filter by day",options=opzioni_filtro)

        # 4. Applichiamo il filtro solo se non è selezionato "All Days"
        if scelta != "All Days":
            df_final = df_final[df_final[nome_colonna_data] == scelta]
            st.info(f"Filter applied: **{scelta}**. Rows: {len(df_final)}")
        else:
            st.success(f" ({len(df_final)} rows).")
    else:
        st.warning("date not found")
    #menu a tendina con i giorni

    # --- Sezione Filtraggio per Fascia Oraria ---
    st.write("Filter by time range")

    # Cerchiamo il nome attuale della colonna Time (se è stata rinominata)
    nome_colonna_ora = new_column_names.get('Time', 'Time')

    if nome_colonna_ora in df_final.columns:
        # Creazione dello slider per le ore (0-23)

        fascia_oraria = st.slider(
            "Select the interval of time:",
            min_value=0,
            max_value=23,
            value=(0, 23)
        )

        # Estraiamo solo l'ora (come numero intero) per il filtraggio
        # Convertiamo temporaneamente in datetime per estrarre l'ora se è stringa
        ore_estratte = pd.to_datetime(df_final[nome_colonna_ora], format='%H:%M:%S').dt.hour

        # Applichiamo il filtro sul dataframe
        df_final = df_final[(ore_estratte >= fascia_oraria[0]) & (ore_estratte <= fascia_oraria[1])]
        st.info(f"Remaining rows after filtering: **{len(df_final)}**")
    else:
        st.warning("Column 'Time' not found.")



    # Lista degli elettrodomestici da filtrare
    elettrodomestici = ['Data_Television', 'Data_Dryer', 'Data_Oven', 'Data_Refrigerator', 'Data_Microwave']

    st.write("### Filter Appliances Status")

    # Creiamo una riga di colonne per i widget, così l'interfaccia rimane compatta

    cols_filtri = st.columns(len(elettrodomestici))

    for i, appliance in enumerate(elettrodomestici):
        # Verifichiamo se la colonna esiste nel dataframe finale
        if appliance in df_final.columns:
            with cols_filtri[i]:
                stato = st.radio(
                    f"Status {appliance.replace('Data_', '')}",
                    options=["All", "0", "1"],
                    key=f"filter_{appliance}",
                    horizontal=True
                )

                # Applichiamo il filtro se non è selezionato "All"
                if stato == "0":
                    df_final = df_final[df_final[appliance].astype(str) == "0"]
                elif stato == "1":
                    df_final = df_final[df_final[appliance].astype(str) == "1"]
        else:
            # Messaggio opzionale se la colonna manca nel mapping
            st.caption(f"⚠️ {appliance} not found")

    # Riepilogo finale dopo tutti i filtri applicati
    st.info(f"Remaining rows after appliance filtering: **{len(df_final)}**")

    # --- Sezione Filtraggio Parametri Elettrici ---
    st.write("### Filter Electrical Parameters")

    # Lista dei parametri numerici (mappati con Data_)
    parametri_elettrici = [
        'Data_Line Voltage',
        'Data_Voltage',
        'Data_Apparent Power',
        'Data_Energy Consumption (kWh)'
    ]

    # Creiamo due colonne per rendere il layout più compatto
    col_elettriche = st.columns(2)

    for i, param in enumerate(parametri_elettrici):
        if param in df_final.columns:
            # Calcoliamo min e max reali per impostare i limiti dello slider
            val_min = float(df_final[param].min())
            val_max = float(df_final[param].max())

            # Se il min e il max sono uguali, lo slider non serve
            if val_min == val_max:
                st.caption(f"⚠️ {param} has a constant value: {val_min}")
                continue

            with col_elettriche[i % 2]:  # Alterna tra la prima e la seconda colonna
                intervallo = st.slider(
                    f"Select range for {param.replace('Data_', '')}",
                    min_value=val_min,
                    max_value=val_max,
                    value=(val_min, val_max),  # Di default seleziona tutto il range
                    key=f"slider_{param}",
                    step=0.1
                )

                # Applichiamo il filtro
                df_final = df_final[
                    (df_final[param] >= intervallo[0]) &
                    (df_final[param] <= intervallo[1])
                    ]
        else:
            st.caption(f"⚠️ {param} not found in mapping.")

    # Riepilogo finale aggiornato
    st.info(f"Remaining rows after electrical filters: **{len(df_final)}**")

    # Mostriamo il dataset filtrato finale
    st.dataframe(df_final, use_container_width=True)



    # --- PREPARAZIONE DATI PER IL MINING (LOG GENERATION) ---
    nome_data = new_column_names.get('Date', 'Date')  #cerco nome colonna data e ora
    nome_ora = new_column_names.get('Time', 'Time')
    colonne_escluse = [nome_data, nome_ora, 'Data_Line Voltage', 'Data_Voltage', 'Data_Apparent Power',
                       'Data_Energy Consumption (kWh)']
    activity_cols = [col for col in df_final.columns if col.startswith('Data_') and col not in colonne_escluse]
    #rimangono gli elettrodomestici

    # Inizializziamo log_df come None per evitare il NameError,creo un dataframe vuoto
    log_df = pd.DataFrame()

    if not df_final.empty:
        # 1 definisco cosa escludere
        colonne_escluse = [nome_colonna_data, nome_colonna_ora, 'Data_Line Voltage', 'Data_Voltage',
                           'Data_Apparent Power', 'Data_Energy Consumption (kWh)']

        # 2. Trova le colonne delle attività
        activity_cols = [col for col in df_final.columns if col.startswith('Data_') and col not in colonne_escluse]

        # 3. Estrai gli eventi
        event_list = []
        df_mining = df_final.sort_values([nome_colonna_data, nome_colonna_ora])

        for col in activity_cols:
            activations = df_mining[pd.to_numeric(df_mining[col], errors='coerce').fillna(0).astype(int) == 1]
            for _, row in activations.iterrows():
                event_list.append({
                    'case:concept:name': row[nome_colonna_data],
                    'concept:name': col.replace('Data_', ''),
                    'time:timestamp': pd.to_datetime(row[nome_colonna_data] + ' ' + row[nome_colonna_ora])
                })

        # 4. Crea il log finale
        if event_list:
            log_df = pd.DataFrame(event_list)
            st.header("Process Discovery")
            # Da qui procedi con gli algoritmi...

            # --- ESECUZIONE ALGORITMI ---
            if not log_df.empty:
                # Layout con due colonne: sinistra per parametri, destra per il grafico
                col_params, col_graph = st.columns([1, 4])

                with col_params:
                    algo_scelto = st.radio("Choose Algorithm:", ["Alpha Miner", "Heuristic Miner", "Inductive Miner"])

                    # Parametro dinamico per Heuristic
                    h_threshold = 0.5
                    if algo_scelto == "Heuristic Miner":
                        h_threshold = st.slider("Dependency Threshold", 0.0, 1.0, 0.5)
                        #se è alto mostra abitudini forti, ignorando azioni casuali
                with st.spinner(f"Running {algo_scelto}..."):
                    log_pm4py = pm4py.format_dataframe(log_df, case_id='case:concept:name', activity_key='concept:name',
                                                       timestamp_key='time:timestamp')

                    if algo_scelto == "Alpha Miner":
                        net, im, fm = alpha_miner.apply(log_pm4py)

                    elif algo_scelto == "Heuristic Miner":
                        net, im, fm = heuristics_miner.apply(log_pm4py, parameters={
                            heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: h_threshold
                        })

                    else:  # Inductive Miner
                        net, im, fm = pm4py.discover_petri_net_inductive(log_pm4py)

                    # Generazione Gviz
                    gviz = pn_visualizer.apply(net, im, fm)
                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    tmp_path = tmp_file.name

                    try:
                        tmp_file.close()  # Chiude per permettere scrittura a Graphviz
                        pn_visualizer.save(gviz, tmp_path)

                        # Usiamo la colonna grande per mostrare l'immagine
                        with col_graph:
                            st.image(tmp_path, caption=f"Result: {algo_scelto}", use_container_width=True)
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)

                            st.markdown("---")
                            st.subheader(f"📊 Evaluation of the model: {algo_scelto}")

                            with st.spinner("Computing metrics..."):
                                try:
                                    # Calcolo Fitness
                                    fitness_result = pm4py.fitness_token_based_replay(log_pm4py, net, im, fm)
                                    fitness_score = fitness_result['average_trace_fitness']

                                    # Calcolo Precision
                                    precision_score = pm4py.precision_token_based_replay(log_pm4py, net, im, fm)

                                    # Calcolo Generalization
                                    generalization_score = generalization_evaluator.apply(log_pm4py, net, im, fm)

                                    # Calcolo Simplicity
                                    simplicity_score = simplicity_evaluator.apply(net)

                                    # Visualizzazione metriche in 4 colonne
                                    m1, m2, m3, m4 = st.columns(4)
                                    m1.metric("Fitness", f"{round(fitness_score * 100, 2)}%")
                                    m2.metric("Precision", f"{round(precision_score * 100, 2)}%")
                                    m3.metric("Generalization", f"{round(generalization_score * 100, 2)}%")
                                    m4.metric("Simplicity", f"{round(simplicity_score * 100, 2)}%")

                                    with st.expander("🔬 Technical details: How are these calculated?"):
                                        st.markdown(f"""
                                        ### 1. Fitness Calculation
                                        The algorithm 'replays' the sequences of Smart Home events onto the Petri Net.
                                        * **Logic:** It starts with a 'token' in the initial state. For every real event (e.g., *TV ON*), it checks if the model allows it.
                                        * **Result:** **100% Fitness** means every single sensor activation in the file is perfectly explained by the graph.
                            
                                        ### 2. Precision Calculation
                                        Precision checks if the model is 'too loose' (allowing things that never happen).
                                        * **Logic:** At each step, it compares what the model **could** do versus what the data **actually** did.
                                        * **Result:** **High Precision** means the model is strict and accurately represents specific household habits.
                            
                                        ### 3. Generalization Calculation
                                        Generalization measures how well the model can describe future, unseen behavior of the system.
                                        * **Logic:** It evaluates if the model is too "fitted" to the current log (overfitting). If a transition is rarely used, the model might be too specific.
                                        * **Result:** **High Generalization** suggests the model is robust and can predict general household patterns beyond the specific sample provided.
                            
                                        ### 4. Simplicity Calculation
                                        Simplicity follows "Occam's Razor": the simplest model that explains the data is usually the best.
                                        * **Logic:** analyze the complexity of connections between places and transitions.
                                        * **Result:** **High Simplicity** means the model is easy to read and lacks unnecessary "spaghetti" structures or redundant nodes.
                                        """)
                                except Exception as e:
                                    st.warning(f"Error calculating metrics: {e}")
                st.success(f"Analysis with {algo_scelto} completed!")
            else:
                st.warning("No events found. Adjust your filters.")


                if 'log_pm4py' in locals() and not log_df.empty:
                    try:
                        # Calcolo unico delle varianti
                        variants = pm4py.get_variants_as_tuples(log_pm4py)
                        variants_list = []
                        for variant, occurrences in variants.items():
                            count = occurrences if isinstance(occurrences, int) else len(occurrences)
                            variants_list.append({
                                "Variant": " -> ".join(variant),
                                "Count": count
                            })
                        # Creazione del DataFrame finale per l'AI
                        df_varianti = pd.DataFrame(variants_list).sort_values(by="Count", ascending=False).head(5)
                    except Exception as e:
                        st.error(f"Errore nel calcolo delle varianti: {e}")
                        df_varianti = pd.DataFrame(columns=["Variant", "Count"])



        # --- SEZIONE CHATBOX AI (OLLAMA) ---
        st.markdown("---")
        st.header("💬 Chat with local AI (Ollama)")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt_utente := st.chat_input("Ask me something about your model..."):
            st.session_state.messages.append({"role": "user", "content": prompt_utente})
            with st.chat_message("user"):
                st.markdown(prompt_utente)

                # Prepariamo il contesto tecnico avanzato
                top_varianti_str = df_varianti.to_string(index=False) if not df_varianti.empty else "No variants found"
                #trasforma la tabella in testo che l'Ai può comprendere meglio

                contesto_tecnico = f"""
                You are a Senior Process Mining Consultant & Smart Home Data Scientist.

                CURRENT CONTEXT:
                - Algorithm Used: {algo_scelto}
                - Model Fitness: {round(fitness_score * 100, 2)}%
                - Model Precision: {round(precision_score * 100, 2)}%
                - Model Generalization: {round(generalization_score * 100, 2)}%
                - Model Simplicity: {round(simplicity_score * 100, 2)}%
                - Top 5 Household Routines: 
                {top_varianti_str}

                YOUR TASKS:
                1. GENERATE REPORTS: Summarize the household behavior based on the metrics.
                2. FIND ANOMALIES: Identify low fitness areas or unusual appliance sequences.
                3. OPTIMIZE: Suggest energy-saving patterns or more efficient routines.
                4. PREDICT: Based on the Top Routines, suggest what the next activity might be if a sequence starts.
                5. INCREMENTAL LEARNING: Explain how the model should learn from the errors.
                6. PROJECT REVIEW: Critique the current process discovery result.

                INSTRUCTIONS:
                - Be technical, precise, and professional.
                - Always provide actionable insights for Smart Home optimization.
                - Answer in English.
                """

            with st.chat_message("assistant"):
                try:
                    # Chiamata a Ollama 
                    response = ollama.chat(model='llama3', messages=[
                        {'role': 'system', 'content': contesto_tecnico},
                        {'role': 'user', 'content': prompt_utente},
                    ])

                    risposta_ai = response['message']['content']
                    st.markdown(risposta_ai)
                    st.session_state.messages.append({"role": "assistant", "content": risposta_ai})

                except Exception as e:
                    st.error(f"Ollama Error: {e}. Make sure Ollama is running (ollama run llama3)")