from playwright.sync_api import sync_playwright, Browser
import time
from typing import Optional
import base64
import os
import json

def normalize(palavra: str) -> str:
    palavra = palavra.lower().strip().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
    return palavra

def act(search: str, filtro_busca: Optional[str] = None) -> dict:
    with sync_playwright() as playwright:
        chromium = playwright.chromium
        browser = chromium.launch(headless=True)
        context = browser.new_context()
        try:
            page = context.new_page()
            page.goto("https://portaldatransparencia.gov.br/pessoa-fisica/busca/lista?pagina=1&tamanhoPagina=10")
            try:
                aceitar_btn = page.get_by_text("Aceitar todos", exact=True)
                aceitar_btn.wait_for(state="visible", timeout=15000)
                aceitar_btn.click()
            except:
                page.click('#accept-all-btn', force=True)
            page.locator('#termo').fill(search)
            
            if filtro_busca:
                page.locator('[aria-controls="box-busca-refinada"]').click()
                page.wait_for_selector('[id="btnConsultarPF"]')
                page.get_by_text(filtro_busca, exact=True).click()
                page.locator('[id="btnConsultarPF"]').click()
            
            else:
                page.get_by_label('Enviar dados do formulário de busca').click()
                page.wait_for_timeout(2000) # Espera 2 segundos para garantir que os resultados foram carregados

            page.wait_for_selector('#resultados', timeout=15000, state='attached')
            results = page.locator('[id="resultados"]').all()

            if len(results) == 0:
                raise ValueError('Nenhum resultado encontrado')
            
            if results[0].get_by_role("link").count() == 0:
                raise ValueError('Nenhum resultado encontrado')

            if len(results) > 0:
                results[0].get_by_role("link").first.click()

            
            
            try:
                aceitar_btn = page.get_by_text("Aceitar todos", exact=True)
                aceitar_btn.wait_for(state="visible", timeout=15000)
                if aceitar_btn.is_visible():
                    aceitar_btn.click()
            except:
                page.click('#accept-all-btn', force=True)

            page.wait_for_selector('[class="dados-tabelados"]', timeout=15000)
            dados = page.locator('[class="dados-tabelados"] > div.row').all()

            for dado in dados:
                linhas = dado.locator("span").all()
                for i, linha in enumerate(linhas):
                    if i == 0:
                        nome = linha.inner_text()
                        nome = normalize(nome).upper()
                    elif i == 1:
                        cpf = linha.inner_text()
                    elif i == 2:
                        localidade = linha.inner_text()
                        localidade = normalize(localidade).upper()
            
            dados = {
                "nome": nome,
                "cpf": cpf,
                "localidade": localidade,
                'beneficios': {}
            }

            page.wait_for_timeout(2000) # Espera 2 segundos para garantir que os dados foram carregados
            recursos = page.get_by_text("Recebimentos de recursos", exact=True)
            if recursos.is_visible():
                recursos.click()

                lista_recebimentos = page.locator('[class="form-group"] > [class="br-table"]').all()
                
                if len(lista_recebimentos) > 0:
                    for i, recebimento in enumerate(lista_recebimentos):
                        tipo_beneficio = recebimento.locator('strong').first.inner_text()
                        valor = page.locator('#tabela-visao-geral-sancoes > tbody > tr').nth(i).locator('td:nth-child(4)').inner_text()
                        tipo_beneficio = normalize(tipo_beneficio)
                        dados['beneficios'][tipo_beneficio] = valor
                
            page.screenshot(path="screenshot.jpg", full_page=True) # Tira um screenshot para verificar o estado da página
            
            with open('screenshot.jpg', 'rb') as f:
                binaries = f.read()
                encoded_image = base64.b64encode(binaries)
                encoded_image = encoded_image.decode('utf-8')
                dados['imagem_base64'] = encoded_image

            os.remove('screenshot.jpg') # Remove o arquivo de screenshot após a conversão para base64

            # async with aiofiles.open('user.json','w+') as f:
            #     await f.write(json.dumps(dados, indent=4))

            time.sleep(1) # Espera 1 segundo para ver o input preenchido
           
            return dados
        finally:
            context.close()
            browser.close()


# async def main():
#     async with async_playwright() as playwright:
#         browser = await run(playwright)
#         try:
#             await act(browser, "João da Silva")
#         finally:
#             await browser.close()

# asyncio.run(main())