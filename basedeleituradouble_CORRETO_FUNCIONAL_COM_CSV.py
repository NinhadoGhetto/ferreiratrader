
import asyncio
import csv
import os
from playwright.async_api import async_playwright

ARQUIVO_CSV = "registro_pedras.csv"
ultima_pedra = None

def salvar_pedra(horario, numero, cor):
    nova_linha = {"horario": horario, "numero": numero, "cor": cor}
    existe = os.path.exists(ARQUIVO_CSV)
    with open(ARQUIVO_CSV, "a", newline='') as csvfile:
        fieldnames = ["horario", "numero", "cor"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not existe:
            writer.writeheader()
        writer.writerow(nova_linha)
        print(f"✅ Pedra salva no CSV: {nova_linha}")

async def extrair_pedra():
    global ultima_pedra
    print("🔵 Monitorando nova pedra...")

    async with async_playwright() as p:
        navegador = await p.chromium.launch(headless=False)
        pagina = await navegador.new_page()
        await pagina.goto("https://www.tipminer.com/br/historico/blaze/double?timezone=America%2FBahia")

        while True:
            try:
                await pagina.wait_for_selector(".cell__circle", timeout=10000)
                cores = await pagina.query_selector_all(".cell__circle")
                numeros = await pagina.query_selector_all(".cell__result")
                horarios = await pagina.query_selector_all(".cell__date")

                if len(cores) > 0 and len(numeros) > 0 and len(horarios) > 0:
                    numero_elemento = numeros[0]
                    horario_elemento = horarios[0]

                    numero = await numero_elemento.inner_text()
                    horario = await horario_elemento.inner_text()
                    cor_formatada = "B" if numero == "0" else "V" if int(numero) <= 7 else "P"

                    pedra_atual = f"{horario}_{numero}_{cor_formatada}"

                    if pedra_atual != ultima_pedra:
                        ultima_pedra = pedra_atual
                        print(f"🔴 [{horario}] Número: {numero} | Cor: {cor_formatada}")
                        salvar_pedra(horario, numero, cor_formatada)
                    else:
                        print(f"⏳ Já registrada: {horario}")
                else:
                    print("⚠️ Elementos incompletos.")
            except Exception as e:
                print(f"❌ Erro ao capturar pedra: {e}")
            await asyncio.sleep(1)

asyncio.run(extrair_pedra())
