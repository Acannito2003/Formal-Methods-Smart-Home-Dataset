# AI-Powered Process Mining for Smart Home Analytics 🏠📊

Questo progetto applica tecniche di **Process Mining** e **Intelligenza Artificiale** per trasformare i log grezzi di una Smart Home in insight comportamentali comprensibili. Partendo da circa **49.000 eventi IoT**, il sistema ricostruisce i flussi di utilizzo degli elettrodomestici e ne valuta la conformità.

---

## 🚀 Caratteristiche Principali

* **Discovery Automatizzata:** Utilizzo di algoritmi come *Alpha Miner*, *Inductive Miner* e *Heuristic Miner* per mappare l'uso dei dispositivi.
* **Analisi Quantitativa:** Monitoraggio di parametri elettrici come *Line Voltage*, *Apparent Power* e *Energy Consumption* ($kWh$).
* **AI Consultant:** Integrazione con **Ollama (Llama 3)** per generare report automatici e suggerimenti di ottimizzazione energetica.
* **Dashboard Interattiva:** Interfaccia sviluppata in **Streamlit** per la visualizzazione dinamica dei grafici e dei Petri Nets.

---

## 📂 Il Dataset
Il dataset utilizzato contiene **48.972 log** relativi a 5 elettrodomestici principali:
1.  **Television**
2.  **Dryer**
3.  **Oven**
4.  **Refrigerator**
5.  **Microwave**

> [!IMPORTANT]
> **Fonte dei dati:** [Kaggle - Smart Home Dataset](https://www.kaggle.com/datasets/pythonafroz/smart-home-dataset)

---

## 🛠️ Tech Stack

| Componente | Tecnologia |
| :--- | :--- |
| **Core** | Python (Pandas, PM4Py) |
| **Frontend** | Streamlit |
| **AI/LLM** | Ollama (Llama 3) |
| **Metodi Formali** | Analisi di Fitness, Precision, Generalization e Simplicity |

