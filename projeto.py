import streamlit as st
from pulp import LpMaximize, LpMinimize, LpProblem, LpVariable, lpSum, value, LpStatus


st.set_page_config(page_title="Simplex com Análise de RHS", layout="centered")
st.title("Simplex + Análise de Recursos (RHS)")

st.header("1️⃣ Definir o Modelo")

num_vars = int(st.number_input("Número de variáveis", 2, 4, 2))
num_constraints = int(st.number_input("Número de restrições", 1, 5, 2))

st.subheader("Função Objetivo")
cols = st.columns(num_vars)
objective_coeffs = []
for i in range(num_vars):
    with cols[i]:
        val = st.number_input(f"Coef. de X{i+1}", key=f"obj_{i}")
        objective_coeffs.append(val)

direction = st.selectbox("Maximizar ou Minimizar?", ["Maximizar", "Minimizar"])

st.subheader("Restrições")
constraints = []
for i in range(num_constraints):
    st.markdown(f"**Restrição {i+1}**")
    cols = st.columns(num_vars + 2)

    coefs = []
    for j in range(num_vars):
        with cols[j]:
            coef = st.number_input(f"Coef. de x{j+1}", key=f"coef_{i}_{j}")
            coefs.append(coef)

    with cols[-2]:
        op = st.selectbox(
            "Operador",
            ["≤", "≥"],
            key=f"op_{i}"
        )

    with cols[-1]:
        rhs = st.number_input("Lado direito", key=f"rhs_{i}")

    constraints.append((coefs, op, rhs))

if st.button("Resolver"):

    model = LpProblem("Simplex_Model", LpMaximize if direction == "Maximizar" else LpMinimize)

    vars = [LpVariable(f"x{i+1}", lowBound=0) for i in range(num_vars)]

    model += lpSum([objective_coeffs[i] * vars[i] for i in range(num_vars)])

    for idx, (coefs, op, rhs) in enumerate(constraints):
        expr = lpSum([coefs[i] * vars[i] for i in range(num_vars)])
        if op == "≤":
            model += expr <= rhs, f"rest_{idx+1}"
        elif op == "≥":
            model += expr >= rhs, f"rest_{idx+1}"

    model.solve()

    st.session_state.saved_model = {
        "num_vars": num_vars,
        "num_constraints": num_constraints,
        "objective_coeffs": objective_coeffs,
        "direction": direction,
        "constraints": constraints,
        "optimal_value": value(model.objective)
    }

    st.subheader("📊 Resultado Inicial")
    st.write(f"Status: {LpStatus[model.status]}")
    st.write(f"Valor ótimo: {value(model.objective)}")

    for var in vars:
        st.write(f"{var.name} = {var.value()}")

    st.subheader("💡 Preços Sombra")
    for name, constraint in model.constraints.items():
        st.write(f"{name}: {constraint.pi:.2f} (Folga: {constraint.slack:.2f})")

    st.session_state.rhs_values = [rhs for (_, _, rhs) in constraints]

if "saved_model" in st.session_state:
    st.header("2️⃣ Alterar Lado direito e Recalcular")

    model_data = st.session_state.saved_model
    num_vars = model_data["num_vars"]
    constraints = model_data["constraints"]
    
    new_rhs = []
    st.subheader("Novo lado direito para cada restrição:")
    for idx, (coefs, op, rhs) in enumerate(constraints):
        val = st.number_input(
            f"Restrição {idx+1} (anterior: {rhs})",
            value=st.session_state.rhs_values[idx] if "rhs_values" in st.session_state else rhs,
            key=f"rhs_new_{idx}"
        )
        new_rhs.append(val)

    if st.button("Recalcular"):
        st.session_state.rhs_values = new_rhs

        model = LpProblem(
            "Simplex_Model", 
            LpMaximize if model_data["direction"] == "Maximizar" else LpMinimize
        )

        vars = [LpVariable(f"x{i+1}", lowBound=0) for i in range(num_vars)]

        model += lpSum([model_data["objective_coeffs"][i] * vars[i] for i in range(num_vars)])

        for idx, (constraint, rhs_value) in enumerate(zip(constraints, new_rhs)):
            coefs, op, _ = constraint
            expr = lpSum([coefs[i] * vars[i] for i in range(num_vars)])
            if op == "≤":
                model += expr <= rhs_value, f"rest_{idx+1}"
            elif op == "≥":
                model += expr >= rhs_value, f"rest_{idx+1}"

        model.solve()

        previous_profit = st.session_state.saved_model.get("optimal_value")
        current_profit = value(model.objective)

        st.subheader("📊 Novo Resultado")
        st.write(f"Status: {LpStatus[model.status]}")
        st.write(f"💰 Valor ótimo anterior: {previous_profit}")
        st.write(f"💰 Novo valor ótimo: {current_profit}")

        if direction == 'Maximizar':
            viavel = current_profit > previous_profit
        else:
            viavel = current_profit < previous_profit

        st.subheader(f"🔍 Avaliação da Troca: {'Viável' if viavel else 'Não Viável'}")

        for var in vars:
            st.write(f"{var.name} = {var.value()}")

        st.subheader("💡 Novos Preços Sombra")
        for name, constraint in model.constraints.items():
            st.write(f"{name}: {constraint.pi:.2f} (Folga: {constraint.slack:.2f})")
