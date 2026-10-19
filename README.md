# Onde estão nossas doenças?

Painel estático com mapas de doenças e indicadores do município do Rio de Janeiro.
Os dados, o Leaflet e o Bootstrap estão incluídos no projeto. Os mapas de ruas e
satélite e a fonte do Google Fonts são carregados pela internet.

## Instalar e usar no Windows

Use um navegador atualizado (Edge, Chrome ou Firefox).

1. Instale uma versão estável do [Python 3 para Windows](https://www.python.org/downloads/windows/)
   compatível com o seu Windows (o iniciador requer Python 3.10 ou superior).
   Se o instalador oferecer **Add python.exe to PATH**, marque essa opção.
2. Copie a pasta inteira do projeto para a máquina, por exemplo
   `C:\Cavalarica`. Se recebeu um ZIP, extraia todos os arquivos primeiro.
   Mantenha as pastas `assets`, `css`, `data`, `img`, `js` e `leaflet` junto dos HTMLs.
3. Dê dois cliques em **INICIAR_WINDOWS.bat**. O navegador padrão abrirá o painel
   por HTTP, normalmente em `http://127.0.0.1:8000/index.html`.
4. Mantenha a janela do iniciador aberta durante o uso. Para encerrar o servidor,
   pressione **Ctrl+C** nessa janela ou feche-a.

Não é preciso instalar pacotes com pip, Node.js, R ou um banco de dados.
Para facilitar o uso diário, crie um atalho para `INICIAR_WINDOWS.bat` na área de trabalho.
Abra o painel pelo iniciador; abrir os HTMLs diretamente por `file://` impede a
identificação da página nas requisições ao OpenStreetMap.

O servidor atende somente à própria máquina (`127.0.0.1`). Se a porta 8000 já
estiver ocupada, ele escolhe uma porta livre e abre o endereço correspondente.
Se o navegador não abrir automaticamente, copie o endereço exibido na janela.

## Mapas de fundo

A configuração está centralizada em `js/mapas-base.js` e é usada pelos 14 mapas.

- **Ruas:** OpenStreetMap, com URL HTTPS canônica e créditos visíveis.
- **Imagem de satélite:** camada Esri World Imagery já utilizada pelo painel.
- **Sem mapa de fundo:** permite consultar os dados locais sem carregar imagens externas.

Se uma imagem do mapa falhar, o painel passa para o fundo simples e mostra um
aviso, preservando as camadas de dados. Para tentar novamente, selecione **Ruas**
ou **Imagem de satélite** no controle de camadas, no canto superior esquerdo.
Se abrir um HTML diretamente como arquivo, apenas o fundo simples fica disponível
e aparece uma orientação para usar o iniciador.

A antiga opção **Aquarela** foi retirada: o endpoint Stamen/Fastly encerrou o
serviço em 2023. Para reintroduzi-la, será necessário configurar o serviço atual
e sua autenticação conforme o [guia de migração da Stadia Maps](https://docs.stadiamaps.com/guides/migrating-from-stamen-map-tiles/).

## Se o mapa não carregar

1. Confirme que abriu o painel pelo iniciador e que o endereço começa com `http://127.0.0.1:`.
2. Verifique a conexão. A rede precisa permitir HTTPS para `tile.openstreetmap.org`
   e `server.arcgisonline.com`.
3. Confira se extensões, antivírus ou configurações de privacidade estão removendo
   o cabeçalho `Referer`. Nas ferramentas do navegador (F12 → Rede), ele deve
   aparecer nas requisições das imagens do mapa. As páginas e o servidor usam
   `strict-origin-when-cross-origin`.
4. Mantenha o cache do navegador habilitado, inclusive durante a inspeção em F12.
5. Se o erro 403 persistir, registre a mensagem recebida e os cabeçalhos da
   requisição para identificar o bloqueio. Corrigir a configuração não garante
   a remoção de um bloqueio anterior por domínio ou rede.

O OpenStreetMap oferece os tiles públicos sem garantia de disponibilidade.
Respeite a [política de uso](https://operations.osmfoundation.org/policies/tiles/):
não faça downloads em massa nem pré-carregamento para uso offline. A opção de
fundo simples usa os dados locais do painel, sem baixar uma cópia dos mapas externos.

## Execução pelo terminal

No Windows:

```bat
py -3 servidor_local.py
```

No Linux/macOS:

```bash
python3 servidor_local.py
```

Para escolher uma porta preferida e abrir o navegador manualmente:

```bash
python3 servidor_local.py --port 8080 --no-browser
```

O servidor sempre usa a pasta onde `servidor_local.py` está salvo, mesmo quando
iniciado a partir de outra pasta. Para publicar o painel na internet, hospede os
arquivos estáticos em um servidor HTTPS; o iniciador foi feito para uso local.

## Verificação para desenvolvimento

O teste do servidor utiliza somente a biblioteca padrão:

```bash
python3 -m unittest discover -s tests -v
```

O teste de navegador usa Playwright, opcional e desnecessário para operar o painel:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
python3 tests/verificar_mapas.py
```

Ele verifica os 14 mapas, créditos, Referer, troca de fundos, uma resposta HTTP
403 contendo uma imagem válida, recuperação e abertura por arquivo. As respostas
externas são simuladas; esse teste não baixa tiles dos provedores. Para usar um
Chrome/Chromium já instalado, passe `--browser-executable` com o caminho do executável.
