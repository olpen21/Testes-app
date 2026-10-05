import json
import os

CAMINHO_PADRAO = "vendas.json"


def ler_json(caminho_arquivo):
    """Lê um arquivo JSON e retorna uma lista de registros.

    Aceita tanto um único array/objeto quanto vários valores JSON
    concatenados no mesmo arquivo (ex.: dois arrays separados).
    """
    with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
        texto = arquivo.read().strip()

    dados = []
    decodificador = json.JSONDecoder()
    pos = 0
    while pos < len(texto):
        # Pula espaços, quebras de linha, etc.
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


def extrair_registro(item):
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

    return vendedor, valor


def formatar_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def percentual_comissao(valor):
    if valor < 100:
        return 0.0
    if valor < 500:
        return 1.0
    return 5.0


def calcular_comissao(valor):
    if valor < 100:
        return 0.0
    if valor < 500:
        return valor * 0.01
    return valor * 0.05


def exibir_tabela(registros):
    if not registros:
        print("Nenhum registro encontrado no JSON.")
        return

    largura = max([len("Vendedor")] + [len(str(r[0] or "—")) for r in registros])

    cabecalho = (f"{'Vendedor'.ljust(largura)}  {'Valor da venda':>15}  "
                 f"{'Taxa':>5}  {'Comissão':>12}")
    print(cabecalho)
    print("=" * len(cabecalho))

    total = 0.0
    total_comissao = 0.0
    for vendedor, valor in registros:
        vendedor = vendedor if vendedor is not None else "—"
        try:
            valor = float(valor) if valor is not None else 0.0
        except (TypeError, ValueError):
            valor = 0.0
        taxa = percentual_comissao(valor)
        comissao = calcular_comissao(valor)
        total += valor
        total_comissao += comissao
        print(f"{str(vendedor).ljust(largura)}  {formatar_br(valor):>15}  "
              f"{taxa:>4.0f}%  {formatar_br(comissao):>12}")

    print("=" * len(cabecalho))
    print(f"{'Total'.ljust(largura)}  {formatar_br(total):>15}  "
          f"{'':>5}  {formatar_br(total_comissao):>12}")


def agrupar_por_vendedor(registros):
    """Agrupa os registros por vendedor, somando vendas e comissões."""
    resumo = {}
    for vendedor, valor in registros:
        try:
            valor = float(valor) if valor is not None else 0.0
        except (TypeError, ValueError):
            valor = 0.0
        nome = str(vendedor) if vendedor is not None else "—"
        item = resumo.setdefault(nome, {"vendas": 0.0, "comissao": 0.0})
        item["vendas"] += valor
        item["comissao"] += calcular_comissao(valor)
    return resumo


def exibir_resumo_por_vendedor(registros):
    """Exibe um resumo agrupado por vendedor, ordenado por comissão (decrescente)."""
    resumo = agrupar_por_vendedor(registros)
    if not resumo:
        return

    # Ordena do maior para o menor total de comissão
    itens = sorted(resumo.items(), key=lambda kv: kv[1]["comissao"], reverse=True)

    largura = max([len("Vendedor")] + [len(nome) for nome, _ in itens])

    print()
    print("Resumo por vendedor")
    cabecalho = (f"{'Vendedor'.ljust(largura)}  {'Total vendas':>15}  "
                 f"{'Comissão total':>15}")
    print(cabecalho)
    print("=" * len(cabecalho))

    for nome, valores in itens:
        print(f"{nome.ljust(largura)}  {formatar_br(valores['vendas']):>15}  "
              f"{formatar_br(valores['comissao']):>15}")

    print("=" * len(cabecalho))
    total_vendas = sum(v["vendas"] for v in resumo.values())
    total_comissao = sum(v["comissao"] for v in resumo.values())
    print(f"{'Total'.ljust(largura)}  {formatar_br(total_vendas):>15}  "
          f"{formatar_br(total_comissao):>15}")


def main():
    caminho = input(f"Digite o caminho do arquivo JSON (Enter para '{CAMINHO_PADRAO}'): ").strip()
    if not caminho:
        caminho = CAMINHO_PADRAO

    if not os.path.exists(caminho):
        print(f"Erro: arquivo não encontrado: {caminho}")
        return

    try:
        dados = ler_json(caminho)
    except json.JSONDecodeError as e:
        print(f"Erro ao ler o JSON: {e}")
        return

    registros = [extrair_registro(item) for item in dados if isinstance(item, dict)]
    exibir_tabela(registros)
    exibir_resumo_por_vendedor(registros)


if __name__ == "__main__":
    main()
