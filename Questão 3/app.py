import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

TAXA_MULTA_DIARIA = 2.5  # % ao dia


def formatar_br(valor):
    """Formata um número como moeda brasileira (R$ 1.234,56)."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_data(texto):
    """Converte uma data no formato DD/MM/AAAA para um objeto date."""
    return datetime.strptime(texto.strip(), "%d/%m/%Y").date()


def calcular_juros(valor, data_vencimento, data_hoje):
    """Calcula os juros (multa de 2,5% ao dia) sobre um valor em atraso.

    Retorna uma tupla (dias_atraso, juros, total).
    """
    dias_atraso = (data_hoje - data_vencimento).days
    if dias_atraso < 0:
        dias_atraso = 0

    juros = valor * (TAXA_MULTA_DIARIA / 100.0) * dias_atraso
    total = valor + juros
    return dias_atraso, juros, total


class AppJuros:
    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Cálculo de Juros por Atraso")
        self.raiz.geometry("520x420")
        self.raiz.resizable(False, False)

        self.var_valor = tk.StringVar()
        self.var_vencimento = tk.StringVar()
        self.var_resultado = tk.StringVar()

        self._montar_interface()

    def _montar_interface(self):
        # --- Entrada de dados ---
        quadro_dados = ttk.LabelFrame(self.raiz, text="Dados do título", padding=12)
        quadro_dados.pack(fill="x", padx=12, pady=(12, 8))

        ttk.Label(quadro_dados, text="Valor (R$):").grid(row=0, column=0, sticky="w", pady=4)
        self.entrada_valor = ttk.Entry(quadro_dados, textvariable=self.var_valor, width=22)
        self.entrada_valor.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(quadro_dados, text="Data de vencimento:").grid(row=1, column=0, sticky="w", pady=4)
        self.entrada_vencimento = ttk.Entry(quadro_dados, textvariable=self.var_vencimento, width=22)
        self.entrada_vencimento.grid(row=1, column=1, sticky="w", padx=8, pady=4)
        self.var_vencimento.trace_add("write", self._aplicar_mascara_data)

        ttk.Label(quadro_dados, text="Multa diária:").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Label(quadro_dados, text=f"{TAXA_MULTA_DIARIA:.1f}% ao dia").grid(
            row=2, column=1, sticky="w", padx=8, pady=4)

        self.botao_calcular = ttk.Button(
            quadro_dados, text="Calcular Juros", command=self.calcular)
        self.botao_calcular.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # --- Resultado ---
        quadro_resultado = ttk.LabelFrame(self.raiz, text="Resultado", padding=12)
        quadro_resultado.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.rotulo_resultado = ttk.Label(
            quadro_resultado,
            text="Informe o valor e a data de vencimento e clique em Calcular Juros.",
            justify="left",
            wraplength=460,
        )
        self.rotulo_resultado.pack(anchor="w", fill="x")

        # Enter calcula, Escape limpa
        self.raiz.bind("<Return>", lambda e: self.calcular())
        self.raiz.bind("<Escape>", lambda e: self._limpar())

    def _aplicar_mascara_data(self, *args):
        """Aplica automaticamente a máscara DD/MM/AAAA no campo de data."""
        texto = self.var_vencimento.get()
        digitos = "".join(c for c in texto if c.isdigit())[:8]

        formatado = ""
        for i, digito in enumerate(digitos):
            if i in (2, 4):
                formatado += "/"
            formatado += digito

        if formatado != texto:
            self.var_vencimento.set(formatado)
            entrada = getattr(self, "entrada_vencimento", None)
            if entrada is not None:
                entrada.icursor(len(formatado))
                entrada.xview(len(formatado))

    def calcular(self):
        texto_valor = self.var_valor.get().strip().replace(".", "").replace(",", ".")
        try:
            valor = float(texto_valor)
        except ValueError:
            messagebox.showwarning("Atenção", "Informe um valor válido (ex.: 1000,00 ou 1000.00).")
            return
        if valor <= 0:
            messagebox.showwarning("Atenção", "O valor deve ser maior que zero.")
            return

        texto_vencimento = self.var_vencimento.get().strip()
        try:
            data_vencimento = parse_data(texto_vencimento)
        except ValueError:
            messagebox.showwarning(
                "Atenção", "Informe a data de vencimento no formato DD/MM/AAAA.")
            return

        data_hoje = datetime.now().date()
        dias_atraso, juros, total = calcular_juros(valor, data_vencimento, data_hoje)

        linhas = [
            f"Data de hoje: {data_hoje.strftime('%d/%m/%Y')}",
            f"Data de vencimento: {data_vencimento.strftime('%d/%m/%Y')}",
            f"Dias em atraso: {dias_atraso}",
            f"Multa: {TAXA_MULTA_DIARIA:.1f}% ao dia",
            "",
            f"Valor original: {formatar_br(valor)}",
            f"Juros (multa): {formatar_br(juros)}",
            f"Total a pagar: {formatar_br(total)}",
        ]
        if dias_atraso == 0:
            linhas.append("")
            linhas.append("O título ainda não venceu — sem juros.")

        self.rotulo_resultado.config(text="\n".join(linhas))

    def _limpar(self):
        self.var_valor.set("")
        self.var_vencimento.set("")
        self.rotulo_resultado.config(
            text="Informe o valor e a data de vencimento e clique em Calcular Juros.")


def main():
    raiz = tk.Tk()
    AppJuros(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
