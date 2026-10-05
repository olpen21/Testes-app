import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


# ---------------------------------------------------------------------------
# Funções de negócio (mesmas regras da versão de terminal)
# ---------------------------------------------------------------------------
def formatar_br(valor):
    """Formata um número como moeda brasileira (R$ 1.234,56)."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


CONFIG_PADRAO = {
    "limite_inferior": 100.0,    # abaixo disso não há comissão
    "limite_superior": 500.0,    # a partir daqui usa a comissão maior
    "percentual_inferior": 1.0,  # comissão (%) entre os limites
    "percentual_superior": 5.0,  # comissão (%) no limite superior ou acima
}


def percentual_comissao(valor, cfg=CONFIG_PADRAO):
    """Retorna a taxa de comissão (%) conforme as regras configuradas."""
    if valor < cfg["limite_inferior"]:
        return 0.0
    if valor < cfg["limite_superior"]:
        return cfg["percentual_inferior"]
    return cfg["percentual_superior"]


def calcular_comissao(valor, cfg=CONFIG_PADRAO):
    """Calcula o valor da comissão com base nas regras configuradas."""
    return valor * percentual_comissao(valor, cfg) / 100.0


def pasta_do_app():
    """Pasta onde o programa (ou .exe) está localizado."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def caminho_json_padrao():
    return os.path.join(pasta_do_app(), "vendas.json")


def caminho_config():
    return os.path.join(pasta_do_app(), "config.json")


def carregar_config():
    """Carrega as configurações de comissão do arquivo config.json."""
    cfg = dict(CONFIG_PADRAO)
    caminho = caminho_config()
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                salvo = json.load(arquivo)
            if isinstance(salvo, dict):
                for chave in cfg:
                    if chave in salvo:
                        cfg[chave] = float(salvo[chave])
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
    return cfg


def salvar_config(cfg):
    """Salva as configurações de comissão no arquivo config.json."""
    with open(caminho_config(), "w", encoding="utf-8") as arquivo:
        json.dump(cfg, arquivo, ensure_ascii=False, indent=4)


def ler_json(caminho):
    """Lê um arquivo JSON, aceitando um ou mais valores JSON concatenados."""
    with open(caminho, "r", encoding="utf-8") as arquivo:
        texto = arquivo.read().strip()

    dados = []
    decodificador = json.JSONDecoder()
    pos = 0
    while pos < len(texto):
        while pos < len(texto) and texto[pos] in " \t\n\r":
            pos += 1
        if pos >= len(texto):
            break
        valor, fim = decodificador.raw_decode(texto, pos)
        if isinstance(valor, list):
            dados.extend(valor)
        else:
            dados.append(valor)
        pos = fim
    return dados


def normalizar(item):
    """Converte um item do JSON em {'vendedor': str, 'valor': float}."""
    vendedor = None
    for chave in ("Vendedor", "vendedor", "nome", "Nome"):
        if chave in item:
            vendedor = item[chave]
            break

    valor = None
    for chave in ("Valor da venda", "valor da venda", "valor_da_venda", "valor", "Valor"):
        if chave in item:
            valor = item[chave]
            break

    try:
        valor = float(valor) if valor is not None else 0.0
    except (TypeError, ValueError):
        valor = 0.0

    return {"vendedor": str(vendedor).strip() if vendedor is not None else "", "valor": valor}


def agrupar(dados, cfg):
    """Agrupa por vendedor, somando vendas e comissões."""
    resumo = {}
    for d in dados:
        nome = d["vendedor"] or "—"
        item = resumo.setdefault(nome, {"vendas": 0.0, "comissao": 0.0})
        item["vendas"] += d["valor"]
        item["comissao"] += calcular_comissao(d["valor"], cfg)
    return resumo


# ---------------------------------------------------------------------------
# Janela de diálogo para adicionar/editar uma venda
# ---------------------------------------------------------------------------
class DialogoRegistro(tk.Toplevel):
    def __init__(self, master, titulo, vendedor="", valor=""):
        super().__init__(master)
        self.title(titulo)
        self.resizable(False, False)
        self.resultado = None
        self.transient(master)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Vendedor:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.ent_vendedor = ttk.Entry(frame, width=32)
        self.ent_vendedor.grid(row=0, column=1, padx=(8, 0), pady=(0, 6))
        self.ent_vendedor.insert(0, vendedor)

        ttk.Label(frame, text="Valor da venda (R$):").grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.ent_valor = ttk.Entry(frame, width=32)
        self.ent_valor.grid(row=1, column=1, padx=(8, 0), pady=(0, 6))
        self.ent_valor.insert(0, valor)

        botoes = ttk.Frame(frame)
        botoes.grid(row=2, column=0, columnspan=2, pady=(8, 0))
        ttk.Button(botoes, text="Salvar", command=self.confirmar).pack(side="left", padx=(0, 8))
        ttk.Button(botoes, text="Cancelar", command=self.destroy).pack(side="left")

        self.ent_vendedor.focus_set()
        self.bind("<Return>", lambda e: self.confirmar())
        self.bind("<Escape>", lambda e: self.destroy())

    def confirmar(self):
        vendedor = self.ent_vendedor.get().strip()
        valor_txt = self.ent_valor.get().strip().replace(",", ".")
        if not vendedor:
            messagebox.showwarning("Atenção", "Informe o nome do vendedor.", parent=self)
            return
        try:
            valor = float(valor_txt)
        except ValueError:
            messagebox.showwarning("Atenção", "Informe um valor numérico válido.", parent=self)
            return
        if valor < 0:
            messagebox.showwarning("Atenção", "O valor não pode ser negativo.", parent=self)
            return
        self.resultado = (vendedor, valor)
        self.destroy()


# ---------------------------------------------------------------------------
# Janela de diálogo para configurar as regras de comissão
# ---------------------------------------------------------------------------
class DialogoConfiguracoes(tk.Toplevel):
    def __init__(self, master, cfg):
        super().__init__(master)
        self.title("Configurações de comissão")
        self.resizable(False, False)
        self.resultado = None
        self.transient(master)
        self.grab_set()

        frame = ttk.Frame(self, padding=14)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Regras de comissão", font=("", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.campos = {}
        linhas = [
            ("limite_inferior", "Vendas abaixo de (R$) — sem comissão:"),
            ("limite_superior", "Vendas a partir de (R$) — comissão maior:"),
            ("percentual_inferior", "Comissão (%) entre os dois valores:"),
            ("percentual_superior", "Comissão (%) no valor maior ou acima:"),
        ]
        for i, (chave, texto) in enumerate(linhas, start=1):
            ttk.Label(frame, text=texto).grid(row=i, column=0, sticky="w", pady=3)
            ent = ttk.Entry(frame, width=14)
            ent.grid(row=i, column=1, sticky="e", padx=(12, 0), pady=3)
            ent.insert(0, f"{cfg[chave]:g}".replace(".", ","))
            self.campos[chave] = ent

        botoes = ttk.Frame(frame)
        botoes.grid(row=len(linhas) + 1, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(botoes, text="Salvar", command=self.confirmar).pack(side="left", padx=(0, 8))
        ttk.Button(botoes, text="Cancelar", command=self.destroy).pack(side="left")

        self.bind("<Return>", lambda e: self.confirmar())
        self.bind("<Escape>", lambda e: self.destroy())

    def confirmar(self):
        try:
            limite_inferior = float(self.campos["limite_inferior"].get().replace(",", "."))
            limite_superior = float(self.campos["limite_superior"].get().replace(",", "."))
            percentual_inferior = float(self.campos["percentual_inferior"].get().replace(",", "."))
            percentual_superior = float(self.campos["percentual_superior"].get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Atenção", "Preencha todos os campos com números válidos.", parent=self)
            return

        if limite_inferior < 0 or limite_superior <= limite_inferior:
            messagebox.showwarning(
                "Atenção",
                "O segundo valor deve ser maior que o primeiro, e ambos devem ser positivos.",
                parent=self,
            )
            return
        if percentual_inferior < 0 or percentual_superior < 0:
            messagebox.showwarning("Atenção", "As porcentagens não podem ser negativas.", parent=self)
            return

        self.resultado = {
            "limite_inferior": limite_inferior,
            "limite_superior": limite_superior,
            "percentual_inferior": percentual_inferior,
            "percentual_superior": percentual_superior,
        }
        self.destroy()


# ---------------------------------------------------------------------------
# Aplicação principal
# ---------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Comissões de Vendas")
        self.geometry("780x620")
        self.minsize(640, 460)

        self.arquivo_atual = caminho_json_padrao()
        self.dados = []
        self.cfg = carregar_config()
        self.total_var = tk.StringVar(value="")
        self.regra_var = tk.StringVar(value="")

        self._criar_widgets()
        self.carregar_arquivo(self.arquivo_atual)

    def _criar_widgets(self):
        # Barra de botões
        barra = ttk.Frame(self, padding=(8, 8, 8, 4))
        barra.pack(fill="x")

        ttk.Button(barra, text="Carregar", command=self.carregar_arquivo).pack(side="left", padx=(0, 4))
        ttk.Button(barra, text="Salvar", command=self.salvar_arquivo).pack(side="left", padx=(0, 4))
        ttk.Button(barra, text="Salvar como", command=self.salvar_como).pack(side="left", padx=(0, 12))
        ttk.Button(barra, text="Adicionar", command=self.adicionar_registro).pack(side="left", padx=(0, 4))
        ttk.Button(barra, text="Editar", command=self.editar_registro).pack(side="left", padx=(0, 4))
        ttk.Button(barra, text="Excluir", command=self.excluir_registro).pack(side="left", padx=(0, 12))
        ttk.Button(barra, text="Configurações", command=self.abrir_configuracoes).pack(side="left")

        ttk.Label(self, textvariable=self.regra_var, anchor="w", padding=(8, 0, 8, 4)).pack(fill="x")

        # Tabela de vendas
        quadro_vendas = ttk.LabelFrame(self, text=" Vendas ", padding=6)
        quadro_vendas.pack(fill="both", expand=True, padx=8, pady=(4, 4))

        colunas = ("vendedor", "valor", "taxa", "comissao")
        self.tree = ttk.Treeview(quadro_vendas, columns=colunas, show="headings", height=12)
        self.tree.heading("vendedor", text="Vendedor")
        self.tree.heading("valor", text="Valor da venda")
        self.tree.heading("taxa", text="Taxa")
        self.tree.heading("comissao", text="Comissão")
        self.tree.column("vendedor", width=220, anchor="w")
        self.tree.column("valor", width=140, anchor="e")
        self.tree.column("taxa", width=80, anchor="center")
        self.tree.column("comissao", width=140, anchor="e")

        scroll_vendas = ttk.Scrollbar(quadro_vendas, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_vendas.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll_vendas.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self.editar_registro())

        # Resumo por vendedor
        quadro_resumo = ttk.LabelFrame(self, text=" Resumo por vendedor ", padding=6)
        quadro_resumo.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        colunas_r = ("vendedor", "vendas", "comissao")
        self.tree_resumo = ttk.Treeview(quadro_resumo, columns=colunas_r, show="headings", height=6)
        self.tree_resumo.heading("vendedor", text="Vendedor")
        self.tree_resumo.heading("vendas", text="Total vendas")
        self.tree_resumo.heading("comissao", text="Comissão total")
        self.tree_resumo.column("vendedor", width=220, anchor="w")
        self.tree_resumo.column("vendas", width=150, anchor="e")
        self.tree_resumo.column("comissao", width=150, anchor="e")

        scroll_resumo = ttk.Scrollbar(quadro_resumo, orient="vertical", command=self.tree_resumo.yview)
        self.tree_resumo.configure(yscrollcommand=scroll_resumo.set)
        self.tree_resumo.pack(side="left", fill="both", expand=True)
        scroll_resumo.pack(side="right", fill="y")

        # Totais e barra de status
        ttk.Label(self, textvariable=self.total_var, anchor="w", padding=(8, 2)).pack(fill="x")
        self.status = ttk.Label(self, text="", anchor="w", padding=(8, 2))
        self.status.pack(fill="x")

    # -- arquivo ------------------------------------------------------------
    def carregar_arquivo(self, caminho=None):
        if caminho is None:
            caminho = filedialog.askopenfilename(
                title="Abrir JSON",
                filetypes=[("Arquivo JSON", "*.json"), ("Todos os arquivos", "*.*")],
                initialdir=pasta_do_app(),
            )
            if not caminho:
                return

        try:
            itens = ler_json(caminho)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{e}")
            return

        self.dados = [normalizar(item) for item in itens if isinstance(item, dict)]
        self.arquivo_atual = caminho
        self.atualizar_tabela()
        self.atualizar_resumo()
        self.status.config(text=f"Arquivo: {caminho}")

    def salvar_arquivo(self):
        if not self.arquivo_atual:
            self.salvar_como()
            return
        try:
            conteudo = [{"vendedor": d["vendedor"], "valor": d["valor"]} for d in self.dados]
            with open(self.arquivo_atual, "w", encoding="utf-8") as arquivo:
                json.dump(conteudo, arquivo, ensure_ascii=False, indent=4)
            self.status.config(text=f"Salvo em: {self.arquivo_atual}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar:\n{e}")

    def salvar_como(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar como",
            defaultextension=".json",
            filetypes=[("Arquivo JSON", "*.json")],
            initialdir=pasta_do_app(),
        )
        if not caminho:
            return
        self.arquivo_atual = caminho
        self.salvar_arquivo()

    # -- visualização -------------------------------------------------------
    def atualizar_tabela(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, d in enumerate(self.dados):
            valor = d["valor"]
            taxa = percentual_comissao(valor, self.cfg)
            comissao = calcular_comissao(valor, self.cfg)
            self.tree.insert(
                "", "end", iid=str(i),
                values=(d["vendedor"], formatar_br(valor), f"{taxa:.0f}%", formatar_br(comissao)),
            )

    def atualizar_resumo(self):
        for item in self.tree_resumo.get_children():
            self.tree_resumo.delete(item)
        resumo = agrupar(self.dados, self.cfg)
        itens = sorted(resumo.items(), key=lambda kv: kv[1]["comissao"], reverse=True)
        for nome, v in itens:
            self.tree_resumo.insert(
                "", "end",
                values=(nome, formatar_br(v["vendas"]), formatar_br(v["comissao"])),
            )
        total_vendas = sum(v["vendas"] for v in resumo.values())
        total_comissao = sum(v["comissao"] for v in resumo.values())
        self.total_var.set(
            f"Total de vendas: {formatar_br(total_vendas)}     "
            f"Comissão total: {formatar_br(total_comissao)}"
        )
        self.regra_var.set(self.texto_regras())

    # -- operações ----------------------------------------------------------
    def adicionar_registro(self):
        dialogo = DialogoRegistro(self, "Adicionar venda")
        self.wait_window(dialogo)
        if dialogo.resultado:
            vendedor, valor = dialogo.resultado
            self.dados.append({"vendedor": vendedor, "valor": valor})
            self.atualizar_tabela()
            self.atualizar_resumo()

    def editar_registro(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione uma venda para editar.")
            return
        idx = int(sel[0])
        d = self.dados[idx]
        valor_preenchido = f"{d['valor']:.2f}".replace(".", ",")
        dialogo = DialogoRegistro(self, "Editar venda", d["vendedor"], valor_preenchido)
        self.wait_window(dialogo)
        if dialogo.resultado:
            vendedor, valor = dialogo.resultado
            self.dados[idx] = {"vendedor": vendedor, "valor": valor}
            self.atualizar_tabela()
            self.atualizar_resumo()

    def excluir_registro(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione uma ou mais vendas para excluir.")
            return
        indices = sorted((int(i) for i in sel), reverse=True)
        if messagebox.askyesno("Confirmar", f"Excluir {len(indices)} registro(s)?"):
            for i in indices:
                self.dados.pop(i)
            self.atualizar_tabela()
            self.atualizar_resumo()
    # -- configurações ------------------------------------------------------
    def texto_regras(self):
        cfg = self.cfg
        li = cfg["limite_inferior"]
        ls = cfg["limite_superior"]
        pi = cfg["percentual_inferior"]
        ps = cfg["percentual_superior"]
        return (f"Regras: abaixo de {formatar_br(li)} = 0%   |   "
                f"de {formatar_br(li)} a {formatar_br(ls - 0.01)} = {pi:g}%   |   "
                f"a partir de {formatar_br(ls)} = {ps:g}%")

    def abrir_configuracoes(self):
        dialogo = DialogoConfiguracoes(self, self.cfg)
        self.wait_window(dialogo)
        if dialogo.resultado:
            self.cfg = dialogo.resultado
            salvar_config(self.cfg)
            self.atualizar_tabela()
            self.atualizar_resumo()
            self.status.config(text=f"Configurações atualizadas. Arquivo: {self.arquivo_atual}")



def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
