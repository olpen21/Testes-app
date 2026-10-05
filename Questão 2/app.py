import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# ---------------------------------------------------------------------------
# Funções de negócio
# ---------------------------------------------------------------------------

def pasta_do_app():
    """Pasta onde o programa (ou .exe) está localizado."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def caminho_estoque():
    return os.path.join(pasta_do_app(), "estoque.json")


def caminho_movimentacoes():
    return os.path.join(pasta_do_app(), "movimentacoes.json")


def carregar_estoque():
    """Carrega a lista de produtos do arquivo estoque.json.

    Aceita tanto {"estoque": [...]} quanto uma lista direta de produtos.
    """
    caminho = caminho_estoque()
    if not os.path.exists(caminho):
        return []

    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    if isinstance(dados, dict):
        return dados.get("estoque", [])
    if isinstance(dados, list):
        return dados
    return []


def salvar_estoque(produtos):
    """Grava a lista de produtos de volta no estoque.json."""
    with open(caminho_estoque(), "w", encoding="utf-8") as arquivo:
        json.dump({"estoque": produtos}, arquivo, ensure_ascii=False, indent=4)


def carregar_movimentacoes():
    """Carrega o histórico de movimentações do arquivo movimentacoes.json."""
    caminho = caminho_movimentacoes()
    if not os.path.exists(caminho):
        return []

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return []

    return dados if isinstance(dados, list) else []


def salvar_movimentacoes(movimentacoes):
    """Grava o histórico de movimentações no movimentacoes.json."""
    with open(caminho_movimentacoes(), "w", encoding="utf-8") as arquivo:
        json.dump(movimentacoes, arquivo, ensure_ascii=False, indent=4)


def proximo_id(movimentacoes):
    """Retorna o próximo número identificador único de movimentação."""
    if not movimentacoes:
        return 1
    maior = 0
    for mov in movimentacoes:
        try:
            maior = max(maior, int(mov.get("id", 0)))
        except (TypeError, ValueError):
            continue
    return maior + 1


# ---------------------------------------------------------------------------
# Aplicação gráfica
# ---------------------------------------------------------------------------

class AppEstoque:
    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Movimentação de Estoque - Depósito")
        self.raiz.geometry("860x640")
        self.raiz.minsize(760, 560)

        self.produtos = carregar_estoque()
        self.movimentacoes = carregar_movimentacoes()

        self.var_tipo = tk.StringVar(value="Entrada")
        self.var_produto = tk.StringVar(value="")

        self._montar_interface()
        self._atualizar_tabela_produtos()
        self._atualizar_tabela_movimentacoes()

    # ------------------------------------------------------------------
    # Montagem da interface
    # ------------------------------------------------------------------
    def _montar_interface(self):
        # --- Lista de produtos ---
        quadro_produtos = ttk.LabelFrame(self.raiz, text="Produtos em estoque", padding=8)
        quadro_produtos.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        colunas = ("codigo", "descricao", "estoque")
        self.tabela_produtos = ttk.Treeview(quadro_produtos, columns=colunas, show="headings", height=6)
        self.tabela_produtos.heading("codigo", text="Código")
        self.tabela_produtos.heading("descricao", text="Produto")
        self.tabela_produtos.heading("estoque", text="Estoque atual")
        self.tabela_produtos.column("codigo", width=90, anchor="center")
        self.tabela_produtos.column("descricao", width=380, anchor="w")
        self.tabela_produtos.column("estoque", width=130, anchor="e")
        self.tabela_produtos.pack(fill="both", expand=True)

        barra_produtos = ttk.Frame(quadro_produtos)
        barra_produtos.pack(fill="x", pady=(6, 0))
        ttk.Button(barra_produtos, text="Adicionar Produto",
                   command=self._abrir_janela_adicionar_produto).pack(side="left")
        ttk.Button(barra_produtos, text="Excluir Produto",
                   command=self._excluir_produto_selecionado).pack(side="left", padx=6)

        # --- Formulário de movimentação ---
        quadro_form = ttk.LabelFrame(self.raiz, text="Lançar movimentação", padding=8)
        quadro_form.pack(fill="x", padx=10, pady=5)

        linha1 = ttk.Frame(quadro_form)
        linha1.pack(fill="x", pady=2)

        ttk.Label(linha1, text="Produto:").pack(side="left")
        opcoes = [f"{p.get('codigoProduto')} - {p.get('descricaoProduto')}" for p in self.produtos]
        self.combo_produto = ttk.Combobox(linha1, textvariable=self.var_produto, values=opcoes, state="readonly", width=42)
        self.combo_produto.pack(side="left", padx=6)
        if opcoes:
            self.combo_produto.current(0)

        ttk.Label(linha1, text="Tipo:").pack(side="left", padx=(16, 0))
        ttk.Radiobutton(linha1, text="Entrada", variable=self.var_tipo, value="Entrada",
                        command=self._definir_descricao_padrao).pack(side="left", padx=4)
        ttk.Radiobutton(linha1, text="Saída", variable=self.var_tipo, value="Saída",
                        command=self._definir_descricao_padrao).pack(side="left", padx=4)

        linha2 = ttk.Frame(quadro_form)
        linha2.pack(fill="x", pady=2)

        ttk.Label(linha2, text="Quantidade:").pack(side="left")
        self.entrada_quantidade = ttk.Spinbox(linha2, from_=1, to=1000000, width=10)
        self.entrada_quantidade.set(1)
        self.entrada_quantidade.pack(side="left", padx=6)

        ttk.Label(linha2, text="Descrição:").pack(side="left", padx=(16, 0))
        self.var_descricao = tk.StringVar()
        self.entrada_descricao = ttk.Entry(linha2, textvariable=self.var_descricao, width=52)
        self.entrada_descricao.pack(side="left", padx=6)
        self._definir_descricao_padrao()

        linha3 = ttk.Frame(quadro_form)
        linha3.pack(fill="x", pady=(6, 0))

        self.botao_lancar = ttk.Button(linha3, text="Lançar Movimentação", command=self.lancar_movimentacao)
        self.botao_lancar.pack(side="left")

        self.rotulo_status = ttk.Label(linha3, text="", foreground="#0a6e0a")
        self.rotulo_status.pack(side="left", padx=12)

        # --- Histórico de movimentações ---
        quadro_movs = ttk.LabelFrame(self.raiz, text="Movimentações realizadas", padding=8)
        quadro_movs.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        colunas_mov = ("id", "codigo", "produto", "tipo", "descricao", "quantidade", "estoque_final", "datahora")
        self.tabela_movs = ttk.Treeview(quadro_movs, columns=colunas_mov, show="headings", height=8)
        self.tabela_movs.heading("id", text="ID")
        self.tabela_movs.heading("codigo", text="Código")
        self.tabela_movs.heading("produto", text="Produto")
        self.tabela_movs.heading("tipo", text="Tipo")
        self.tabela_movs.heading("descricao", text="Descrição")
        self.tabela_movs.heading("quantidade", text="Qtd.")
        self.tabela_movs.heading("estoque_final", text="Estoque final")
        self.tabela_movs.heading("datahora", text="Data/Hora")
        self.tabela_movs.column("id", width=50, anchor="center")
        self.tabela_movs.column("codigo", width=70, anchor="center")
        self.tabela_movs.column("produto", width=180, anchor="w")
        self.tabela_movs.column("tipo", width=80, anchor="center")
        self.tabela_movs.column("descricao", width=170, anchor="w")
        self.tabela_movs.column("quantidade", width=60, anchor="center")
        self.tabela_movs.column("estoque_final", width=100, anchor="e")
        self.tabela_movs.column("datahora", width=140, anchor="center")
        self.tabela_movs.pack(fill="both", expand=True)

        barra = ttk.Scrollbar(quadro_movs, orient="vertical", command=self.tabela_movs.yview)
        self.tabela_movs.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")

    # ------------------------------------------------------------------
    # Atualização das tabelas
    # ------------------------------------------------------------------
    def _atualizar_tabela_produtos(self):
        for item in self.tabela_produtos.get_children():
            self.tabela_produtos.delete(item)
        for p in self.produtos:
            self.tabela_produtos.insert("", "end", values=(
                p.get("codigoProduto"),
                p.get("descricaoProduto"),
                p.get("estoque"),
            ))

    def _atualizar_combo_produto(self):
        """Atualiza as opções do seletor de produto após inclusão/exclusão."""
        opcoes = [f"{p.get('codigoProduto')} - {p.get('descricaoProduto')}" for p in self.produtos]
        self.combo_produto["values"] = opcoes
        if opcoes:
            self.combo_produto.current(0)
        else:
            self.var_produto.set("")

    def _proximo_codigo_produto(self):
        """Sugere o próximo código livre para um novo produto."""
        if not self.produtos:
            return 1
        maior = 0
        for p in self.produtos:
            try:
                maior = max(maior, int(p.get("codigoProduto", 0)))
            except (TypeError, ValueError):
                continue
        return maior + 1

    def _atualizar_tabela_movimentacoes(self):
        for item in self.tabela_movs.get_children():
            self.tabela_movs.delete(item)
        for mov in self.movimentacoes:
            self.tabela_movs.insert("", "end", values=(
                mov.get("id"),
                mov.get("codigoProduto"),
                mov.get("produto"),
                mov.get("tipo"),
                mov.get("descricao"),
                mov.get("quantidade"),
                mov.get("estoque_final"),
                mov.get("data_hora"),
            ))

    def _definir_descricao_padrao(self):
        """Preenche a descrição com um texto que identifica o tipo da movimentação."""
        tipo = self.var_tipo.get()
        self.var_descricao.set(f"{tipo} de mercadoria")

    # ------------------------------------------------------------------
    # Cadastro de produtos
    # ------------------------------------------------------------------
    def _abrir_janela_adicionar_produto(self):
        """Abre uma janela para cadastrar um novo produto no estoque."""
        janela = tk.Toplevel(self.raiz)
        janela.title("Adicionar Produto")
        janela.resizable(False, False)
        janela.grab_set()

        frame = ttk.Frame(janela, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Código:").grid(row=0, column=0, sticky="w", pady=4)
        var_codigo = tk.StringVar(value=str(self._proximo_codigo_produto()))
        ttk.Entry(frame, textvariable=var_codigo, width=15).grid(row=0, column=1, sticky="w", pady=4, padx=6)

        ttk.Label(frame, text="Descrição:").grid(row=1, column=0, sticky="w", pady=4)
        var_descricao = tk.StringVar()
        ttk.Entry(frame, textvariable=var_descricao, width=40).grid(row=1, column=1, sticky="w", pady=4, padx=6)

        ttk.Label(frame, text="Estoque inicial:").grid(row=2, column=0, sticky="w", pady=4)
        var_estoque = tk.StringVar(value="0")
        ttk.Spinbox(frame, from_=0, to=1000000, textvariable=var_estoque, width=13).grid(
            row=2, column=1, sticky="w", pady=4, padx=6)

        rotulo_erro = ttk.Label(frame, text="", foreground="#c0392b")
        rotulo_erro.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        def confirmar():
            erro = self._adicionar_produto(
                var_codigo.get().strip(),
                var_descricao.get().strip(),
                var_estoque.get().strip(),
            )
            if erro:
                rotulo_erro.config(text=erro)
                return
            janela.destroy()

        botoes = ttk.Frame(frame)
        botoes.grid(row=4, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(botoes, text="Cancelar", command=janela.destroy).pack(side="right")
        ttk.Button(botoes, text="Adicionar", command=confirmar).pack(side="right", padx=6)

        janela.wait_window()

    def _excluir_produto_selecionado(self):
        """Exclui o produto selecionado na lista de estoque."""
        selecionado = self.tabela_produtos.selection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um produto na lista para excluir.")
            return

        valores = self.tabela_produtos.item(selecionado[0], "values")
        try:
            codigo = int(valores[0])
        except (TypeError, ValueError):
            return
        produto = next((p for p in self.produtos if p.get("codigoProduto") == codigo), None)
        if produto is None:
            return

        confirmado = messagebox.askyesno(
            "Excluir produto",
            f"Deseja realmente excluir o produto '{produto.get('descricaoProduto')}' ({codigo}) do estoque?\n\n"
            f"O histórico de movimentações será mantido."
        )
        if not confirmado:
            return

        self.produtos.remove(produto)
        salvar_estoque(self.produtos)
        self._atualizar_tabela_produtos()
        self._atualizar_combo_produto()
        self.rotulo_status.config(text=f"Produto '{produto.get('descricaoProduto')}' excluído do estoque.")

    def _adicionar_produto(self, codigo_txt, descricao, estoque_txt):
        """Valida e cadastra um novo produto.

        Retorna uma mensagem de erro ou None em caso de sucesso.
        """
        codigo_txt = (codigo_txt or "").strip()
        descricao = (descricao or "").strip()
        estoque_txt = (estoque_txt or "").strip()

        try:
            codigo = int(codigo_txt)
        except ValueError:
            return "Código deve ser um número inteiro."
        if not descricao:
            return "Informe a descrição do produto."
        if any(p.get("codigoProduto") == codigo for p in self.produtos):
            return "Já existe um produto com este código."
        try:
            estoque_inicial = int(estoque_txt)
        except ValueError:
            return "Estoque inicial deve ser um número inteiro."
        if estoque_inicial < 0:
            return "Estoque inicial não pode ser negativo."

        novo = {
            "codigoProduto": codigo,
            "descricaoProduto": descricao,
            "estoque": estoque_inicial,
        }
        self.produtos.append(novo)
        salvar_estoque(self.produtos)
        self._atualizar_tabela_produtos()
        self._atualizar_combo_produto()
        self.var_produto.set(f"{codigo} - {descricao}")
        self.rotulo_status.config(text=f"Produto '{descricao}' adicionado com sucesso.")
        return None

    # ------------------------------------------------------------------
    # Lançamento da movimentação
    # ------------------------------------------------------------------
    def lancar_movimentacao(self):
        # Produto selecionado
        selecao = self.var_produto.get().strip()
        if not selecao:
            messagebox.showwarning("Atenção", "Selecione um produto.")
            return
        try:
            codigo = int(selecao.split("-")[0].strip())
        except ValueError:
            messagebox.showerror("Erro", "Produto selecionado inválido.")
            return

        produto = next((p for p in self.produtos if p.get("codigoProduto") == codigo), None)
        if produto is None:
            messagebox.showerror("Erro", "Produto não encontrado no estoque.")
            return

        # Quantidade
        try:
            quantidade = int(self.entrada_quantidade.get())
        except ValueError:
            messagebox.showwarning("Atenção", "Informe uma quantidade válida (número inteiro).")
            return
        if quantidade <= 0:
            messagebox.showwarning("Atenção", "A quantidade deve ser maior que zero.")
            return

        tipo = self.var_tipo.get()
        estoque_atual = int(produto.get("estoque", 0))

        # Saída não pode deixar o estoque negativo
        if tipo == "Saída":
            if quantidade > estoque_atual:
                messagebox.showerror(
                    "Estoque insuficiente",
                    f"Não é possível retirar {quantidade} unidade(s).\n"
                    f"Estoque atual de {produto.get('descricaoProduto')}: {estoque_atual}."
                )
                return
            estoque_final = estoque_atual - quantidade
        else:
            estoque_final = estoque_atual + quantidade

        descricao = self.var_descricao.get().strip()
        if not descricao:
            descricao = f"{tipo} de mercadoria"

        # Número identificador único
        identificador = proximo_id(self.movimentacoes)

        movimentacao = {
            "id": identificador,
            "codigoProduto": codigo,
            "produto": produto.get("descricaoProduto"),
            "tipo": tipo,
            "descricao": descricao,
            "quantidade": quantidade,
            "estoque_final": estoque_final,
            "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }

        # Aplica a movimentação no estoque
        produto["estoque"] = estoque_final
        self.movimentacoes.append(movimentacao)

        # Persiste os dados
        salvar_estoque(self.produtos)
        salvar_movimentacoes(self.movimentacoes)

        # Atualiza a interface
        self._atualizar_tabela_produtos()
        self._atualizar_tabela_movimentacoes()
        self.rotulo_status.config(text=f"Movimentação #{identificador} registrada com sucesso.")

        # Retorna a quantidade final do produto movimentado
        messagebox.showinfo(
            "Movimentação registrada",
            f"Movimentação #{identificador} - {descricao}\n\n"
            f"Produto: {produto.get('descricaoProduto')} ({codigo})\n"
            f"Tipo: {tipo} de {quantidade} unidade(s)\n\n"
            f"Estoque final: {estoque_final} unidade(s)."
        )


def main():
    raiz = tk.Tk()
    AppEstoque(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
